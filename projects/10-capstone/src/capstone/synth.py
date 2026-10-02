"""Fonte sintética determinística (um 'extract diário de API'): novos + atualizações + duplicatas + lixo."""

from __future__ import annotations

import json
import random
from datetime import UTC, date, datetime, timedelta

COUNTRIES = ["BR", "PT", "US", "AR", "MX"]
CATEGORIES = ["electronics", "books", "home", "fashion", "toys"]
PROGRESSION = {1: ["paid", "shipped"], 2: ["shipped", "delivered"]}
FIRST_DAY = date(2024, 3, 1)
BAD_RATE = {"clean": 0.0, "dirty": 0.03, "heavy_dirty": 0.15}


def _base(seed: int, order_id: str) -> dict:
    r = random.Random(f"{seed}:{order_id}")
    return {
        "order_id": order_id,
        "customer_id": f"C{r.randint(1, 120):04d}",
        "country": r.choices(COUNTRIES, weights=[5, 2, 3, 1, 1])[0],
        "category": r.choice(CATEGORIES),
        "amount": f"{r.lognormvariate(4.2, 0.8):.2f}",
    }


def _oid(d: date, i: int) -> str:
    return f"O{d:%Y%m%d}{i:04d}"


def _ts(r: random.Random, d: date) -> str:
    return (datetime(d.year, d.month, d.day, tzinfo=UTC) + timedelta(seconds=r.randint(0, 86399))).isoformat()


def generate_extract(ds: date, scenario: str = "clean", *, seed: int = 42, n_new: int = 300) -> bytes:
    r = random.Random(f"{seed}:{ds}")
    lines: list[str] = []
    for i in range(n_new):
        lines.append(
            json.dumps(
                {
                    **_base(seed, _oid(ds, i)),
                    "status": r.choice(["created", "paid"]),
                    "order_date": ds.isoformat(),
                    "updated_at": _ts(r, ds),
                }
            )
        )
    for age, statuses in PROGRESSION.items():  # atualizações de pedidos dos 2 dias anteriores
        old = ds - timedelta(days=age)
        if old < FIRST_DAY:
            continue
        for i in range(n_new):
            if r.random() < 0.08:
                lines.append(
                    json.dumps(
                        {
                            **_base(seed, _oid(old, i)),
                            "status": r.choice(statuses),
                            "order_date": old.isoformat(),
                            "updated_at": _ts(r, ds),
                        }
                    )
                )
    for _ in range(int(len(lines) * 0.02)):  # duplicatas exatas (at-least-once)
        lines.append(r.choice(lines))
    good = json.loads(r.choice(lines))
    variants = [
        lambda: '{"order_id": "BAD_TRUNC", "amount": "1',
        lambda: json.dumps({**good, "order_id": "BAD_AMT", "amount": "abc"}),
        lambda: json.dumps({**good, "order_id": "BAD_NEG", "amount": "-9.90"}),
        lambda: json.dumps({**good, "order_id": "BAD_DATE", "order_date": "2024-13-45"}),
        lambda: json.dumps({**good, "order_id": "BAD_STATUS", "status": "teleported"}),
        lambda: json.dumps({**good, "order_id": None}),
    ]
    for _ in range(int(len(lines) * BAD_RATE[scenario])):
        lines.insert(r.randint(0, len(lines)), r.choice(variants)())
    r.shuffle(lines)
    return ("\n".join(lines) + "\n").encode()
