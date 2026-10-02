#!/usr/bin/env python3
"""Gera um CSV sintético de pedidos, **com sujeira proposital** (determinístico por seed).

Inclui: duplicatas com `updated_at` diferente, status inválido, valor negativo,
UF inexistente, campo obrigatório vazio e vírgula decimal — para exercitar a
validação/quarentena/dedupe. Nenhum dado é real.

Uso:  python scripts/generate_sample_data.py --rows 500 --out sample_data/orders.csv
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

UFS = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE"]
STATUS = ["created", "paid", "shipped", "canceled"]
FIELDS = ["order_id", "customer_id", "amount", "status", "uf", "created_at", "updated_at"]


def generate(rows: int, seed: int = 42) -> list[dict[str, str]]:
    rng = random.Random(seed)
    base = datetime(2024, 1, 1, tzinfo=UTC)
    out: list[dict[str, str]] = []
    for i in range(rows):
        created = base + timedelta(minutes=rng.randint(0, 60 * 24 * 30))
        updated = created + timedelta(minutes=rng.randint(0, 600))
        out.append(
            {
                "order_id": f"O-{i:06d}",
                "customer_id": f"C-{rng.randint(1, max(2, rows // 5)):05d}",
                "amount": f"{rng.uniform(5, 900):.2f}",
                "status": rng.choice(STATUS),
                "uf": rng.choice(UFS),
                "created_at": created.isoformat(),
                "updated_at": updated.isoformat(),
            }
        )

    # --- sujeira controlada: ~7% de linhas inválidas + duplicatas (abaixo do gate de 20%) ---
    n = max(1, rows // 60)
    for _ in range(n):  # duplicatas: mesma chave, versão mais nova
        d = dict(rng.choice(out))
        d["status"] = "shipped"
        d["updated_at"] = (datetime.fromisoformat(d["updated_at"]) + timedelta(hours=3)).isoformat()
        out.append(d)
    for _ in range(n):
        out[rng.randrange(rows)]["status"] = "ENTREGUE"  # status inválido
    for _ in range(n):
        out[rng.randrange(rows)]["amount"] = "-10.00"  # valor negativo
    for _ in range(n):
        out[rng.randrange(rows)]["uf"] = "XX"  # UF inexistente
    for _ in range(n):
        out[rng.randrange(rows)]["customer_id"] = ""  # obrigatório vazio
    for _ in range(n):
        r = out[rng.randrange(rows)]
        r["amount"] = r["amount"].replace(".", ",")  # vírgula decimal (aceitável)
    rng.shuffle(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=Path("sample_data/orders.csv"))
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    data = generate(args.rows, args.seed)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(data)
    print(f"{len(data)} linhas gravadas em {args.out}")


if __name__ == "__main__":
    main()
