import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from raw_data import generate


def test_deterministico():
    assert generate(1) == generate(1)


def test_integridade_referencial_dia1():
    d = generate(1)
    cust = {c["customer_id"] for c in d["customers"]}
    prod = {p["product_id"] for p in d["products"]}
    orders = {o["order_id"] for o in d["orders"]}
    assert all(o["customer_id"] in cust for o in d["orders"])
    assert all(
        i["product_id"] in prod and i["order_id"] in orders for i in d["order_items"]
    )


def test_chaves_unicas():
    d = generate(1)
    assert len({o["order_id"] for o in d["orders"]}) == len(d["orders"])
    assert len({(i["order_id"], i["line_no"]) for i in d["order_items"]}) == len(
        d["order_items"]
    )


def test_dia2_muda_clientes_e_adiciona_pedidos():
    d1, d2 = generate(1), generate(2)
    assert len(d2["orders"]) > len(d1["orders"])
    c1 = {c["customer_id"]: c for c in d1["customers"]}
    changed = [
        c
        for c in d2["customers"]
        if c["updated_at"] != c1[c["customer_id"]]["updated_at"]
    ]
    assert changed and all(c["uf"] != c1[c["customer_id"]]["uf"] for c in changed)
    # quem não mudou, permanece idêntico
    same = [c for c in d2["customers"] if c not in changed]
    assert all(c == c1[c["customer_id"]] for c in same)
