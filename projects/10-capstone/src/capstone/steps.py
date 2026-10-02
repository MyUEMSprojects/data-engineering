"""Os passos do pipeline. Cada um é IDEMPOTENTE por data lógica (`ds`) e pode ser reexecutado à vontade."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict
from datetime import date

import duckdb
import pyarrow as pa

from . import config, quality
from . import lakehouse as lh
from .synth import generate_extract


class GateNotPassed(RuntimeError):
    """Silver recusa rodar sem um gate aprovado para o `ds` (contrato entre passos)."""


def _report_path(kind: str, ds: str):
    return config.ops(kind, f"{ds}.json")


# ------------------------------------------------------------------ 1. ingestão (raw imutável → bronze)
def ingest(ds: date, scenario: str = "clean") -> dict:
    data = generate_extract(ds, scenario, seed=config.SEED)
    digest = hashlib.sha256(data).hexdigest()[:12]
    raw = config.LAKE / "raw" / "orders" / f"ds={ds}" / f"extract-{digest}.jsonl"
    created = not raw.exists()
    if created:  # a landing zone é IMUTÁVEL: um arquivo nunca é sobrescrito
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(data)
    src = f"raw/orders/ds={ds}/{raw.name}"
    lines = [ln for ln in data.decode().split("\n") if ln.strip()]
    now = lh.now_utc()
    tbl = pa.table(
        {
            "raw": lines,
            "_ingest_ds": [ds.isoformat()] * len(lines),
            "_source_file": [src] * len(lines),
            "_line_no": list(range(1, len(lines) + 1)),
            "_ingested_at": [now] * len(lines),
        },
        schema=lh.BRONZE_SCHEMA,
    )
    lh.overwrite_partition(lh.T_BRONZE, tbl, ds.isoformat(), "_ingest_ds")
    return {"rows": len(lines), "raw_file": src, "raw_created": created}


def _bronze_rows(ds: date) -> list[dict]:
    t = lh.open_table(*lh.T_BRONZE).to_pyarrow_table(filters=[("_ingest_ds", "=", ds.isoformat())])
    return t.to_pylist()


# ------------------------------------------------------------------ 2. qualidade (gate)
def gate(ds: date) -> quality.GateResult:
    prev = (
        sorted(p for p in (config.LAKE / "_ops" / "reports").glob("*.json"))
        if (config.LAKE / "_ops" / "reports").exists()
        else []
    )
    history = []
    for p in prev:
        rep = json.loads(p.read_text())
        if rep["ds"] < ds.isoformat() and rep["status"] == "published":
            history.append(rep["rows_read"])
    g = quality.run_gate(ds, _bronze_rows(ds), history)
    lh.overwrite_partition(lh.T_QUAR, pa.Table.from_pylist(g.rejects, schema=lh.REJECT_SCHEMA), ds.isoformat(), "ds")
    _report_path("reports", ds.isoformat()).write_text(
        json.dumps(
            {
                "ds": g.ds,
                "status": "blocked" if g.blocked else "published",
                "rows_read": g.rows_read,
                "valid": len(g.valid),
                "rejected": len(g.rejects),
                "reject_rate": round(g.reject_rate, 4),
                "checks": [asdict(c) for c in g.checks],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return g


# ------------------------------------------------------------------ 3. silver (MERGE ACID)
def silver(ds: date) -> dict:
    rep_file = _report_path("reports", ds.isoformat())
    if not rep_file.exists() or json.loads(rep_file.read_text())["status"] != "published":
        raise GateNotPassed(f"gate de {ds} ausente ou bloqueado — silver não roda")
    best: dict[str, dict] = {}
    for r in _bronze_rows(ds):
        rec, _ = quality.parse_line(r["raw"])
        if rec is None:
            continue
        rec.update(_ingest_ds=ds.isoformat(), _source_file=r["_source_file"])
        key = (rec["updated_at"], r["_line_no"])
        if rec["order_id"] not in best or key > best[rec["order_id"]][0]:
            best[rec["order_id"]] = (key, rec)
    batch = pa.Table.from_pylist([v[1] for v in best.values()], schema=lh.SILVER_SCHEMA)
    m = lh.merge_silver(batch)
    return {"batch_orders": batch.num_rows, "inserted": m["num_target_rows_inserted"], "updated": m["num_target_rows_updated"]}


# ------------------------------------------------------------------ 4. gold (ELT em SQL, DuckDB)
GOLD_SQL = {
    "daily_revenue": """
        SELECT order_date, country, category, count(*) AS orders, sum(amount) AS revenue,
               cast(round(avg(amount), 2) AS DECIMAL(12,2)) AS avg_ticket
        FROM silver WHERE status <> 'canceled' GROUP BY ALL ORDER BY ALL""",
    "customer_ltv": """
        SELECT customer_id, count(*) AS orders, sum(amount) AS lifetime_revenue,
               min(order_date) AS first_order, max(order_date) AS last_order
        FROM silver WHERE status <> 'canceled' GROUP BY customer_id ORDER BY customer_id""",
    "order_status_funnel": "SELECT status, count(*) AS orders FROM silver GROUP BY status ORDER BY status",
}


def gold() -> dict:
    from deltalake import write_deltalake

    con = duckdb.connect()
    con.register("silver", lh.read(*lh.T_SILVER))
    out = {}
    for name, sql in GOLD_SQL.items():
        t = con.sql(sql).to_arrow_table()
        write_deltalake(lh.path("gold", name), t, mode="overwrite", schema_mode="overwrite")
        out[name] = t.num_rows
    con.close()  # fechar explicitamente: threads do DuckDB vivas no encerramento do interpretador abortam o processo
    return out


def timed(fn, *a, **k):
    t0 = time.perf_counter()
    res = fn(*a, **k)
    return res, time.perf_counter() - t0
