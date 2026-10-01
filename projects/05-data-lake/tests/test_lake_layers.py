from datetime import date
from decimal import Decimal

import pyarrow as pa

from lake.bronze import ingest
from lake.compaction import compact_silver
from lake.gold import build_gold
from lake.inventory import inventory
from lake.reader import pruning_report, read_silver
from lake.silver import build_silver
from lake.synth import generate_batch

from .conftest import batch, event, put


# ---------------------------------------------------------------- storage / bronze
def test_local_write_is_atomic_no_tmp_left(lake):
    lake.write("a/b/c.txt", b"x")
    assert lake.read("a/b/c.txt") == b"x"
    assert [f.path for f in lake.list_files()] == ["a/b/c.txt"]


def test_bronze_is_idempotent_and_immutable(lake):
    data = batch(event("O1"))
    r1 = ingest(lake, data, date(2024, 1, 1))
    r2 = ingest(lake, data, date(2024, 1, 1))
    assert r1.created and not r2.created and r1.path == r2.path
    r3 = ingest(lake, batch(event("O2")), date(2024, 1, 1))  # outro conteúdo ⇒ outro arquivo
    assert r3.path != r1.path
    assert len(lake.list_files("bronze")) == 2
    assert lake.read(r1.path) == data  # bytes exatos, intocados


# ---------------------------------------------------------------- silver
def test_silver_conserves_every_line(lake):
    put(lake, "2024-01-02", event("O1"), event("O2", amount=-5), raw=["lixo{", ""])
    r = build_silver(lake)
    assert r.lines_read == r.valid + r.rejected == 3
    assert r.reject_reasons == {"negative_amount": 1, "invalid_json": 1}
    q = lake.list_files("quarantine")
    assert len(q) == 1
    rows = lake.read_parquet(q[0].path).to_pylist()
    assert {x["reason"] for x in rows} == {"negative_amount", "invalid_json"}
    assert all(x["raw"] and x["source_file"].startswith("bronze/") for x in rows)


def test_silver_keeps_latest_event_and_ignores_stale_late_arrival(lake):
    put(lake, "2024-01-01", event("O1", status="created", updated_at="2024-01-01T08:00:00+00:00"))
    put(lake, "2024-01-02", event("O1", status="shipped", updated_at="2024-01-02T08:00:00+00:00"))
    # chega DEPOIS, mas é um evento MAIS ANTIGO: não pode sobrescrever o shipped
    put(lake, "2024-01-03", event("O1", status="paid", updated_at="2024-01-01T12:00:00+00:00"))
    r = build_silver(lake)
    assert r.orders == 1 and r.duplicates_removed == 2
    t = read_silver(lake)
    assert t.column("status").to_pylist() == ["shipped"]


def test_silver_partitions_by_business_date_and_late_data_touches_only_its_partition(lake):
    put(lake, "2024-01-01", event("A", order_date="2024-01-01"))
    put(lake, "2024-01-02", event("B", order_date="2024-01-02"))
    first = build_silver(lake)
    assert (first.partitions_written, first.partitions_unchanged) == (2, 0)
    # dado atrasado: chega no dia 3 um evento de um pedido do dia 1
    put(
        lake,
        "2024-01-03",
        event(
            "A", order_date="2024-01-01", status="delivered", updated_at="2024-01-03T09:00:00+00:00"
        ),
    )
    second = build_silver(lake)
    assert (second.partitions_written, second.partitions_unchanged) == (1, 1)
    dirs = {f.path.split("/")[2] for f in lake.list_files("silver")}
    assert dirs == {"order_date=2024-01-01", "order_date=2024-01-02"}


def test_silver_is_idempotent_and_reproducible_from_bronze(lake):
    for d in range(1, 4):
        ingest(lake, generate_batch(date(2024, 1, d), n_new=60), date(2024, 1, d))
    build_silver(lake)
    snapshot = {f.path for f in lake.list_files("silver")}
    again = build_silver(lake)
    assert again.partitions_written == 0
    assert {f.path for f in lake.list_files("silver")} == snapshot
    # "reprocessar do zero": apagar silver inteira e reconstruir dá EXATAMENTE os mesmos arquivos
    for f in lake.list_files("silver"):
        lake.delete(f.path)
    build_silver(lake)
    assert {f.path for f in lake.list_files("silver")} == snapshot


