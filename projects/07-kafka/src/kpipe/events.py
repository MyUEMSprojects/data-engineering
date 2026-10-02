"""Contrato do evento + geração determinística + parsing/validação.

Um pedido tem um CICLO DE VIDA: created → paid → shipped → delivered (ou canceled). Cada passo é
um evento com ``seq`` crescente por pedido. A chave da mensagem é o ``order_id``: o Kafka só
garante ordem DENTRO de uma partição, e a mesma chave sempre cai na mesma partição.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation

SCHEMA_VERSION = 1
STATUSES = ("created", "paid", "shipped", "delivered", "canceled")
LIFECYCLES = (
    ("created", "paid", "shipped", "delivered"),
    ("created", "paid", "shipped", "delivered"),
    ("created", "paid", "shipped", "delivered"),
    ("created", "paid", "canceled"),
    ("created", "canceled"),
)


class InvalidEvent(ValueError):
    """Mensagem que NÃO deve ser reprocessada: vai para a DLQ com o motivo."""


@dataclass(frozen=True)
class OrderEvent:
    order_id: str
    seq: int
    customer_id: str
    status: str
    amount: Decimal
    event_ts: datetime
    schema_version: int = SCHEMA_VERSION

    @property
    def event_id(self) -> str:  # chave natural de idempotência
        return f"{self.order_id}-{self.seq}"

    def to_bytes(self) -> bytes:
        d = asdict(self)
        d["amount"] = str(self.amount)
        d["event_ts"] = self.event_ts.isoformat()
        return json.dumps(d, separators=(",", ":")).encode()


def parse_event(raw: bytes | None) -> OrderEvent:
    """bytes → OrderEvent ou ``InvalidEvent`` com motivo explícito (nunca devolve lixo)."""
    if not raw:
        raise InvalidEvent("empty_payload")
    try:
        d = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise InvalidEvent("invalid_json") from e
    if not isinstance(d, dict):
        raise InvalidEvent("invalid_json")
    if d.get("schema_version") != SCHEMA_VERSION:
        raise InvalidEvent(f"unsupported_schema_version:{d.get('schema_version')}")
    for f in ("order_id", "seq", "customer_id", "status", "amount", "event_ts"):
        if d.get(f) in (None, ""):
            raise InvalidEvent(f"missing_field:{f}")
    if not isinstance(d["seq"], int) or isinstance(d["seq"], bool) or d["seq"] < 1:
        raise InvalidEvent("bad_seq")
    if d["status"] not in STATUSES:
        raise InvalidEvent("unknown_status")
    try:
        amount = Decimal(str(d["amount"]))
    except InvalidOperation as e:
        raise InvalidEvent("bad_amount") from e
    if not amount.is_finite() or amount < 0:
        raise InvalidEvent("bad_amount")
    try:
        ts = datetime.fromisoformat(str(d["event_ts"]))
    except ValueError as e:
        raise InvalidEvent("bad_timestamp") from e
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return OrderEvent(
        str(d["order_id"]),
        d["seq"],
        str(d["customer_id"]),
        d["status"],
        amount.quantize(Decimal("0.01")),
        ts,
    )


def generate_events(
    n_orders: int, *, seed: int = 42, start: datetime | None = None
) -> Iterator[OrderEvent]:
    """Eventos em ORDEM DE TEMPO (os de pedidos diferentes se intercalam), determinísticos pela seed."""
    rng = random.Random(seed)
    start = start or datetime(2024, 1, 1, tzinfo=UTC)
    events: list[OrderEvent] = []
    for i in range(n_orders):
        order_id = f"O{i:07d}"
        customer = f"C{rng.randint(1, 500):04d}"
        amount = Decimal(str(round(rng.lognormvariate(4.2, 0.8), 2))).quantize(Decimal("0.01"))
        t = start + timedelta(seconds=i * 3 + rng.randint(0, 2))
        for seq, status in enumerate(rng.choice(LIFECYCLES), start=1):
            events.append(OrderEvent(order_id, seq, customer, status, amount, t))
            t += timedelta(seconds=rng.randint(5, 600))
    events.sort(key=lambda e: (e.event_ts, e.order_id, e.seq))
    yield from events


def expected_state(events: list[OrderEvent]) -> dict[str, tuple[str, int]]:
    """Estado final esperado por pedido: (status, seq) do último evento — o 'gabarito' das verificações."""
    out: dict[str, tuple[str, int]] = {}
    for e in events:
        if e.order_id not in out or e.seq > out[e.order_id][1]:
            out[e.order_id] = (e.status, e.seq)
    return out
