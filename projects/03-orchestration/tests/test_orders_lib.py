import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "include"))
import orders_lib as lib

D = date(2024, 1, 15)


def test_geracao_e_deterministica_por_data():
    assert lib.generate_orders(D) == lib.generate_orders(D)
    assert lib.generate_orders(D) != lib.generate_orders(date(2024, 1, 16))


def test_particao_tem_so_o_dia_e_ids_unicos():
    rows = lib.generate_orders(D, n=100)
    assert {r["order_date"] for r in rows} == {D.isoformat()}
    assert len({r["order_id"] for r in rows}) == 100


def test_caminho_da_particao_e_deterministico():
    assert (
        lib.partition_path("/data", D).as_posix()
        == "/data/raw/orders/dt=2024-01-15/orders.csv"
    )


def test_escrita_atomica_idempotente_e_sem_lixo(tmp_path):
    p = lib.partition_path(tmp_path, D)
    rows = lib.generate_orders(D, n=50)
    assert lib.write_csv_atomic(p, rows) == 50
    first = p.read_bytes()
    lib.write_csv_atomic(p, rows)  # reexecução
    assert p.read_bytes() == first
    assert not list(p.parent.glob("*.tmp"))  # sem temporários órfãos


def test_escrita_atomica_nao_corrompe_em_falha(tmp_path):
    p = lib.partition_path(tmp_path, D)
    lib.write_csv_atomic(p, lib.generate_orders(D, n=10))
    original = p.read_bytes()

    def boom():
        yield {
            "order_id": "x",
            "customer_id": "c",
            "amount": "1",
            "status": "paid",
            "order_date": D.isoformat(),
            "created_at": "t",
        }
        raise RuntimeError("falha no meio")

    with pytest.raises(RuntimeError):
        lib.write_csv_atomic(p, boom())
    assert p.read_bytes() == original  # arquivo anterior intacto
    assert not list(p.parent.glob("*.tmp"))


def test_validate_nao_perde_linhas_e_acusa_motivos():
    rows = lib.generate_orders(D, n=300, dirty_rate=0.3)
    res = lib.validate(rows, D)
    assert res.total == 300 and res.rejected
    assert all(reason for _, reason in res.rejected)


def test_validate_limpo_nao_rejeita():
    assert lib.validate(lib.generate_orders(D, n=100, dirty_rate=0), D).reject_rate == 0


def test_validate_pega_duplicata_e_outra_data():
    r = lib.generate_orders(D, n=2, dirty_rate=0)
    dup = dict(r[0])
    other = dict(r[1], order_id="X", order_date="2024-01-16")
    res = lib.validate(r + [dup, other], D)
    reasons = sorted(reason for _, reason in res.rejected)
    assert reasons == ["order_date fora da partição", "order_id duplicado"]


def test_summarize_exclui_cancelados():
    valid = [
        {"status": "paid", "amount": "10.00"},
        {"status": "canceled", "amount": "99.00"},
        {"status": "shipped", "amount": "5.50"},
    ]
    assert lib.summarize(valid) == {"orders": 3, "revenue": Decimal("15.50")}
