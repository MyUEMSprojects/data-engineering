"""Destino PostgreSQL IDEMPOTENTE. Reaplicar o mesmo lote não muda o resultado."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import psycopg

from .events import OrderEvent

INSERT_EVENT = """
INSERT INTO order_events (event_id, order_id, seq, customer_id, status, amount, event_ts,
                          kafka_partition, kafka_offset)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (event_id) DO NOTHING
RETURNING event_id
"""
UPSERT_STATE = """
INSERT INTO orders_current (order_id, customer_id, status, amount, seq, updated_at)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (order_id) DO UPDATE
   SET customer_id = EXCLUDED.customer_id, status = EXCLUDED.status, amount = EXCLUDED.amount,
       seq = EXCLUDED.seq, updated_at = EXCLUDED.updated_at
 WHERE EXCLUDED.seq > orders_current.seq          -- o estado só AVANÇA
RETURNING order_id
"""


@dataclass(frozen=True)
class Record:
    event: OrderEvent
    partition: int
    offset: int


@dataclass
class WriteStats:
    inserted: int = 0  # eventos novos
    duplicates: int = 0  # reentregas ignoradas (event_id já existia)
    state_updates: int = 0
    stale_ignored: int = 0  # evento mais antigo que o estado atual
    detail: dict = field(default_factory=dict)


class Sink(Protocol):
    def write(self, records: list[Record]) -> WriteStats: ...


class PostgresSink:
    def __init__(self, dsn: str):
        self.conn = psycopg.connect(dsn, autocommit=True)

    def close(self) -> None:
        self.conn.close()

    def write(self, records: list[Record]) -> WriteStats:
        stats = WriteStats()
        if not records:
            return stats
        # estado: dentro do lote, só o evento de maior seq por pedido importa
        latest: dict[str, OrderEvent] = {}
        for r in records:
            cur = latest.get(r.event.order_id)
            if cur is None or r.event.seq > cur.seq:
                latest[r.event.order_id] = r.event

        with self.conn.transaction(), self.conn.cursor() as cur:  # TUDO ou NADA
            cur.executemany(
                INSERT_EVENT,
                [
                    (
                        r.event.event_id,
                        r.event.order_id,
                        r.event.seq,
                        r.event.customer_id,
                        r.event.status,
                        r.event.amount,
                        r.event.event_ts,
                        r.partition,
                        r.offset,
                    )
                    for r in records
                ],
                returning=True,
            )
            while True:
                if cur.fetchone() is not None:
                    stats.inserted += 1
                if not cur.nextset():
                    break
            stats.duplicates = len(records) - stats.inserted

            cur.executemany(
                UPSERT_STATE,
                [
                    (e.order_id, e.customer_id, e.status, e.amount, e.seq, e.event_ts)
                    for e in latest.values()
                ],
                returning=True,
            )
            while True:
                if cur.fetchone() is not None:
                    stats.state_updates += 1
                if not cur.nextset():
                    break
            stats.stale_ignored = len(latest) - stats.state_updates
        return stats
