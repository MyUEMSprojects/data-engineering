"""Gerador determinístico e SINTÉTICO do estado da origem (OLTP) em um dado "dia".

day=1: estado inicial.
day=2: alguns clientes mudaram de UF/segmento (updated_at novo) e entraram novos pedidos
       -> permite demonstrar SCD2 (snapshots) e carga incremental. Nenhum dado é real.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

UFS = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE"]
SEGMENTS = ["varejo", "corporativo", "premium"]
CATEGORIES = {"eletronicos": 300, "casa": 120, "moda": 80, "livros": 40, "esporte": 150}
STATUS = ["created", "paid", "shipped", "canceled"]
D1 = datetime(2024, 1, 1, tzinfo=UTC)
D2 = datetime(2024, 2, 1, tzinfo=UTC)


def generate(
    day: int = 1,
    n_customers: int = 200,
    n_products: int = 50,
    n_orders: int = 1500,
    seed: int = 7,
) -> dict[str, list[dict]]:
    if day not in (1, 2):
        raise ValueError("day deve ser 1 ou 2")
    rng = random.Random(seed)

    customers = [
        {
            "customer_id": f"C{i:05d}",
            "name": f"Cliente {i:05d}",
            "email": f"cliente{i:05d}@exemplo.test",
            "uf": rng.choice(UFS),
            "segment": rng.choice(SEGMENTS),
            "updated_at": D1,
        }
        for i in range(1, n_customers + 1)
    ]
    products = []
    for i in range(1, n_products + 1):
        cat = rng.choice(list(CATEGORIES))
        base = CATEGORIES[cat]
        products.append(
            {
                "product_id": f"P{i:04d}",
                "name": f"Produto {i:04d}",
                "category": cat,
                "list_price": round(base * rng.uniform(0.6, 1.6), 2),
                "updated_at": D1,
            }
        )

    def make_orders(start: int, count: int, t0: datetime, span_days: int):
        orders, items = [], []
        for k in range(start, start + count):
            oid = f"O{k:07d}"
            ts = t0 + timedelta(minutes=rng.randint(0, span_days * 24 * 60))
            orders.append(
                {
                    "order_id": oid,
                    "customer_id": rng.choice(customers)["customer_id"],
                    "order_ts": ts,
                    "status": rng.choices(STATUS, [1, 6, 4, 1])[0],
                    "updated_at": ts,
                }
            )
            for line in range(1, rng.randint(1, 4) + 1):
                p = rng.choice(products)
                items_disc = rng.choice([0, 0, 0, 0.05, 0.1, 0.15])
                items.append(
                    {
                        "order_id": oid,
                        "line_no": line,
                        "product_id": p["product_id"],
                        "quantity": rng.randint(1, 5),
                        "unit_price": round(
                            p["list_price"] * rng.uniform(0.95, 1.05), 2
                        ),
                        "discount": items_disc,
                    }
                )
        return orders, items

    orders, items = make_orders(1, n_orders, D1, 30)

    if day == 2:
        # clientes que mudaram (mesmo customer_id, atributos novos, updated_at mais novo)
        changed = rng.sample(customers, k=max(1, n_customers // 10))
        for c in changed:
            c["uf"] = rng.choice([u for u in UFS if u != c["uf"]])
            c["segment"] = rng.choice([s for s in SEGMENTS if s != c["segment"]])
            c["updated_at"] = D2
        more_o, more_i = make_orders(n_orders + 1, n_orders // 5, D2, 14)
        orders += more_o
        items += more_i

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": items,
    }
