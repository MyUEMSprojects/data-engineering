from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from confluent_kafka import Consumer, KafkaError, KafkaException, TopicPartition
from confluent_kafka.admin import AdminClient, NewTopic


def admin(bootstrap: str) -> AdminClient:
    return AdminClient({"bootstrap.servers": bootstrap})


def ensure_topics(bootstrap: str, topics: dict[str, int]) -> None:
    """Cria os tópicos se não existirem (idempotente)."""
    a = admin(bootstrap)
    futs = a.create_topics(
        [NewTopic(t, num_partitions=n, replication_factor=1) for t, n in topics.items()]
    )
    for f in futs.values():
        try:
            f.result()
        except KafkaException as e:
            if e.args[0].code() != KafkaError.TOPIC_ALREADY_EXISTS:
                raise


def delete_topics(bootstrap: str, topics: list[str]) -> None:
    a = admin(bootstrap)
    existing = set(a.list_topics(timeout=10).topics)
    todo = [t for t in topics if t in existing]
    if not todo:
        return
    for _, f in a.delete_topics(todo, operation_timeout=30).items():
        f.result()
    deadline = time.time() + 30
    while time.time() < deadline and set(todo) & set(a.list_topics(timeout=10).topics):
        time.sleep(0.5)


@dataclass(frozen=True)
class PartitionLag:
    partition: int
    committed: int
    end: int

    @property
    def lag(self) -> int:
        return self.end - max(self.committed, 0)


def lag(bootstrap: str, group: str, topic: str) -> list[PartitionLag]:
    """Lag = fim do log − offset commitado do grupo. É A métrica de saúde de um consumidor."""
    c = Consumer({"bootstrap.servers": bootstrap, "group.id": group, "enable.auto.commit": False})
    try:
        md = c.list_topics(topic, timeout=10).topics[topic]
        tps = [TopicPartition(topic, p) for p in sorted(md.partitions)]
        committed = {tp.partition: tp.offset for tp in c.committed(tps, timeout=10)}
        out = []
        for tp in tps:
            _, high = c.get_watermark_offsets(tp, timeout=10)
            out.append(PartitionLag(tp.partition, committed[tp.partition], high))
        return out
    finally:
        c.close()


def topic_size(bootstrap: str, topic: str) -> int:
    c = Consumer({"bootstrap.servers": bootstrap, "group.id": f"size-{uuid.uuid4().hex[:6]}"})
    try:
        md = c.list_topics(topic, timeout=10).topics[topic]
        total = 0
        for p in md.partitions:
            lo, hi = c.get_watermark_offsets(TopicPartition(topic, p), timeout=10)
            total += hi - lo
        return total
    finally:
        c.close()


def read_all(bootstrap: str, topic: str, max_idle_s: float = 3.0) -> list:
    """Lê um tópico inteiro desde o início (grupo descartável, sem commit). Para inspecionar a DLQ."""
    c = Consumer(
        {
            "bootstrap.servers": bootstrap,
            "group.id": f"read-{uuid.uuid4().hex[:6]}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    c.subscribe([topic])
    out, idle = [], 0.0
    try:
        while idle < max_idle_s:
            msgs = c.consume(200, 0.5)
            real = [m for m in msgs if not m.error()]
            if real:
                out.extend(real)
                idle = 0.0
            else:
                idle += 0.5
    finally:
        c.close()
    return out
