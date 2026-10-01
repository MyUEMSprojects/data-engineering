"""Lógica PURA do pipeline (sem Airflow, sem banco): testável com pytest em qualquer lugar.

O DAG só orquestra; a lógica de dados vive aqui — separation of concerns
(orquestre, não transforme: ver módulo 11).
"""

from __future__ import annotations

import csv
import os
import random
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ["order_id", "customer_id", "amount", "status", "order_date", "created_at"]
VALID_STATUS = {"created", "paid", "shipped", "canceled"}


def generate_orders(
    day: date, n: int = 200, dirty_rate: float = 0.02
) -> list[dict[str, str]]:
    """Pedidos SINTÉTICOS de UM dia. **Determinístico por data** (seed = ordinal do dia).

    Determinismo é o que torna o extract idempotente: reexecutar a mesma data
    produz exatamente os mesmos dados. `dirty_rate` injeta linhas inválidas.
    """
    rng = random.Random(day.toordinal())
    base = datetime(day.year, day.month, day.day, tzinfo=UTC)
    rows = []
    for i in range(n):
        ts = base + timedelta(seconds=rng.randint(0, 86399))
        rows.append(
            {
                "order_id": f"{day:%Y%m%d}-{i:05d}",
                "customer_id": f"C{rng.randint(1, 500):04d}",
                "amount": f"{rng.uniform(5, 800):.2f}",
                "status": rng.choice(sorted(VALID_STATUS)),
                "order_date": day.isoformat(),
                "created_at": ts.isoformat(),
            }
        )
    for r in rows:
        if rng.random() < dirty_rate:
            kind = rng.choice(["status", "amount", "customer"])
            if kind == "status":
                r["status"] = "ENTREGUE"
            elif kind == "amount":
                r["amount"] = "-1"
            else:
                r["customer_id"] = ""
    return rows


def partition_path(root: Path | str, day: date) -> Path:
    """Caminho DETERMINÍSTICO da partição (estilo Hive): rodar de novo sobrescreve, não acumula."""
    return Path(root) / "raw" / "orders" / f"dt={day.isoformat()}" / "orders.csv"


def write_csv_atomic(path: Path, rows: Iterable[Mapping[str, str]]) -> int:
    """Escreve em arquivo temporário e `replace` (atômico): ninguém lê um arquivo pela metade."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow(r)
                n += 1
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return n


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@dataclass(frozen=True)
class ValidationResult:
    valid: list[dict[str, str]]
    rejected: list[tuple[dict[str, str], str]]

    @property
    def total(self) -> int:
        return len(self.valid) + len(self.rejected)

    @property
    def reject_rate(self) -> float:
        return len(self.rejected) / self.total if self.total else 0.0


def _check(row: Mapping[str, str], day: date) -> str | None:
    """Devolve o motivo da rejeição, ou None se a linha é válida."""
    if not row.get("order_id"):
        return "order_id ausente"
    if not row.get("customer_id", "").strip():
        return "customer_id ausente"
    try:
        if Decimal(row["amount"]) < 0:
            return "amount negativo"
    except (InvalidOperation, KeyError):
        return "amount inválido"
    if row.get("status") not in VALID_STATUS:
        return f"status inválido: {row.get('status')!r}"
    if row.get("order_date") != day.isoformat():
        return "order_date fora da partição"  # linha de outro dia no arquivo errado
    return None


def validate(rows: Iterable[Mapping[str, str]], day: date) -> ValidationResult:
    valid, rejected, seen = [], [], set()
    for raw in rows:
        row = dict(raw)
        reason = _check(row, day)
        if reason is None and row["order_id"] in seen:
            reason = "order_id duplicado"
        if reason:
            rejected.append((row, reason))
        else:
            seen.add(row["order_id"])
            valid.append(row)
    return ValidationResult(valid, rejected)


def summarize(valid: Iterable[Mapping[str, str]]) -> dict[str, Decimal | int]:
    """Agregados do dia (exclui cancelados da receita)."""
    orders, revenue = 0, Decimal(0)
    for r in valid:
        orders += 1
        if r["status"] != "canceled":
            revenue += Decimal(r["amount"])
    return {"orders": orders, "revenue": revenue.quantize(Decimal("0.01"))}
