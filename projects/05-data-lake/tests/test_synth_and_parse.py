import json
from datetime import date

import pytest

from lake.silver import parse_line
from lake.synth import generate_batch

from .conftest import event


def test_batch_is_deterministic_and_dated():
    a = generate_batch(date(2024, 1, 5), n_new=50)
    assert a == generate_batch(date(2024, 1, 5), n_new=50)
    assert a != generate_batch(date(2024, 1, 6), n_new=50)


def test_batch_contains_the_hard_cases():
    lines = generate_batch(date(2024, 1, 5), n_new=200).decode().strip().split("\n")
    assert len(lines) != len(set(lines)), "esperava duplicatas exatas (at-least-once)"
    bad = 0
    old = False
    for ln in lines:
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            bad += 1
            continue
        old |= obj.get("order_date") not in (None, "2024-01-05") and obj["order_id"].startswith("O")
    assert bad >= 1 and old, "faltam linhas inválidas ou atualizações de pedidos antigos"


def test_no_updates_before_first_day():
    lines = generate_batch(date(2024, 1, 1), n_new=100).decode().strip().split("\n")
    dates = {json.loads(ln).get("order_date") for ln in lines if ln.startswith('{"order_id": "O2')}
    assert dates <= {"2024-01-01"}


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda e: {**e, "amount": -1}, "negative_amount"),
        (lambda e: {**e, "amount": None}, "missing_field:amount"),
        (lambda e: {**e, "amount": "abc"}, "bad_amount"),
        (lambda e: {**e, "amount": "NaN"}, "bad_amount"),
        (lambda e: {**e, "order_date": "2024-13-45"}, "bad_date"),
        (lambda e: {**e, "updated_at": "ontem"}, "bad_timestamp"),
        (lambda e: {**e, "status": "teleported"}, "unknown_status"),
        (lambda e: {k: v for k, v in e.items() if k != "customer_id"}, "missing_field:customer_id"),
    ],
)
def test_parse_rejects_with_explicit_reason(mutate, reason):
    rec, why = parse_line(json.dumps(mutate(event())))
    assert rec is None and why == reason


def test_parse_invalid_json_and_non_object():
    assert parse_line('{"order_id": "x"')[1] == "invalid_json"
    assert parse_line("[1, 2]")[1] == "invalid_json"


def test_parse_normalizes_types():
    rec, why = parse_line(json.dumps(event(amount=12.3, updated_at="2024-01-01T10:00:00Z")))
    assert why is None
    assert str(rec["amount"]) == "12.30"  # Decimal com 2 casas, sem float
    assert rec["updated_at"].tzinfo is not None
    assert rec["order_date"] == date(2024, 1, 1)
