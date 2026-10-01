from __future__ import annotations

from confluent_kafka import Consumer


def make_consumer(
    bootstrap: str,
    group: str,
    topic: str,
    *,
    assignor: str = "cooperative-sticky",
    on_assign=None,
    on_revoke=None,
) -> Consumer:
    """Consumidor com commit MANUAL: o offset só avança depois que o destino confirmou a gravação."""
    c = Consumer(
        {
            "bootstrap.servers": bootstrap,
            "group.id": group,
            "auto.offset.reset": "earliest",  # grupo novo começa do início do log
            "enable.auto.commit": False,
            "partition.assignment.strategy": assignor,
            "session.timeout.ms": 10000,  # sem heartbeat por 10 s ⇒ o broker o considera morto
        }
    )
    kw = {}
    if on_assign:
        kw["on_assign"] = on_assign
    if on_revoke:
        kw["on_revoke"] = on_revoke
    c.subscribe([topic], **kw)
    return c
