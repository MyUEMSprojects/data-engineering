"""Testes de integração: Kafka + PostgreSQL reais (docker compose up -d).

    KAFKA_BOOTSTRAP=localhost:9092 PG_DSN=postgresql://de:de@localhost:5432/sink pytest -m integration

Sem as variáveis (ou sem os serviços no ar) são PULADOS. Cada teste usa tópicos e grupos próprios.
"""

import os
import uuid
from decimal import Decimal

import psycopg
import pytest

from kpipe import admin as adm
from kpipe.cli import check_state
from kpipe.consumer import make_consumer
from kpipe.events import generate_events, parse_event
from kpipe.pipeline import Pipeline
from kpipe.producer import make_producer, produce_events
from kpipe.sink import PostgresSink, Record

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP")
PG_DSN = os.environ.get("PG_DSN")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not (BOOTSTRAP and PG_DSN), reason="defina KAFKA_BOOTSTRAP e PG_DSN"),
]


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setattr("kpipe.cli.PG_DSN", PG_DSN)
    topic = f"it.{uuid.uuid4().hex[:8]}"
    adm.ensure_topics(BOOTSTRAP, {topic: 4, f"{topic}.dlq": 1})
    with psycopg.connect(PG_DSN) as c:
        c.execute("truncate order_events, orders_current")
    yield topic, f"g-{uuid.uuid4().hex[:6]}"
    adm.delete_topics(BOOTSTRAP, [topic, f"{topic}.dlq"])


def _consume_all(topic, group, *, before_commit=None):
    c = make_consumer(BOOTSTRAP, group, topic)
    sink = PostgresSink(PG_DSN)
    pipe = Pipeline(
        c,
        sink,
        make_producer(BOOTSTRAP),
        f"{topic}.dlq",
        batch_size=100,
        poll_timeout=0.5,
        before_commit=before_commit,
    )
    try:
        pipe.run(max_idle_s=4)
    finally:
        c.close()
        sink.close()
    return pipe


def test_end_to_end_with_poison_messages(env):
    topic, group = env
    s = produce_events(BOOTSTRAP, topic, generate_events(150), poison=5)
    assert s.failed == 0
    pipe = _consume_all(topic, group)
    r = check_state(150, 42)
    assert r["events_in_sink"] == r["expected_events"] and r["wrong_state"] == 0
    assert r["duplicate_event_ids"] == 0 and pipe.stats["dlq"] == 5
    dlq = adm.read_all(BOOTSTRAP, f"{topic}.dlq")
    assert len(dlq) == 5
    assert all(dict(m.headers())["error"] for m in dlq)
    assert sum(x.lag for x in adm.lag(BOOTSTRAP, group, topic)) == 0


def test_crash_between_write_and_commit_causes_redelivery_without_duplicates(env):
    topic, group = env
    produce_events(BOOTSTRAP, topic, generate_events(150))

    class Crash(Exception): ...

    def boom(batch_no):
        if batch_no == 1:
            raise Crash

    with pytest.raises(Crash):
        _consume_all(topic, group, before_commit=boom)  # gravou o lote 1 e MORREU antes do commit
    mid = check_state(150, 42)
    assert 0 < mid["events_in_sink"] < mid["expected_events"]  # ficou pela metade

    pipe = _consume_all(topic, group)  # "reinício": mesmo grupo ⇒ retoma do último commit (nenhum!)
    r = check_state(150, 42)
    assert r["events_in_sink"] == r["expected_events"] and r["duplicate_event_ids"] == 0
    assert r["wrong_state"] == 0
    assert pipe.stats["duplicates_ignored"] > 0  # o lote do crash foi REENTREGUE e absorvido
    assert sum(x.lag for x in adm.lag(BOOTSTRAP, group, topic)) == 0


def test_same_key_goes_to_same_partition_preserving_order(env):
    topic, group = env
    produce_events(BOOTSTRAP, topic, generate_events(80))
    _consume_all(topic, group)
    with psycopg.connect(PG_DSN) as c, c.cursor() as cur:
        cur.execute(
            "select order_id, count(distinct kafka_partition) from order_events group by 1 having count(distinct kafka_partition) > 1"
        )
        assert cur.fetchall() == []  # todo evento de um pedido veio da MESMA partição
        cur.execute("""select count(*) from (select order_id, seq, kafka_offset,
                      lag(kafka_offset) over (partition by order_id order by seq) prev
                      from order_events) t where prev is not null and kafka_offset < prev""")
        assert cur.fetchone()[0] == 0  # e na ordem do seq


# ---------------------------------------------------------------- sink (só PostgreSQL)
@pytest.fixture
def sink():
    with psycopg.connect(PG_DSN) as c:
        c.execute("truncate order_events, orders_current")
    s = PostgresSink(PG_DSN)
    yield s
    s.close()


def _records(n=3):
    return [Record(e, 0, i) for i, e in enumerate(generate_events(n))]


def test_sink_is_idempotent(sink):
    recs = _records(20)
    first = sink.write(recs)
    second = sink.write(recs)  # reentrega do MESMO lote
    assert first.inserted == len(recs) and second.inserted == 0
    assert second.duplicates == len(recs) and second.state_updates == 0
    with psycopg.connect(PG_DSN) as c:
        assert c.execute("select count(*) from order_events").fetchone()[0] == len(recs)


def test_state_only_advances_even_when_an_old_event_arrives_late(sink):
    evs = [e for e in generate_events(1) if e.order_id == "O0000000"]
    assert len(evs) >= 2
    sink.write([Record(evs[-1], 0, 10)])  # chega primeiro o MAIS NOVO
    st = sink.write([Record(evs[0], 0, 11)])  # depois o mais antigo (fora de ordem)
    assert st.inserted == 1 and st.stale_ignored == 1 and st.state_updates == 0
    with psycopg.connect(PG_DSN) as c:
        status, seq = c.execute("select status, seq from orders_current").fetchone()
    assert (status, seq) == (evs[-1].status, evs[-1].seq)


def test_sink_transaction_is_all_or_nothing(sink):
    good = _records(3)
    bad_event = parse_event(
        b'{"schema_version":1,"order_id":"OX","seq":1,"customer_id":"C","status":"paid","amount":"1","event_ts":"2024-01-01T00:00:00+00:00"}'
    )
    object.__setattr__(bad_event, "amount", Decimal("-5"))  # viola o CHECK (amount >= 0) do banco
    with pytest.raises(psycopg.errors.CheckViolation):
        sink.write([*good, Record(bad_event, 0, 99)])
    with psycopg.connect(PG_DSN) as c:
        assert c.execute("select count(*) from order_events").fetchone()[0] == 0  # nada ficou
        assert c.execute("select count(*) from orders_current").fetchone()[0] == 0