def test_changing_file_layout_never_duplicates_rows(lake):
    """Regressão: layout novo reaproveitava o nome '-000' e deixava o arquivo antigo (linhas em dobro)."""
    put(lake, "2024-01-01", *[event(f"O{i}") for i in range(10)])
    build_silver(lake)
    build_silver(lake, rows_per_file=3)
    assert read_silver(lake).num_rows == 10
    build_silver(lake)
    assert read_silver(lake).num_rows == 10
    assert len(lake.list_files("silver")) == 1


# ---------------------------------------------------------------- reader / compaction / inventory
def _lake_with_days(lake, days=4):
    for d in range(1, days + 1):
        ingest(lake, generate_batch(date(2024, 1, d), n_new=80), date(2024, 1, d))
    return build_silver(lake)


def test_partition_pruning_skips_files(lake):
    _lake_with_days(lake, 4)
    all_ = pruning_report(lake, None, None)
    one = pruning_report(lake, date(2024, 1, 3), date(2024, 1, 3))
    assert all_.files_scanned == all_.files_total == 4
    assert one.files_scanned == 1 and one.files_skipped == 3
    assert one.rows_returned == read_silver(lake, date(2024, 1, 3), date(2024, 1, 3)).num_rows


def test_compaction_reduces_files_and_preserves_data(lake):
    _lake_with_days(lake, 3)
    before = read_silver(lake).sort_by([("order_id", "ascending")])
    build_silver(lake, rows_per_file=20)
    many = len(lake.list_files("silver"))
    rep = compact_silver(lake)
    after = read_silver(lake).sort_by([("order_id", "ascending")])
    assert many > rep.files_after == 3 and rep.files_before == many
    assert after.equals(before)


def test_inventory_uses_metadata_only(lake):
    r = _lake_with_days(lake, 2)
    inv = {(t.layer, t.table): t for t in inventory(lake)}
    assert inv[("silver", "orders")].rows == r.orders
    assert inv[("silver", "orders")].partitions == 2
    assert inv[("bronze", "orders")].rows is None  # JSONL: sem rodapé


# ---------------------------------------------------------------- gold
def test_gold_reconciles_with_silver_and_excludes_canceled(lake):
    put(
        lake,
        "2024-01-01",
        event("O1", amount=100, status="paid"),
        event("O2", amount=50, status="canceled"),
        event("O3", amount=25, status="delivered", country="PT"),
    )
    build_silver(lake)
    res = {g.table: g for g in build_gold(lake)}
    assert set(res) == {"daily_revenue", "customer_value", "status_funnel"}
    daily = lake.read_parquet(
        next(f.path for f in lake.list_files("gold/daily_revenue"))
    ).to_pylist()
    assert sum(r["revenue"] for r in daily) == Decimal("125.00")  # 100 + 25, sem o cancelado
    assert sum(r["orders"] for r in daily) == 2
    funnel = lake.read_parquet(next(f.path for f in lake.list_files("gold/status_funnel")))
    assert sum(funnel.column("orders").to_pylist()) == 3  # o funil conta TODOS os status


def test_gold_is_idempotent(lake):
    _lake_with_days(lake, 2)
    assert all(g.written for g in build_gold(lake))
    assert not any(g.written for g in build_gold(lake))


def test_gold_revenue_equals_silver_total(lake):
    _lake_with_days(lake, 3)
    build_gold(lake)
    silver = read_silver(lake)
    expected = sum(
        a
        for a, s in zip(
            silver.column("amount").to_pylist(), silver.column("status").to_pylist(), strict=True
        )
        if s != "canceled"
    )
    daily = lake.read_parquet(next(f.path for f in lake.list_files("gold/daily_revenue")))
    assert sum(daily.column("revenue").to_pylist()) == expected
    assert isinstance(daily.schema.field("revenue").type, pa.DataType)
