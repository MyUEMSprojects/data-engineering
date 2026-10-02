import json
import re
import threading
import urllib.request
from http.server import HTTPServer

import duckdb

from dqpipe.cli import main
from dqpipe.exporter import make_handler

from .conftest import START

DAY = START.replace(day=20)


def read(path, sql="select * from '{p}'"):
    return duckdb.connect().execute(sql.format(p=path)).fetchall()


def test_reexecucao_e_idempotente(seeded):
    r1 = seeded(DAY, "dirty_rows")
    pub, quar = r1.paths["publish"], r1.paths["quarantine"]
    before = (read(pub), read(quar), (seeded.out / "state" / "history.json").read_text())
    r2 = seeded(DAY, "dirty_rows")  # MESMA partição, mesmos dados
    after = (read(pub), read(quar), (seeded.out / "state" / "history.json").read_text())
    assert before == after  # sem duplicar linhas nem entradas de histórico
    assert (r1.rows_published, r1.rows_quarantined) == (r2.rows_published, r2.rows_quarantined)


def test_lote_bloqueado_nao_apaga_a_ultima_publicacao_boa(seeded):
    good = seeded(DAY, "clean")
    pub = good.paths["publish"]
    n_before = read(pub, "select count(*) from '{p}'")[0][0]
    bad = seeded(DAY, "duplicates")  # reprocessa a mesma partição com dado ruim
    assert not bad.published
    assert "publish" not in bad.paths
    assert read(pub, "select count(*) from '{p}'")[0][0] == n_before  # consumidores seguem servidos


def test_lote_bloqueado_nao_polui_o_baseline_de_anomalias(seeded):
    seeded(DAY, "volume_drop")  # bloqueado
    history = json.loads((seeded.out / "state" / "history.json").read_text())["orders"]
    assert f"{DAY}" not in history and len(history) == 8


def test_quarentena_guarda_o_original_com_os_motivos(seeded):
    r = seeded(DAY, "dirty_rows")
    rows = read(r.paths["quarantine"], "select order_id, _dq_reasons from '{p}'")
    assert len(rows) == r.rows_quarantined
    assert all(reasons for _, reasons in rows)


def test_publicacao_tem_tipos_do_contrato_e_so_linhas_validas(seeded):
    r = seeded(DAY, "dirty_rows")
    cols = dict(
        read(
            r.paths["publish"],
            "select column_name, column_type from " "(describe select * from '{p}')",
        )
    )
    assert cols["amount"] == "DOUBLE" and cols["created_at"] == "TIMESTAMP"
    bad = read(
        r.paths["publish"],
        "select count(*) from '{p}' where amount < 0 or customer_id is null"
        " or status not in ('created','paid','shipped','canceled')",
    )
    assert bad[0][0] == 0


def test_relatorio_json_e_markdown(seeded):
    r = seeded(DAY, "duplicates")
    report = json.loads(open(r.paths["report"].replace("report.md", "report.json")).read())
    assert report["decision"] == "blocked" and report["reasons"]
    md = open(r.paths["report"], encoding="utf-8").read()
    assert "BLOQUEADO" in md and "pk_unique" in md


SAMPLE = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*(\{[^}]*\})? -?[0-9.e+-]+$")


def test_metricas_no_formato_prometheus(seeded):
    seeded(DAY, "clean")
    text = (seeded.out / "metrics" / "dq.prom").read_text()
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    assert lines and all(SAMPLE.match(ln) for ln in lines), [
        ln for ln in lines if not SAMPLE.match(ln)
    ]
    for name in (
        "dq_check_passed",
        "dq_rows",
        "dq_gate_blocked",
        "dq_data_age_seconds",
        "dq_last_run_timestamp_seconds",
        "dq_contract_info",
    ):
        assert f"# TYPE {name} gauge" in text
    assert 'dq_gate_blocked{dataset="orders"} 0' in text


def test_metricas_refletem_bloqueio_e_check_falho(seeded):
    seeded(DAY, "stale")
    text = (seeded.out / "metrics" / "dq.prom").read_text()
    assert 'dq_gate_blocked{dataset="orders"} 1' in text
    assert (
        'dq_check_passed{dataset="orders",check="freshness",level="dataset",severity="hard"} 0'
        in text
    )


def test_exporter_serve_metrics(seeded):
    seeded(DAY, "clean")
    srv = HTTPServer(("127.0.0.1", 0), make_handler(seeded.out / "metrics" / "dq.prom"))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        body = urllib.request.urlopen(
            f"http://127.0.0.1:{srv.server_port}/metrics", timeout=5
        ).read()
        assert b"dq_gate_blocked" in body
    finally:
        srv.shutdown()


def test_cli_exit_code_0_publicado_e_2_bloqueado(tmp_path):
    out = tmp_path / "out"
    for i in range(6):  # histórico
        d = START.replace(day=1 + i)
        src = tmp_path / f"c{i}.csv"
        assert main(["synth", "--day", str(d), "--out", str(src)]) == 0
        assert (
            main(
                [
                    "run",
                    "--input",
                    str(src),
                    "--partition",
                    str(d),
                    "--out",
                    str(out),
                    "--as-of",
                    f"{d.replace(day=d.day + 1)}T06:00:00+00:00",
                    "--contract",
                    "contracts/orders.yaml",
                ]
            )
            == 0
        )
    d = START.replace(day=20)
    src = tmp_path / "bad.csv"
    main(["synth", "--day", str(d), "--scenario", "duplicates", "--out", str(src)])
    code = main(
        [
            "run",
            "--input",
            str(src),
            "--partition",
            str(d),
            "--out",
            str(out),
            "--as-of",
            f"{d.replace(day=21)}T06:00:00+00:00",
            "--contract",
            "contracts/orders.yaml",
        ]
    )
    assert code == 2
