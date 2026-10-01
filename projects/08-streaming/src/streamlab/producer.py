from __future__ import annotations

from confluent_kafka import Producer

from .events import Phase, parse_click


def produce_phase(bootstrap: str, topic: str, phase: Phase) -> int:
    p = Producer({"bootstrap.servers": bootstrap, "enable.idempotence": True, "acks": "all", "linger.ms": 20})
    failed = []

    def cb(err, _m):
        if err:
            failed.append(err)

    for raw in phase.messages:
        c = parse_click(raw)
        key = c.user_id.encode() if c else None  # chave = usuário ⇒ ordem por usuário numa partição
        while True:
            try:
                p.produce(topic, key=key, value=raw, on_delivery=cb)
                break
            except BufferError:
                p.poll(0.5)
        p.poll(0)
    p.flush(60)
    if failed:
        raise RuntimeError(f"{len(failed)} mensagens não entregues: {failed[0]}")
    return len(phase.messages)
