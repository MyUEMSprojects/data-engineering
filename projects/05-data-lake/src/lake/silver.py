"""Silver: dado LIMPO, tipado, deduplicado e particionado por ``order_date`` (data de NEGÓCIO).

Regras (todas testadas):
1. Cada linha da bronze é parseada e validada; inválidas vão para **quarentena** com o motivo
   (nada some em silêncio: ``lidas = válidas + rejeitadas``).
2. Deduplicação por ``order_id`` ficando com o evento de maior ``updated_at``; empate desfeito
   por (data de ingestão, arquivo, linha) — determinístico. Evento **velho chegando tarde não
   sobrescreve** um mais novo.
3. Cada partição é recomputada a partir de TODA a bronze e publicada de forma idempotente
   (partição idêntica ⇒ não reescreve).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

import pyarrow as pa

from .bronze import bronze_prefix
from .publish import publish_dir
from .storage import Lake

REQUIRED = (
    "order_id",
    "customer_id",
    "country",
    "category",
    "amount",
    "status",
    "order_date",
    "updated_at",
)
STATUSES = {"created", "paid", "shipped", "delivered", "canceled"}

SILVER_SCHEMA = pa.schema(
    [
        ("order_id", pa.string()),
        ("customer_id", pa.string()),
        ("country", pa.string()),
        ("category", pa.string()),
        ("amount", pa.decimal128(12, 2)),
        ("status", pa.string()),
        ("updated_at", pa.timestamp("us", tz="UTC")),
        ("_source_file", pa.string()),  # linhagem: de qual arquivo bronze veio
    ]
)
REJECT_SCHEMA = pa.schema(
    [
        ("ingest_date", pa.date32()),
        ("source_file", pa.string()),
        ("line_no", pa.int32()),
        ("reason", pa.string()),
        ("raw", pa.string()),
    ]
)


def silver_dir(order_date: date | None = None) -> str:
    base = "silver/orders"
    return f"{base}/order_date={order_date.isoformat()}" if order_date else base


def parse_line(raw: str) -> tuple[dict | None, str | None]:
    """Devolve (registro, None) ou (None, motivo)."""
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(obj, dict):
        return None, "invalid_json"
    for name in REQUIRED:
        if obj.get(name) in (None, ""):
            return None, f"missing_field:{name}"
    try:
        amount = Decimal(str(obj["amount"]))
    except InvalidOperation:
        return None, "bad_amount"
    if not amount.is_finite():
        return None, "bad_amount"
    if amount < 0:
        return None, "negative_amount"
    try:
        order_date = date.fromisoformat(str(obj["order_date"]))
    except ValueError:
        return None, "bad_date"
    try:
        updated_at = datetime.fromisoformat(str(obj["updated_at"]).replace("Z", "+00:00"))
    except ValueError:
        return None, "bad_timestamp"
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    if obj["status"] not in STATUSES:
        return None, "unknown_status"
    return (
        {
            "order_id": str(obj["order_id"]),
            "customer_id": str(obj["customer_id"]),
            "country": str(obj["country"]),
            "category": str(obj["category"]),
            "amount": amount.quantize(Decimal("0.01")),
            "status": obj["status"],
            "order_date": order_date,
            "updated_at": updated_at.astimezone(UTC),
        },
        None,
    )


@dataclass
class SilverResult:
    bronze_files: int = 0
    lines_read: int = 0
    valid: int = 0
    rejected: int = 0
    orders: int = 0  # após deduplicação
    partitions_written: int = 0
    partitions_unchanged: int = 0
    reject_reasons: Counter = field(default_factory=Counter)

    @property
    def duplicates_removed(self) -> int:
        return self.valid - self.orders


def build_silver(lake: Lake, *, rows_per_file: int = 1_000_000) -> SilverResult:
    res = SilverResult()
    best: dict[str, tuple[tuple, dict]] = {}
    rejects: dict[date, list[dict]] = {}

    files = [f for f in lake.list_files(bronze_prefix()) if f.path.endswith(".jsonl")]
    res.bronze_files = len(files)
    for f in files:
        ingest_date = date.fromisoformat(f.path.split("ingest_date=")[1].split("/")[0])
        text = lake.read(f.path).decode("utf-8", errors="replace")
        for line_no, raw in enumerate(text.split("\n"), start=1):
            if not raw.strip():
                continue
            res.lines_read += 1
            rec, reason = parse_line(raw)
            if rec is None:
                res.rejected += 1
                res.reject_reasons[reason] += 1
                rejects.setdefault(ingest_date, []).append(
                    {
                        "ingest_date": ingest_date,
                        "source_file": f.path,
                        "line_no": line_no,
                        "reason": reason,
                        "raw": raw,
                    }
                )
                continue
            res.valid += 1
            rec["_source_file"] = f.path
            key = (rec["updated_at"], ingest_date, f.path, line_no)
            cur = best.get(rec["order_id"])
            if cur is None or key > cur[0]:
                best[rec["order_id"]] = (key, rec)

    res.orders = len(best)
    by_date: dict[date, list[dict]] = {}
    for _, rec in best.values():
        by_date.setdefault(rec["order_date"], []).append(rec)

    for order_date, recs in sorted(by_date.items()):
        table = pa.Table.from_pylist(
            [{k: v for k, v in r.items() if k != "order_date"} for r in recs],
            schema=SILVER_SCHEMA,
        )
        out = publish_dir(
            lake, silver_dir(order_date), table, sort_by="order_id", rows_per_file=rows_per_file
        )
        if out.written:
            res.partitions_written += 1
        else:
            res.partitions_unchanged += 1

    for ingest_date, rows in rejects.items():  # quarentena (recomputada, também idempotente)
        publish_dir(
            lake,
            f"quarantine/orders/ingest_date={ingest_date.isoformat()}",
            pa.Table.from_pylist(rows, schema=REJECT_SCHEMA),
            sort_by="line_no",
        )
    return res
