"""Transformação pura: valida, normaliza e deduplica pedidos.

Sem I/O. Toda a lógica de negócio fica aqui para ser testável sem banco/rede
(separation of concerns — ver módulo 03/07 do repositório).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

VALID_STATUS = {"created", "paid", "shipped", "canceled"}
VALID_UF = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}  # fmt: skip


class ValidationError(ValueError):
    """Linha inválida; a mensagem vira o motivo da quarentena."""


@dataclass(frozen=True, slots=True)
class Order:
    order_id: str
    customer_id: str
    amount: Decimal
    status: str
    uf: str | None
    created_at: datetime
    updated_at: datetime


def _required(raw: Mapping[str, Any], field: str) -> str:
    value = raw.get(field)
    if value is None or str(value).strip() == "":
        raise ValidationError(f"campo obrigatório ausente: {field}")
    return str(value).strip()


def _parse_ts(value: str, field: str) -> datetime:
    """Aceita ISO-8601. Datas sem fuso são assumidas como UTC (política explícita)."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{field} inválido: {value!r}") from exc
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def parse_order(raw: Mapping[str, Any]) -> Order:
    """Converte uma linha crua em `Order` ou levanta `ValidationError`."""
    order_id = _required(raw, "order_id")
    customer_id = _required(raw, "customer_id")

    try:
        amount = Decimal(_required(raw, "amount").replace(",", "."))
    except InvalidOperation as exc:
        raise ValidationError(f"amount inválido: {raw.get('amount')!r}") from exc
    if not amount.is_finite() or amount < 0:
        raise ValidationError(f"amount fora do domínio: {amount}")
    amount = amount.quantize(Decimal("0.01"))

    status = _required(raw, "status").lower()
    if status not in VALID_STATUS:
        raise ValidationError(f"status inválido: {status!r}")

    uf_raw = (raw.get("uf") or "").strip().upper()
    if uf_raw and uf_raw not in VALID_UF:
        raise ValidationError(f"uf inválida: {uf_raw!r}")
    uf = uf_raw or None

    created_at = _parse_ts(_required(raw, "created_at"), "created_at")
    updated_at = _parse_ts(raw.get("updated_at") or raw["created_at"], "updated_at")
    if updated_at < created_at:
        raise ValidationError("updated_at anterior a created_at")

    return Order(order_id, customer_id, amount, status, uf, created_at, updated_at)


def validate_rows(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[list[Order], list[tuple[Mapping[str, Any], str]]]:
    """Separa linhas válidas das rejeitadas (com o motivo). Nunca descarta em silêncio."""
    valid: list[Order] = []
    rejected: list[tuple[Mapping[str, Any], str]] = []
    for raw in rows:
        try:
            valid.append(parse_order(raw))
        except ValidationError as exc:
            rejected.append((raw, str(exc)))
    return valid, rejected


def deduplicate(orders: Iterable[Order]) -> list[Order]:
    """Mantém, por `order_id`, a versão com maior `updated_at` (empate: a última lida).

    Determinístico: a ordem de saída segue a primeira aparição de cada chave.
    """
    best: dict[str, Order] = {}
    for order in orders:
        current = best.get(order.order_id)
        if current is None or order.updated_at >= current.updated_at:
            best[order.order_id] = order
    return list(best.values())
