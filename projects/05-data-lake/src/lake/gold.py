"""Gold: tabelas ANALÍTICAS prontas para consumo, derivadas da silver (DuckDB sobre Arrow).

Recomputadas por inteiro e publicadas de forma idempotente. São pequenas e baratas de refazer —
por isso *full refresh* é a escolha certa aqui (em volumes grandes: incremental por partição).
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import pyarrow as pa

from .publish import publish_dir
from .reader import read_silver
from .storage import Lake

GOLD_SQL = {
    "daily_revenue": """
        select cast(order_date as date) as order_date, country, category,
               count(*)                          as orders,
               sum(amount)                       as revenue,
               cast(round(avg(amount), 2) as decimal(12, 2)) as avg_ticket
        from silver_orders
        where status <> 'canceled'
        group by order_date, country, category
        order by order_date, country, category
    """,
    "customer_value": """
        select customer_id,
               count(*)              as orders,
               sum(amount)           as lifetime_revenue,
               min(order_date)       as first_order_date,
               max(order_date)       as last_order_date
        from silver_orders
        where status <> 'canceled'
        group by customer_id
        order by customer_id
    """,
    "status_funnel": """
        select order_date, status, count(*) as orders
        from silver_orders
        group by order_date, status
        order by order_date, status
    """,
}


@dataclass(frozen=True)
class GoldResult:
    table: str
    rows: int
    written: bool


def connect(lake: Lake) -> duckdb.DuckDBPyConnection:
    """Conexão DuckDB com a silver registrada como ``silver_orders``."""
    con = duckdb.connect()
    con.register("silver_orders", read_silver(lake))
    return con


def build_gold(lake: Lake) -> list[GoldResult]:
    con = connect(lake)
    out = []
    for name, sql in GOLD_SQL.items():
        table: pa.Table = con.sql(sql).to_arrow_table()
        res = publish_dir(lake, f"gold/{name}", table)
        out.append(GoldResult(name, table.num_rows, res.written))
    return out
