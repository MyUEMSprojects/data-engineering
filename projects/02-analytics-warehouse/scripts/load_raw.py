#!/usr/bin/env python3
"""Carrega o estado sintético da origem no schema `raw` do PostgreSQL (o "EL" do ELT).

Cada execução é um *full refresh* da camada raw (espelha uma réplica da origem).
O histórico de mudanças NÃO se perde: é capturado depois pelo `dbt snapshot` (SCD2).

    python scripts/load_raw.py --day 1     # estado inicial
    python scripts/load_raw.py --day 2     # clientes mudaram + novos pedidos
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg
from raw_data import generate

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = {
    "customers": ["customer_id", "name", "email", "uf", "segment", "updated_at"],
    "products": ["product_id", "name", "category", "list_price", "updated_at"],
    "orders": ["order_id", "customer_id", "order_ts", "status", "updated_at"],
    "order_items": [
        "order_id",
        "line_no",
        "product_id",
        "quantity",
        "unit_price",
        "discount",
    ],
}


def load(dsn: str, day: int) -> dict[str, int]:
    data = generate(day)
    counts: dict[str, int] = {}
    with psycopg.connect(dsn) as conn, conn.transaction():  # tudo-ou-nada
        conn.execute((ROOT / "sql/raw_schema.sql").read_text())
        for table, cols in COLUMNS.items():
            conn.execute(f"TRUNCATE raw.{table}")
            with conn.cursor().copy(
                f"COPY raw.{table} ({', '.join(cols)}) FROM STDIN"
            ) as cp:
                for row in data[table]:
                    cp.write_row([row[c] for c in cols])
            counts[table] = len(data[table])
    return counts


def default_dsn() -> str:
    return (
        f"postgresql://{os.getenv('DBT_USER', 'de')}:{os.getenv('DBT_PASSWORD', 'de')}"
        f"@{os.getenv('DBT_HOST', 'localhost')}:{os.getenv('DBT_PORT', '5432')}"
        f"/{os.getenv('DBT_DBNAME', 'warehouse')}"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, choices=[1, 2], default=1)
    ap.add_argument("--dsn", default=default_dsn())
    a = ap.parse_args()
    print(load(a.dsn, a.day))
