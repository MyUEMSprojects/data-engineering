"""Parse + validação (função PURA) e o GATE de qualidade do lote.

`parse_line` é a ÚNICA definição de "linha válida": quality e silver a reutilizam — duas regras
diferentes para a mesma coisa é como silver e gold passam a discordar.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from . import config

REQUIRED = ("order_id", "customer_id", "country", "category", "amount", "status", "order_date", "updated_at")
STATUSES = {"created", "paid", "shipped", "delivered", "canceled"}


def parse_line(raw: str) -> tuple[dict | None, str | None]:
    try:
        o = json.loads(raw)
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(o, dict):
        return None, "invalid_json"
    for f in REQUIRED:
        if o.get(f) in (None, ""):
            return None, f"missing_field:{f}"
    try:
        amount = Decimal(str(o["amount"]))
    except InvalidOperation:
        return None, "bad_amount"
    if not amount.is_finite() or amount < 0:
        return None, "bad_amount"
    try:
        od = date.fromisoformat(str(o["order_date"]))
        ts = datetime.fromisoformat(str(o["updated_at"]).replace("Z", "+00:00"))
    except ValueError:
        return None, "bad_date"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    if o["status"] not in STATUSES:
        return None, "unknown_status"
    return {
        "order_id": str(o["order_id"]),
        "customer_id": str(o["customer_id"]),
        "country": str(o["country"]),
        "category": str(o["category"]),
        "amount": amount.quantize(Decimal("0.01")),
        "status": o["status"],
        "order_date": od,
        "updated_at": ts.astimezone(UTC),
    }, None


@dataclass
class Check:
    name: str
    level: str  # "hard" (bloqueia) | "soft" (avisa)
    passed: bool
    detail: str = ""
    skipped: bool = False


@dataclass
class GateResult:
    ds: str
    rows_read: int
    valid: list[dict] = field(default_factory=list)
    rejects: list[dict] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return any(c.level == "hard" and not c.passed for c in self.checks)

    @property
    def warnings(self) -> list[Check]:
        return [c for c in self.checks if c.level == "soft" and not c.passed and not c.skipped]

    @property
    def reject_rate(self) -> float:
        return len(self.rejects) / self.rows_read if self.rows_read else 0.0


def robust_z(history: list[float], value: float) -> float | None:
    if len(history) < config.MIN_HISTORY_FOR_ANOMALY:
        return None
    med = statistics.median(history)
    mad = statistics.median(abs(x - med) for x in history) * 1.4826
    return 0.0 if mad == 0 and value == med else (None if mad == 0 else (value - med) / mad)


def run_gate(ds: date, raw_rows: list[dict], volume_history: list[int]) -> GateResult:
    """raw_rows: linhas da bronze da partição (dicts com raw/_source_file/_line_no)."""
    g = GateResult(ds.isoformat(), len(raw_rows))
    for r in raw_rows:
        rec, reason = parse_line(r["raw"])
        if rec is None:
            g.rejects.append(
                {"ds": g.ds, "source_file": r["_source_file"], "line_no": r["_line_no"], "reason": reason, "raw": r["raw"]}
            )
        else:
            g.valid.append({**rec, "_ingest_ds": g.ds, "_source_file": r["_source_file"]})

    g.checks.append(Check("not_empty", "hard", g.rows_read > 0, f"{g.rows_read} linhas"))
    g.checks.append(
        Check(
            "reject_rate",
            "hard",
            g.reject_rate <= config.MAX_REJECT_RATE,
            f"{g.reject_rate:.1%} (limite {config.MAX_REJECT_RATE:.0%})",
        )
    )
    if g.valid:
        newest = max(v["updated_at"] for v in g.valid)
        end = datetime(ds.year, ds.month, ds.day, tzinfo=UTC) + timedelta(days=1)
        age_h = (end - newest).total_seconds() / 3600
        g.checks.append(Check("freshness", "hard", age_h <= config.MAX_STALENESS_H, f"dado mais novo tem {age_h:.1f} h"))
        ids = [v["order_id"] for v in g.valid]
        dup = 1 - len(set(ids)) / len(ids)
        g.checks.append(Check("duplicate_rate", "soft", dup <= 0.10, f"{dup:.1%} de linhas repetem order_id"))
    z = robust_z([float(x) for x in volume_history], float(g.rows_read))
    g.checks.append(
        Check(
            "volume_anomaly",
            "soft",
            z is None or abs(z) <= 4,
            "histórico insuficiente" if z is None else f"z={z:+.1f}",
            skipped=z is None,
        )
    )
    return g
