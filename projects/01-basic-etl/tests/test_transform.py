from datetime import UTC, datetime
from decimal import Decimal

import pytest

from basic_etl.transform import ValidationError, deduplicate, parse_order, validate_rows


def raw(**overrides):
    base = {
        "order_id": "O-1",
        "customer_id": "C-1",
        "amount": "10.50",
        "status": "paid",
        "uf": "sp",
        "created_at": "2024-01-10T10:00:00Z",
        "updated_at": "2024-01-10T11:00:00Z",
    }
    base.update(overrides)
    return base


def test_parse_ok_normaliza_campos():
    o = parse_order(raw(status="PAID", uf="sp", amount="10,5"))
    assert o.status == "paid" and o.uf == "SP"
    assert o.amount == Decimal("10.50")
    assert o.created_at == datetime(2024, 1, 10, 10, tzinfo=UTC)


def test_data_sem_fuso_vira_utc():
    o = parse_order(raw(created_at="2024-01-10T10:00:00", updated_at="2024-01-10T10:00:00"))
    assert o.created_at.tzinfo is UTC


def test_updated_at_ausente_usa_created_at():
    r = raw()
    del r["updated_at"]
    assert parse_order(r).updated_at == parse_order(r).created_at


def test_uf_vazia_vira_none():
    assert parse_order(raw(uf="")).uf is None


@pytest.mark.parametrize(
    "overrides, trecho",
    [
        ({"order_id": ""}, "order_id"),
        ({"customer_id": "  "}, "customer_id"),
        ({"amount": "abc"}, "amount"),
        ({"amount": "-1"}, "fora do domínio"),
        ({"amount": "NaN"}, "fora do domínio"),
        ({"status": "ENTREGUE"}, "status"),
        ({"uf": "XX"}, "uf"),
        ({"created_at": "ontem"}, "created_at"),
        ({"updated_at": "2023-01-01T00:00:00Z"}, "anterior"),
    ],
)
def test_linhas_invalidas(overrides, trecho):
    with pytest.raises(ValidationError, match=trecho):
        parse_order(raw(**overrides))


def test_validate_rows_separa_e_nao_perde_linhas():
    rows = [raw(order_id="A"), raw(order_id="B", status="x"), raw(order_id="C")]
    valid, rejected = validate_rows(rows)
    assert [o.order_id for o in valid] == ["A", "C"]
    assert len(rejected) == 1 and "status" in rejected[0][1]
    assert len(valid) + len(rejected) == len(rows)


def test_deduplicate_mantem_versao_mais_recente():
    velho = parse_order(raw(order_id="A", status="created", updated_at="2024-01-10T11:00:00Z"))
    novo = parse_order(raw(order_id="A", status="shipped", updated_at="2024-01-10T15:00:00Z"))
    outro = parse_order(raw(order_id="B"))
    out = deduplicate([novo, velho, outro])  # ordem de chegada não importa
    assert {o.order_id: o.status for o in out} == {"A": "shipped", "B": "paid"}


def test_deduplicate_e_idempotente():
    a = parse_order(raw(order_id="A"))
    once = deduplicate([a, a])
    assert deduplicate(once) == once
