"""Gerador SINTÉTICO e determinístico de lotes diários de pedidos, com cenários de falha.

Cada cenário simula um problema real de dados para exercitar um tipo de check:

clean         lote saudável
dirty_rows    ~3% de linhas inválidas (status/valor/cliente) -> quarentena, lote publicado
heavy_dirty   ~12% de linhas inválidas -> estoura max_quarantine_rate -> lote BLOQUEADO
duplicates    chaves duplicadas -> unicidade falha (hard)
schema_drift  a origem renomeou `amount` e adicionou coluna -> schema falha (hard)
volume_drop   só ~15% das linhas chegaram -> volume (hard) + anomalia (soft)
stale         dados com >2 dias de atraso -> freshness falha (hard)
null_uf       20% de `uf` nulo -> warning (soft), lote publicado
mean_shift    valores x4 (ex.: unidade mudou para centavos?) -> anomalia (soft), publicado
"""

from __future__ import annotations

import csv
import random
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

SCENARIOS = [
    "clean", "dirty_rows", "heavy_dirty", "duplicates", "schema_drift",
    "volume_drop", "stale", "null_uf", "mean_shift",
]  # fmt: skip
UFS = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE"]
STATUS = ["created", "paid", "shipped", "canceled"]
FIELDS = ["order_id", "customer_id", "amount", "status", "uf", "created_at"]


def generate_batch(day: date, scenario: str = "clean", seed: int = 11) -> list[dict[str, str]]:
    if scenario not in SCENARIOS:
        raise ValueError(f"cenário desconhecido: {scenario!r}; use um de {SCENARIOS}")
    rng = random.Random(f"{seed}-{day.isoformat()}")  # determinístico por (seed, dia)
    n = int(1000 * rng.uniform(0.95, 1.05))
    base = datetime(day.year, day.month, day.day, tzinfo=UTC)
    rows = [
        {
            "order_id": f"{day:%Y%m%d}-{i:06d}",
            "customer_id": f"C{rng.randint(1, 800):05d}",
            "amount": f"{rng.lognormvariate(4.0, 0.6):.2f}",
            "status": rng.choices(STATUS, [1, 6, 4, 1])[0],
            "uf": rng.choice(UFS),
            "created_at": (base + timedelta(seconds=rng.randint(0, 86399))).isoformat(),
        }
        for i in range(n)
    ]

    def pick(frac: float) -> list[dict[str, str]]:
        return rng.sample(rows, k=max(1, int(len(rows) * frac)))

    if scenario in ("dirty_rows", "heavy_dirty"):
        for r in pick(0.03 if scenario == "dirty_rows" else 0.12):
            kind = rng.choice(["status", "amount", "customer"])
            if kind == "status":
                r["status"] = "ENTREGUE"
            elif kind == "amount":
                r["amount"] = "-5.00"
            else:
                r["customer_id"] = ""
    elif scenario == "duplicates":
        rows += [dict(r) for r in pick(0.02)]
    elif scenario == "schema_drift":
        for r in rows:
            r["total_amount"] = r.pop("amount")  # renomeou a coluna
            r["channel"] = "web"  # e adicionou outra
    elif scenario == "volume_drop":
        rows = rng.sample(rows, k=int(len(rows) * 0.15))
    elif scenario == "stale":
        old = timedelta(days=2)
        for r in rows:
            r["created_at"] = (datetime.fromisoformat(r["created_at"]) - old).isoformat()
    elif scenario == "null_uf":
        for r in pick(0.20):
            r["uf"] = ""
    elif scenario == "mean_shift":
        for r in rows:
            r["amount"] = f"{float(r['amount']) * 4:.2f}"
    return rows


def write_batch(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else FIELDS
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    return path
