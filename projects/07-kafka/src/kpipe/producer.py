from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass

from confluent_kafka import Producer

from .events import OrderEvent

POISON = [
    b'{"order_id": "O_TRUNC", "seq": 1',  # JSON truncado
    b"",  # payload vazio
    b'{"schema_version":1,"order_id":"O_NOAMT","seq":1,"customer_id":"C1","status":"paid","event_ts":"2024-01-01T00:00:00+00:00"}',
    b'{"schema_version":1,"order_id":"O_ST","seq":1,"customer_id":"C1","status":"teleported","amount":"5","event_ts":"2024-01-01T00:00:00+00:00"}',
    b'{"schema_version":99,"order_id":"O_V","seq":1,"customer_id":"C1","status":"paid","amount":"5","event_ts":"2024-01-01T00:00:00+00:00"}',
]


@dataclass
class ProduceStats:
    sent: int = 0
    delivered: int = 0
    failed: int = 0
    poison: int = 0


def make_producer(bootstrap: str) -> Producer:
    return Producer(
        {
            "bootstrap.servers": bootstrap,
            "enable.idempotence": True,  # sem duplicatas por retry do producer (implica acks=all)
            "acks": "all",
            "linger.ms": 20,  # agrupa mensagens → batches maiores
            "compression.type": "lz4",
            "client.id": "kpipe-producer",
        }
    )


def produce_events(
    bootstrap: str, topic: str, events: Iterable[OrderEvent], *, poison: int = 0, seed: int = 1
) -> ProduceStats:
    """Envia os eventos (chave = order_id) e, opcionalmente, mensagens-veneno intercaladas."""
    p = make_producer(bootstrap)
    stats = ProduceStats()
    rng = random.Random(seed)
    payloads: list[tuple[bytes, bytes]] = [(e.order_id.encode(), e.to_bytes()) for e in events]
    for i in range(poison):
        payloads.insert(
            rng.randint(0, len(payloads)), (f"poison-{i}".encode(), POISON[i % len(POISON)])
        )
        stats.poison += 1

    def on_delivery(err, _msg):
        if err is None:
            stats.delivered += 1
        else:
            stats.failed += 1

    for key, value in payloads:
        while True:
            try:
                p.produce(topic, key=key, value=value, on_delivery=on_delivery)
                break
            except BufferError:  # fila local cheia: deixa o producer drenar e tenta de novo
                p.poll(0.5)
        stats.sent += 1
        p.poll(0)
    p.flush(60)
    return stats
