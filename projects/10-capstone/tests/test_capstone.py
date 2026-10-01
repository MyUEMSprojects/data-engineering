import json
from datetime import date
from decimal import Decimal

import pytest

from capstone import cli, quality, steps
from capstone import lakehouse as lh
from capstone.synth import generate_extract

D1, D2 = date(2024, 3, 1), date(2024, 3, 2)


def line(**kw):
    base = {
        "order_id": "O1",
        "customer_id": "C1",
        "country": "BR",
        "category": "books",
        "amount": "10.5",
        "status": "paid",
        "order_date": "2024-03-01",
        "updated_at": "2024-03-01T10:00:00+00:00",
    }
    return json.dumps({**base, **kw})


# ---------------------------------------------------------------- parse / gate (puros)
@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ('{"a": 1', "invalid_json"),
        ("[1]", "invalid_json"),
        (line(order_id=None), "missing_field:order_id"),
        (line(amount="abc"), "bad_amount"),
        (line(amount="-1"), "bad_amount"),
        (line(amount="NaN"), "bad_amount"),
        (line(order_date="2024-13-45"), "bad_date"),
        (line(status="x"), "unknown_status"),
    ],
)
def test_parse_line_rejects_with_reason(raw, reason):
    assert quality.parse_line(raw) == (None, reason)


def test_parse_line_normalizes():
    rec, _ = quality.parse_line(line(amount="10.5", updated_at="2024-03-01T10:00:00Z"))
    assert rec["amount"] == Decimal("10.50") and rec["updated_at"].tzinfo is not None


def _rows(*lines):
    return [{"raw": x, "_source_file": "f", "_line_no": i} for i, x in enumerate(lines, 1)]


def test_gate_blocks_on_reject_rate_and_empty_batch_and_stale_data():
    ok = [line(order_id=f"O{i}") for i in range(20)]
    assert not quality.run_gate(D1, _rows(*ok), []).blocked
    assert quality.run_gate(D1, _rows(*ok, "lixo", "lixo", "lixo"), []).blocked  # 13% > 5%
    assert quality.run_gate(D1, [], []).blocked
    stale = [line(order_id="O1", updated_at="2024-02-20T00:00:00+00:00")]
    g = quality.run_gate(D1, _rows(*stale), [])
    assert g.blocked and any(c.name == "freshness" and not c.passed for c in g.checks)


def test_soft_checks_warn_but_do_not_block_and_anomaly_needs_history():
    g = quality.run_gate(D1, _rows(*[line(order_id="O1")] * 5), [])  # 100% duplicado, sem histórico
    assert not g.blocked and [c.name for c in g.warnings] == ["duplicate_rate"]
    vol = next(c for c in g.checks if c.name == "volume_anomaly")
    assert vol.skipped  # sem histórico: PULA, não "aprova"
    g2 = quality.run_gate(D1, _rows(*[line(order_id=f"O{i}") for i in range(500)]), [100, 101, 99, 100, 102])
    assert "volume_anomaly" in [c.name for c in g2.warnings]


def test_robust_z_resists_outliers_and_constant_series():
    assert quality.robust_z([100, 101, 99, 100, 1_000_000], 100) == pytest.approx(0, abs=0.7)
    assert quality.robust_z([5, 5, 5, 5], 5) == 0.0 and quality.robust_z([5, 5, 5, 5], 9) is None
    assert quality.robust_z([1, 2], 3) is None


def test_synth_is_deterministic_and_scenarios_differ():
    assert generate_extract(D1, "clean") == generate_extract(D1, "clean")
    assert generate_extract(D1, "clean") != generate_extract(D1, "dirty")

    def bad(sc):
        return sum(quality.parse_line(x)[0] is None for x in generate_extract(D1, sc).decode().split("\n") if x)

    assert bad("clean") == 0 < bad("dirty") < bad("heavy_dirty")


# ---------------------------------------------------------------- passos com Delta real
def test_ingest_is_idempotent_and_raw_is_immutable(lake):
    a = steps.ingest(D1)
    b = steps.ingest(D1)
    assert a["raw_created"] and not b["raw_created"]
    assert lh.read(*lh.T_BRONZE).num_rows == a["rows"]  # reexecução NÃO duplica a partição
    steps.ingest(D2)
    assert lh.read(*lh.T_BRONZE).num_rows == a["rows"] + steps.ingest(D2)["rows"]


def test_silver_refuses_to_run_without_an_approved_gate(lake):
    steps.ingest(D1, "heavy_dirty")
    assert steps.gate(D1).blocked
    with pytest.raises(steps.GateNotPassed):
        steps.silver(D1)
    with pytest.raises(steps.GateNotPassed):
        steps.silver(D2)  # nem gate existe


