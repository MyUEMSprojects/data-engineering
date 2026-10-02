"""Fonte sintética e DETERMINÍSTICA: eventos de pedidos em JSON Lines, como uma API/CDC entregaria.

Cada lote (um por dia de ingestão) mistura, de propósito, o que quebra pipelines de verdade:
- pedidos NOVOS do dia;
- ATUALIZAÇÕES de pedidos antigos (status avança) → *late data* em partições passadas;
- linhas DUPLICADAS (entrega at-least-once);
- linhas INVÁLIDAS (JSON truncado, campo ausente, valor negativo, data impossível, status desconhecido).
"""

from __future__ import annotations

import json
import random
from datetime import UTC, date, datetime, timedelta

COUNTRIES = ["BR", "PT", "US", "AR", "MX"]
CATEGORIES = ["electronics", "books", "home", "fashion", "toys"]
PROGRESSION = {1: ["paid", "shipped"], 2: ["shipped", "delivered"], 3: ["delivered", "canceled"]}


def _order_base(seed: int, order_id: str) -> dict:
    """Atributos estáveis de um pedido: derivados do id, para que atualizações os repitam."""
    rng = random.Random(f"{seed}:{order_id}")
    return {
        "order_id": order_id,
        "customer_id": f"C{rng.randint(1, 400):04d}",
        "country": rng.choices(COUNTRIES, weights=[5, 2, 3, 1, 1])[0],
        "category": rng.choice(CATEGORIES),
        "amount": round(rng.lognormvariate(4.2, 0.8), 2),
    }


def _order_id(day: date, i: int) -> str:
    return f"O{day:%Y%m%d}{i:04d}"


def _ts(rng: random.Random, day: date) -> str:
    t = datetime(day.year, day.month, day.day, tzinfo=UTC) + timedelta(
        seconds=rng.randint(0, 86399)
    )
    return t.isoformat()


def generate_batch(
    ingest_date: date,
    *,
    n_new: int = 300,
    update_rate: float = 0.15,
    duplicate_rate: float = 0.03,
    bad_rate: float = 0.02,
    seed: int = 42,
    first_day: date = date(2024, 1, 1),
) -> bytes:
    rng = random.Random(f"{seed}:{ingest_date.isoformat()}")
    lines: list[str] = []

    for i in range(n_new):
        base = _order_base(seed, _order_id(ingest_date, i))
        lines.append(
            json.dumps(
                {
                    **base,
                    "status": rng.choice(["created", "paid"]),
                    "order_date": ingest_date.isoformat(),
                    "updated_at": _ts(rng, ingest_date),
                }
            )
        )

    for age, statuses in PROGRESSION.items():  # atualizações de pedidos de D-1..D-3
        old = ingest_date - timedelta(days=age)
        if old < first_day:  # não existiam pedidos antes do início da história da fonte
            continue
        for i in range(n_new):
            if rng.random() < update_rate / len(PROGRESSION):
                base = _order_base(seed, _order_id(old, i))
                lines.append(
                    json.dumps(
                        {
                            **base,
                            "status": rng.choice(statuses),
                            "order_date": old.isoformat(),
                            "updated_at": _ts(rng, ingest_date),
                        }
                    )
                )

    for _ in range(int(len(lines) * duplicate_rate)):  # at-least-once: a mesma linha, 2x
        lines.append(rng.choice(lines))

    good = json.loads(rng.choice(lines))
    bad_variants = [
        lambda: '{"order_id": "O_TRUNCATED", "amount": 1',  # JSON truncado
        lambda: json.dumps({**good, "order_id": "O_NOAMT", "amount": None}),
        lambda: json.dumps({**good, "order_id": "O_NEG", "amount": -10.5}),
        lambda: json.dumps({**good, "order_id": "O_BADDATE", "order_date": "2024-13-45"}),
        lambda: json.dumps({**good, "order_id": "O_STATUS", "status": "teleported"}),
        lambda: json.dumps({k: v for k, v in good.items() if k != "customer_id"}),
    ]
    for _ in range(max(1, int(len(lines) * bad_rate))):
        lines.insert(rng.randint(0, len(lines)), rng.choice(bad_variants)())

    rng.shuffle(lines)  # a ordem de chegada não é a ordem dos eventos
    return ("\n".join(lines) + "\n").encode("utf-8")
