"""Testes de integração: exigem um PostgreSQL real.

docker compose up -d
TEST_DATABASE_URL=postgresql://de:de@localhost:5432/warehouse pytest -m integration
"""

import os
from pathlib import Path

import pytest

from basic_etl.pipeline import run

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not URL, reason="defina TEST_DATABASE_URL para rodar"),
]

SCHEMA = (Path(__file__).resolve().parents[1] / "sql/schema.sql").read_text()


@pytest.fixture()
def conn():
    import psycopg

    with psycopg.connect(URL, autocommit=True) as c:
        c.execute(SCHEMA)
        c.execute("TRUNCATE orders, orders_rejected")
        yield c


def row(oid, status="paid", updated="2024-01-01T12:00:00Z", **kw):
    r = {
        "order_id": oid,
        "customer_id": "C",
        "amount": "10",
        "status": status,
        "uf": "SP",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": updated,
    }
    r.update(kw)
    return r


def count(conn, table="orders"):
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_carga_e_idempotente(conn):
    rows = [row("A"), row("B")]
    run(rows, database_url=URL)
    run(rows, database_url=URL)  # rerodar não duplica
    assert count(conn) == 2


def test_upsert_atualiza_mas_nunca_regride(conn):
    run([row("A", status="created", updated="2024-01-01T12:00:00Z")], database_url=URL)
    run([row("A", status="shipped", updated="2024-01-01T15:00:00Z")], database_url=URL)
    run([row("A", status="created", updated="2024-01-01T11:00:00Z")], database_url=URL)  # velho
    status = conn.execute("SELECT status FROM orders WHERE order_id='A'").fetchone()[0]
    assert status == "shipped"


def test_rejeitadas_vao_para_quarentena(conn):
    run(
        [row("A"), row("B", status="invalido"), row("C"), row("D"), row("E"), row("F")],
        database_url=URL,
        max_reject_rate=0.5,
    )
    assert count(conn) == 5 and count(conn, "orders_rejected") == 1
    reason = conn.execute("SELECT reason FROM orders_rejected").fetchone()[0]
    assert "status" in reason


def test_quarentena_e_idempotente(conn):
    rows = [row("A"), row("B", status="invalido"), row("C"), row("D"), row("E"), row("F")]
    run(rows, database_url=URL, max_reject_rate=0.5)
    run(rows, database_url=URL, max_reject_rate=0.5)  # reexecução
    assert count(conn, "orders_rejected") == 1