def test_pipeline_end_to_end_and_idempotent_merge(lake):
    for d in (D1, D2):
        assert cli.run_day(d, "dirty", quiet=True) == 0
    n = lh.read(*lh.T_SILVER).num_rows
    v = lh.open_table(*lh.T_SILVER).version()
    cli.run_day(D2, "dirty", quiet=True)  # reexecução
    assert lh.read(*lh.T_SILVER).num_rows == n
    assert lh.read(*lh.T_QUAR).num_rows > 0 and set(lh.read(*lh.T_QUAR).column("ds").to_pylist()) == {"2024-03-01", "2024-03-02"}
    exp = cli.expected_silver([(D1, "dirty"), (D2, "dirty")])
    got = {r["order_id"]: (r["status"], str(r["amount"])) for r in lh.read(*lh.T_SILVER).to_pylist()}
    assert got == exp
    assert lh.open_table(*lh.T_SILVER).version() >= v


def test_merge_never_regresses_to_an_older_event(lake):
    def batch(status, ts):
        import pyarrow as pa

        rec, _ = quality.parse_line(line(status=status, updated_at=ts))
        rec.update(_ingest_ds="x", _source_file="f")
        return pa.Table.from_pylist([rec], schema=lh.SILVER_SCHEMA)

    lh.merge_silver(batch("created", "2024-03-01T08:00:00+00:00"))
    lh.merge_silver(batch("shipped", "2024-03-01T12:00:00+00:00"))
    m = lh.merge_silver(batch("paid", "2024-03-01T09:00:00+00:00"))  # evento ANTIGO chegando tarde
    assert m["num_target_rows_updated"] == 0
    assert lh.read(*lh.T_SILVER).column("status").to_pylist() == ["shipped"]


def test_time_travel_and_restore(lake):
    cli.run_day(D1, quiet=True)
    cli.run_day(D2, quiet=True)
    dt = lh.open_table(*lh.T_SILVER)
    rows = [lh.read(*lh.T_SILVER, version=v).num_rows for v in range(dt.version() + 1)]
    assert rows == sorted(rows) and rows[0] < rows[-1]
    dt.restore(0)
    assert lh.read(*lh.T_SILVER).num_rows == rows[0]


def test_schema_enforcement_rejects_wrong_schema(lake):
    import pyarrow as pa
    from deltalake import write_deltalake

    cli.run_day(D1, quiet=True)
    with pytest.raises(Exception):  # noqa: B017, PT011
        write_deltalake(lh.path(*lh.T_SILVER), pa.table({"order_id": [1], "surprise": ["x"]}), mode="append")


def test_gold_reconciles_with_silver_and_excludes_canceled(lake):
    cli.run_day(D1, quiet=True)
    silver = lh.read(*lh.T_SILVER).to_pylist()
    exp = sum(r["amount"] for r in silver if r["status"] != "canceled")
    gold = lh.read("gold", "daily_revenue")
    assert sum(gold.column("revenue").to_pylist()) == exp
    assert sum(lh.read("gold", "order_status_funnel").column("orders").to_pylist()) == len(silver)


def test_metrics_are_valid_prometheus_text_and_flag_a_blocked_gate(lake):
    cli.run_day(D1, quiet=True)
    assert cli.run_day(D2, "heavy_dirty", quiet=True) == 2
    text = (lake / "_ops" / "metrics" / "capstone.prom").read_text()
    assert "capstone_gate_blocked 1.0" in text and "capstone_run_success 0.0" in text
    for ln in text.strip().split("\n"):
        assert ln.startswith("#") or len(ln.rsplit(" ", 1)) == 2 and float(ln.rsplit(" ", 1)[1]) is not None
    assert text.count("# TYPE capstone_batch_rows") == 1  # HELP/TYPE uma vez por métrica
    run = json.loads((lake / "_ops" / "runs" / "2024-03-02.json").read_text())
    assert run["status"] == "blocked"


def test_blocked_day_leaves_silver_and_gold_untouched(lake):
    cli.run_day(D1, quiet=True)
    n, v = lh.read(*lh.T_SILVER).num_rows, lh.open_table(*lh.T_SILVER).version()
    cli.run_day(D2, "heavy_dirty", quiet=True)
    assert lh.read(*lh.T_SILVER).num_rows == n and lh.open_table(*lh.T_SILVER).version() == v
    # a bronze GUARDA o dia bloqueado (para diagnóstico/reprocessamento) — só não é promovido
    assert lh.read(*lh.T_BRONZE).num_rows > n
