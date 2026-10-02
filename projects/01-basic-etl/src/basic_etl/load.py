"""Carga no PostgreSQL: upsert idempotente + quarentena.

Idempotência: `INSERT ... ON CONFLICT DO UPDATE` por `order_id`. Reexecutar o
mesmo arquivo não duplica nem corrompe — pré-requisito de retries/backfill.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator, Mapping, Sequence
from itertools import islice
from typing import Any

import psycopg

from .transform import Order

UPSERT_SQL = """
INSERT INTO orders (order_id, customer_id, amount, status, uf, created_at, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (order_id) DO UPDATE SET
    customer_id = EXCLUDED.customer_id,
    amount      = EXCLUDED.amount,
    status      = EXCLUDED.status,
    uf          = EXCLUDED.uf,
    created_at  = EXCLUDED.created_at,
    updated_at  = EXCLUDED.updated_at,
    _loaded_at  = now()
WHERE EXCLUDED.updated_at >= orders.updated_at   -- nunca regride para versão mais antiga
"""

REJECT_SQL = """
INSERT INTO orders_rejected (row_hash, run_id, raw_row, reason)
VALUES (%s, %s, %s::jsonb, %s)
ON CONFLICT (row_hash) DO NOTHING          -- idempotente: a mesma linha ruim não se repete
"""


def batched(items: Iterable[Any], size: int) -> Iterator[list[Any]]:
    """Agrupa em lotes (equivalente a `itertools.batched`, que só existe no 3.12+)."""
    it = iter(items)
    while batch := list(islice(it, size)):
        yield batch


def _row(o: Order) -> tuple:
    return (o.order_id, o.customer_id, o.amount, o.status, o.uf, o.created_at, o.updated_at)


def _reject_row(run_id: str, raw: Mapping[str, Any], reason: str) -> tuple:
    payload = json.dumps(dict(raw), default=str, sort_keys=True)
    digest = hashlib.md5(f"{payload}|{reason}".encode(), usedforsecurity=False).hexdigest()
    return (digest, run_id, payload, reason)


def upsert_orders(conn: psycopg.Connection, orders: Sequence[Order], batch_size: int = 1000) -> int:
    """Faz upsert em lotes dentro de **uma transação** (tudo ou nada). Retorna nº enviado."""
    sent = 0
    with conn.transaction(), conn.cursor() as cur:
        for batch in batched(orders, batch_size):
            cur.executemany(UPSERT_SQL, [_row(o) for o in batch])
            sent += len(batch)
    return sent


def quarantine(
    conn: psycopg.Connection,
    run_id: str,
    rejected: Sequence[tuple[Mapping[str, Any], str]],
) -> int:
    """Registra as linhas rejeitadas com o motivo (auditoria/reprocesso)."""
    if not rejected:
        return 0
    with conn.transaction(), conn.cursor() as cur:
        cur.executemany(
            REJECT_SQL,
            [_reject_row(run_id, raw, reason) for raw, reason in rejected],
        )
    return len(rejected)
