"""PostgreSQL: sink idempotente com livro-razão de micro-lotes (exactly-once efetivo no destino)."""

from __future__ import annotations

from datetime import datetime, timezone

import psycopg

UPSERT_WINDOW = """
INSERT INTO page_views_1m (window_start, page, views, users, updated_batch)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (window_start, page) DO UPDATE
   SET views = EXCLUDED.views, users = EXCLUDED.users, updated_batch = EXCLUDED.updated_batch
"""
INSERT_REJECT = """
INSERT INTO stream_rejects (kafka_partition, kafka_offset, reason, raw)
VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
"""


def connect(dsn: str) -> psycopg.Connection:
    return psycopg.connect(dsn, autocommit=True)


def _utc(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def apply_batch(conn: psycopg.Connection, query: str, batch_id: int, sql: str, rows: list[tuple]) -> bool:
    """Aplica o micro-lote UMA vez. Devolve False se (query, batch_id) já foi aplicado.

    Livro-razão + dados na MESMA transação: ou os dois entram, ou nenhum. Se o Spark reexecutar o lote
    depois de uma falha (ele garante reexecução do último lote não confirmado no checkpoint), o
    `ON CONFLICT` do livro-razão impede a segunda aplicação.
    """
    with conn.transaction():
        first = conn.execute(
            "INSERT INTO batch_log (query, batch_id) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING 1",
            (query, batch_id),
        ).fetchone()
        if first is None:
            return False
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
    return True


def window_rows(batch_id: int, rows) -> list[tuple]:
    return [(_utc(r["window_start"]), r["page"], r["views"], r["users"], batch_id) for r in rows]


def fetch_windows(conn: psycopg.Connection) -> dict[tuple[datetime, str], tuple[int, int]]:
    cur = conn.execute("SELECT window_start, page, views, users FROM page_views_1m")
    return {(r[0], r[1]): (r[2], r[3]) for r in cur.fetchall()}


def count(conn: psycopg.Connection, table: str) -> int:
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # noqa: S608 — nome interno


def reset(conn: psycopg.Connection) -> None:
    conn.execute("TRUNCATE page_views_1m, stream_rejects, batch_log")
