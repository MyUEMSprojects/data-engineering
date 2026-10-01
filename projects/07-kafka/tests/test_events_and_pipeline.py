"""Testes sem infraestrutura: contrato do evento e a ORDEM das operações do consumidor (com fakes)."""

import json
from decimal import Decimal

import pytest
from confluent_kafka import KafkaError, KafkaException

from kpipe.events import (
    InvalidEvent,
    OrderEvent,
    expected_state,
    generate_events,
    parse_event,
)
from kpipe.pipeline import Pipeline
from kpipe.sink import Record, WriteStats


# ---------------------------------------------------------------- eventos
def _ev(**kw):
    base = {
        "schema_version": 1,
        "order_id": "O1",
        "seq": 1,
        "customer_id": "C1",
        "status": "paid",
        "amount": "10.50",
        "event_ts": "2024-01-01T10:00:00+00:00",
    }
    return json.dumps({**base, **kw}).encode()


def test_roundtrip():
    e = next(generate_events(5))
    assert parse_event(e.to_bytes()) == e
    assert e.event_id == f"{e.order_id}-{e.seq}"


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (None, "empty_payload"),
        (b"", "empty_payload"),
        (b'{"order_id": "x"', "invalid_json"),
        (b"[1]", "invalid_json"),
        (_ev(schema_version=2), "unsupported_schema_version:2"),
        (_ev(amount=None), "missing_field:amount"),
        (_ev(seq=0), "bad_seq"),
        (_ev(seq=True), "bad_seq"),
        (_ev(seq="1"), "bad_seq"),
        (_ev(status="teleported"), "unknown_status"),
        (_ev(amount="abc"), "bad_amount"),
        (_ev(amount="-1"), "bad_amount"),
        (_ev(amount="NaN"), "bad_amount"),
        (_ev(event_ts="ontem"), "bad_timestamp"),
    ],
)
def test_invalid_events_have_explicit_reasons(payload, reason):
    with pytest.raises(InvalidEvent) as ei:
        parse_event(payload)
    assert str(ei.value) == reason


def test_naive_timestamp_is_assumed_utc_and_amount_is_decimal():
    e = parse_event(_ev(event_ts="2024-01-01T10:00:00", amount="7"))
    assert e.event_ts.utcoffset().total_seconds() == 0 and e.amount == Decimal("7.00")


def test_generator_is_deterministic_time_ordered_and_per_order_sequenced():
    a = list(generate_events(200, seed=1))
    assert a == list(generate_events(200, seed=1)) and a != list(generate_events(200, seed=2))
    assert [e.event_ts for e in a] == sorted(e.event_ts for e in a)
    last: dict[str, int] = {}
    for e in a:  # dentro de cada pedido, seq cresce de 1 em 1, na ordem de chegada
        assert e.seq == last.get(e.order_id, 0) + 1
        last[e.order_id] = e.seq


def test_expected_state_is_last_event_per_order():
    evs = list(generate_events(100))
    st = expected_state(evs)
    assert len(st) == 100
    for e in evs:
        assert st[e.order_id][1] >= e.seq


# ---------------------------------------------------------------- pipeline (fakes)
class Msg:
    def __init__(self, value, partition=0, offset=0, key=b"k", error=None):
        self._v, self._p, self._o, self._k, self._e = value, partition, offset, key, error

    def error(self):
        return self._e

    def topic(self):
        return "t"

    def partition(self):
        return self._p

    def offset(self):
        return self._o

    def key(self):
        return self._k

    def value(self):
        return self._v


class FakeConsumer:
    def __init__(self, batches, calls):
        self.batches, self.calls, self.commits = list(batches), calls, []

    def consume(self, n, timeout):
        return self.batches.pop(0) if self.batches else []

    def commit(self, offsets, asynchronous):
        self.calls.append("commit")
        assert asynchronous is False  # commit SÍNCRONO: só segue depois de confirmado
        self.commits.append({(o.topic, o.partition): o.offset for o in offsets})


