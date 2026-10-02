import copy

import pytest
import yaml

from dqpipe.anomaly import is_anomalous, robust_z
from dqpipe.contract import ContractError, parse_contract

from .conftest import CONTRACT

BASE = yaml.safe_load(CONTRACT.read_text())


def mutated(**changes):
    doc = copy.deepcopy(BASE)
    doc.update(changes)
    return doc


def test_contrato_do_projeto_e_valido():
    c = parse_contract(BASE)
    assert c.dataset == "orders" and c.partition_column == "created_at"
    assert {x.level for x in c.checks} == {"row", "dataset"}


@pytest.mark.parametrize(
    "doc, trecho",
    [
        (mutated(partition_column="nao_existe"), "partition_column"),
        (mutated(max_quarantine_rate=2), "max_quarantine_rate"),
        (
            mutated(
                checks=[{"id": "x", "level": "row", "type": "unique", "columns": ["order_id"]}]
            ),
            "inválido para level",
        ),
        (
            mutated(checks=[{"id": "x", "level": "row", "type": "not_null", "column": "fantasma"}]),
            "não existe",
        ),
        (
            mutated(
                checks=[
                    {
                        "id": "x",
                        "level": "row",
                        "type": "not_null",
                        "column": "uf",
                        "severity": "grave",
                    }
                ]
            ),
            "severity",
        ),
        (
            mutated(
                checks=[
                    {"id": "a", "level": "row", "type": "not_null", "column": "uf"},
                    {"id": "a", "level": "row", "type": "not_null", "column": "uf"},
                ]
            ),
            "duplicado",
        ),
    ],
)
def test_contrato_invalido_falha_cedo(doc, trecho):
    with pytest.raises(ContractError, match=trecho):
        parse_contract(doc)


def test_tipo_de_coluna_nao_suportado():
    doc = copy.deepcopy(BASE)
    doc["schema"]["columns"][0]["type"] = "BLOB"
    with pytest.raises(ContractError, match="tipo não suportado"):
        parse_contract(doc)


def test_robust_z_resiste_a_outlier_no_historico():
    limpo = [100, 101, 99, 100, 102, 98, 100]
    com_outlier = [*limpo, 10_000]
    # média/desvio explodiriam com o outlier; mediana/MAD quase não mudam
    assert abs(robust_z(130, limpo) - robust_z(130, com_outlier)) < 1.5


def test_is_anomalous_historico_insuficiente_pula():
    assert is_anomalous(5, [1, 2, 3], z_max=3, min_history=5) == (None, None)


def test_is_anomalous_detecta_desvio():
    hist = [100, 101, 99, 100, 102, 98]
    assert is_anomalous(100.5, hist, 5, 5)[0] is False
    assert is_anomalous(400, hist, 5, 5)[0] is True


def test_historico_constante_nao_divide_por_zero():
    anomalous, z = is_anomalous(100, [100] * 6, z_max=5, min_history=5)
    assert anomalous is False and z == 0
