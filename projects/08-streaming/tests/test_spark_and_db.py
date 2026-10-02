"""Spark (parse) e PostgreSQL (sink). Rodam no contêiner: ./run.sh pytest (ver README)."""

import pytest

from streamlab import db
from streamlab.events import build_scenario, parse_click

pyspark = pytest.importorskip("pyspark")


def test_spark_parse_agrees_with_the_python_reference_for_every_scenario_message(spark):
    """PARIDADE: a regra de validade do Spark == a do gabarito, mensagem a mensagem."""
    from streamlab.job import parse, rejected, valid_events

    msgs = [m for p in build_scenario() for m in p.messages]
    raw = spark.createDataFrame(
        [(i % 3, i, m.decode()) for i, m in enumerate(msgs)], "partition int, offset long, v string"
    )
    raw = raw.selectExpr("partition", "offset", "cast(v as binary) as value")
    parsed = parse(raw)
    ok_ids = {r.event_id for r in valid_events(parsed).collect()}
    py_ok = {c.event_id for m in msgs if (c := parse_click(m))}
    assert ok_ids == py_ok
    assert rejected(parsed).count() == sum(1 for m in msgs if parse_click(m) is None) == 3
    reasons = {r.reason for r in rejected(parsed).collect()}
    assert reasons == {"invalid_json", "missing_or_bad_field"}


# ---------------------------------------------------------------- sink
def _row(b=1):
    from datetime import datetime, timezone

    return [(datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc), "home", 3, 2, b)]


def test_apply_batch_is_applied_once(pg):
    assert db.apply_batch(pg, "windows", 0, db.UPSERT_WINDOW, _row()) is True
    assert db.apply_batch(pg, "windows", 0, db.UPSERT_WINDOW, _row()) is False  # reexecução do MESMO lote
    assert db.count(pg, "batch_log") == 1 and db.count(pg, "page_views_1m") == 1


def test_upsert_overwrites_with_absolute_values_so_replays_are_harmless(pg):
    db.apply_batch(pg, "windows", 0, db.UPSERT_WINDOW, _row())
    from datetime import datetime, timezone

    newer = [(datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc), "home", 5, 3, 1)]
    db.apply_batch(pg, "windows", 1, db.UPSERT_WINDOW, newer)  # update mode: o valor ABSOLUTO substitui
    ((views, users),) = db.fetch_windows(pg).values()
    assert (views, users) == (5, 3)


def test_ledger_and_data_are_atomic(pg):
    bad = [(None, "home", 1, 1, 1)]  # viola NOT NULL em window_start
    with pytest.raises(Exception):  # noqa: B017, PT011 — qualquer violação do banco
        db.apply_batch(pg, "windows", 7, db.UPSERT_WINDOW, bad)
    assert db.count(pg, "batch_log") == 0  # o livro-razão NÃO ficou marcado: o lote poderá ser refeito
    assert db.apply_batch(pg, "windows", 7, db.UPSERT_WINDOW, _row()) is True


def test_different_queries_have_independent_ledgers(pg):
    assert db.apply_batch(pg, "windows", 0, db.UPSERT_WINDOW, _row()) is True
    assert db.apply_batch(pg, "rejects", 0, db.INSERT_REJECT, [(0, 1, "invalid_json", "x")]) is True
    assert db.apply_batch(pg, "rejects", 0, db.INSERT_REJECT, [(0, 2, "invalid_json", "y")]) is False


@pytest.mark.integration
def test_end_to_end_demo_matches_the_reference():
    """Kafka + Spark + PostgreSQL reais: 3 fases e verificação contra o gabarito (30–60 s)."""
    import os

    if not os.environ.get("KAFKA_BOOTSTRAP"):
        pytest.skip("defina KAFKA_BOOTSTRAP e PG_DSN")
    from streamlab.cli import cmd_demo

    with pytest.raises(SystemExit) as e:
        cmd_demo(None)
    assert e.value.code == 0
