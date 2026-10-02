"""Um teste por cenário de falha: a decisão do gate e o MOTIVO precisam estar corretos."""

import pytest

from dqpipe.synth import SCENARIOS, generate_batch

from .conftest import START, as_of

DAY = START.replace(day=20)


def ids(result):
    return {r.id for r in result.results if r.failed}


def test_clean_publica_sem_avisos(seeded):
    r = seeded(DAY)
    assert r.published and not r.reasons and not r.warnings and r.rows_quarantined == 0


def test_dirty_rows_publica_e_poe_ruins_na_quarentena(seeded):
    r = seeded(DAY, "dirty_rows")
    assert r.published and 0 < r.rows_quarantined <= 0.05 * r.rows_read
    assert r.rows_published + r.rows_quarantined == r.rows_read  # nenhuma linha some
    assert {"customer_not_null", "status_domain", "amount_range"} & ids(r)


def test_heavy_dirty_estoura_limite_de_quarentena(seeded):
    r = seeded(DAY, "heavy_dirty")
    assert not r.published and r.rows_published == 0
    assert any("quarentena" in x for x in r.reasons)


def test_duplicatas_bloqueiam(seeded):
    r = seeded(DAY, "duplicates")
    assert not r.published and "pk_unique" in ids(r)


def test_schema_drift_bloqueia_antes_de_qualquer_outro_check(seeded):
    r = seeded(DAY, "schema_drift")
    assert not r.published
    assert [x.id for x in r.results] == ["schema_matches_contract"]  # nem tenta os demais
    assert "amount" in r.reasons[0] and "total_amount" in r.reasons[0]


def test_volume_drop_bloqueia_e_anomalia_avisa(seeded):
    r = seeded(DAY, "volume_drop")
    assert not r.published
    assert {"volume_in_range", "volume_anomaly"} <= ids(r)


def test_stale_bloqueia_por_freshness(seeded):
    r = seeded(DAY, "stale")
    assert not r.published and "freshness" in ids(r)


def test_null_uf_so_avisa(seeded):
    r = seeded(DAY, "null_uf")
    assert r.published and any("uf_null_rate" in w for w in r.warnings)


def test_mean_shift_so_avisa_via_anomalia(seeded):
    r = seeded(DAY, "mean_shift")
    assert r.published and any("amount_mean_anomaly" in w for w in r.warnings)


def test_anomalia_e_pulada_sem_historico_suficiente(run):
    r = run(START)  # 1º lote: não há baseline
    skipped = {c.id for c in r.results if c.status == "skipped"}
    assert skipped == {"volume_anomaly", "amount_mean_anomaly"}
    assert r.published  # pular não é reprovar


def test_lote_vazio_e_bloqueado(tmp_path, contract):
    from dqpipe.runner import run_batch

    f = tmp_path / "vazio.csv"
    f.write_text("order_id,customer_id,amount,status,uf,created_at\n")
    r = run_batch(f, contract, START, tmp_path / "out")
    assert not r.published and r.reasons == ["lote vazio"]


def test_valor_nao_conversivel_vai_para_quarentena(tmp_path, contract):
    from dqpipe.runner import run_batch
    from dqpipe.synth import write_batch

    rows = generate_batch(START, "clean")
    rows[0]["amount"] = "abc"
    r = run_batch(
        write_batch(tmp_path / "x.csv", rows), contract, START, tmp_path / "o", as_of(START)
    )
    assert r.rows_quarantined == 1
    assert next(c for c in r.results if c.id == "type_cast:amount").failed


def test_todos_os_cenarios_sao_deterministicos():
    for s in SCENARIOS:
        assert generate_batch(START, s) == generate_batch(START, s)


def test_cenario_desconhecido():
    with pytest.raises(ValueError, match="desconhecido"):
        generate_batch(START, "inexistente")