class FakeProducer:
    def __init__(self, calls):
        self.calls, self.sent = calls, []

    def produce(self, topic, key, value, headers):
        self.sent.append((topic, key, value, dict(headers)))

    def flush(self, t):
        self.calls.append("dlq.flush")

    def poll(self, t): ...


class RecordingSink:
    def __init__(self, calls, fail=False):
        self.calls, self.fail, self.records = calls, fail, []

    def write(self, records):
        self.calls.append("sink.write")
        if self.fail:
            raise RuntimeError("banco fora do ar")
        self.records += records
        return WriteStats(inserted=len(records))


def _pipeline(batches, *, fail=False, before_commit=None):
    calls: list[str] = []
    c, p, s = FakeConsumer(batches, calls), FakeProducer(calls), RecordingSink(calls, fail)
    return (
        Pipeline(c, s, p, "t.dlq", batch_size=10, poll_timeout=0.0, before_commit=before_commit),
        c,
        p,
        s,
        calls,
    )


def test_order_of_operations_dlq_flush_then_sink_then_commit():
    pipe, c, p, s, calls = _pipeline([[Msg(_ev(), 0, 5), Msg(b"lixo", 1, 9)]])
    pipe.run(max_idle_s=0.0)
    assert calls == ["dlq.flush", "sink.write", "commit"]  # commit SEMPRE por último
    assert c.commits == [{("t", 0): 6, ("t", 1): 10}]  # offset commitado = último + 1, por partição
    assert len(s.records) == 1 and len(p.sent) == 1


def test_poison_goes_to_dlq_with_reason_and_source_and_does_not_block_the_batch():
    pipe, c, p, s, _ = _pipeline([[Msg(b"{", 2, 7, key=b"K"), Msg(_ev(), 2, 8)]])
    pipe.run(max_idle_s=0.0)
    topic, key, value, headers = p.sent[0]
    assert (topic, key, value) == ("t.dlq", b"K", b"{")
    assert headers["error"] == b"invalid_json" and headers["source"] == b"t:2:7"
    assert len(s.records) == 1 and pipe.stats["dlq"] == 1


def test_sink_failure_means_no_commit_so_the_batch_will_be_redelivered():
    pipe, c, _, _, calls = _pipeline([[Msg(_ev(), 0, 0)]], fail=True)
    with pytest.raises(RuntimeError):
        pipe.run(max_idle_s=0.0)
    assert "commit" not in calls and c.commits == []


def test_crash_hook_between_write_and_commit_leaves_offsets_uncommitted():
    def boom(batch_no):
        raise SystemExit("crash")

    pipe, c, _, s, calls = _pipeline([[Msg(_ev(), 0, 0)]], before_commit=boom)
    with pytest.raises(SystemExit):
        pipe.run(max_idle_s=0.0)
    assert calls == ["dlq.flush", "sink.write"] and c.commits == [] and len(s.records) == 1


def test_partition_eof_is_ignored_but_other_errors_raise():
    eof = Msg(None, error=KafkaError(KafkaError._PARTITION_EOF))
    pipe, c, *_ = _pipeline([[eof, Msg(_ev(), 0, 3)]])
    pipe.run(max_idle_s=0.0)
    assert c.commits == [{("t", 0): 4}]
    bad = Msg(None, error=KafkaError(KafkaError._ALL_BROKERS_DOWN))
    pipe2, *_ = _pipeline([[bad]])
    with pytest.raises(KafkaException):
        pipe2.run(max_idle_s=0.0)


def test_run_stops_when_idle_and_on_stop_flag():
    pipe, *_ = _pipeline([])
    assert dict(pipe.run(max_idle_s=0.0)) == {}  # nada a fazer ⇒ encerra por ociosidade
    pipe2, *_ = _pipeline([[Msg(_ev(), 0, 0)], [Msg(_ev(order_id="O2"), 0, 1)]])
    pipe2.run(max_idle_s=5.0, stop=lambda: pipe2.batches >= 1)
    assert pipe2.batches == 1


def test_record_type_carries_kafka_coordinates():
    e = parse_event(_ev())
    r = Record(e, 3, 42)
    assert (r.partition, r.offset) == (3, 42) and isinstance(r.event, OrderEvent)
