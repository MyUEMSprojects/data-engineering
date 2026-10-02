"""Loop do consumidor: at-least-once com destino idempotente (⇒ efeito *exactly-once* no destino).

Ordem das operações em CADA lote (a que garante "nunca perder"):

    1. parse/validação      → inválidas vão para a DLQ (com o motivo nos headers)
    2. flush da DLQ         → a DLQ precisa estar durável ANTES de avançarmos o offset
    3. escrita no destino   → 1 transação; idempotente
    4. commit dos offsets   → só DEPOIS de 2 e 3

Se o processo morrer entre 3 e 4, o lote é REENTREGUE e reaplicado — sem duplicar, porque o destino
é idempotente. Inverter 3 e 4 (commit antes de gravar) trocaria "pode duplicar" por "pode PERDER".
"""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable

from confluent_kafka import KafkaError, KafkaException, TopicPartition

from .events import InvalidEvent, parse_event
from .sink import Record, Sink

log = logging.getLogger("kpipe")


class Pipeline:
    def __init__(
        self,
        consumer,
        sink: Sink,
        dlq_producer,
        dlq_topic: str,
        *,
        batch_size: int = 500,
        poll_timeout: float = 1.0,
        before_commit: Callable[[int], None] | None = None,
    ):
        self.consumer, self.sink, self.dlq = consumer, sink, dlq_producer
        self.dlq_topic = dlq_topic
        self.batch_size, self.poll_timeout = batch_size, poll_timeout
        self.before_commit = before_commit  # gancho de injeção de falha (testes/demo)
        self.stats: Counter = Counter()
        self.batches = 0

    # ------------------------------------------------------------------ loop
    def run(self, *, max_idle_s: float = 5.0, stop: Callable[[], bool] = lambda: False) -> Counter:
        idle = 0.0
        while not stop():
            msgs = self.consumer.consume(self.batch_size, self.poll_timeout)
            if not msgs:
                idle += self.poll_timeout
                if idle >= max_idle_s:
                    break
                continue
            idle = 0.0
            self.process_batch(msgs)
        return self.stats

    # ------------------------------------------------------------------ 1 lote
    def process_batch(self, msgs) -> None:
        records: list[Record] = []
        positions: dict[tuple[str, int], int] = {}
        for m in msgs:
            err = m.error()
            if err:
                if err.code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(err)
            positions[(m.topic(), m.partition())] = max(
                positions.get((m.topic(), m.partition()), -1), m.offset()
            )
            try:
                ev = parse_event(m.value())
            except InvalidEvent as e:
                self._to_dlq(m, str(e))
                continue
            records.append(Record(ev, m.partition(), m.offset()))

        self.dlq.flush(30)  # (2) DLQ durável antes do commit
        ws = self.sink.write(records)  # (3) destino idempotente
        self.batches += 1
        if self.before_commit:
            self.before_commit(self.batches)  # injeção de falha: aqui = "crash entre 3 e 4"
        if positions:
            self.consumer.commit(
                offsets=[TopicPartition(t, p, off + 1) for (t, p), off in positions.items()],
                asynchronous=False,
            )  # (4)
        self.stats["messages"] += len(msgs)
        self.stats["inserted"] += ws.inserted
        self.stats["duplicates_ignored"] += ws.duplicates
        self.stats["state_updates"] += ws.state_updates
        self.stats["stale_ignored"] += ws.stale_ignored

    def _to_dlq(self, m, reason: str) -> None:
        self.stats["dlq"] += 1
        headers = [
            ("error", reason.encode()),
            ("source", f"{m.topic()}:{m.partition()}:{m.offset()}".encode()),
        ]
        while True:
            try:
                self.dlq.produce(self.dlq_topic, key=m.key(), value=m.value(), headers=headers)
                return
            except BufferError:
                self.dlq.poll(0.5)
