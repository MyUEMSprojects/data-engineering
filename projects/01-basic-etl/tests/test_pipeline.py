import subprocess
import sys
from pathlib import Path

import pytest

from basic_etl.pipeline import run, transform_stage

ROOT = Path(__file__).resolve().parents[1]
GOOD = {
    "order_id": "A",
    "customer_id": "C",
    "amount": "1",
    "status": "paid",
    "uf": "SP",
    "created_at": "2024-01-01T00:00:00Z",
}


def test_transform_stage_conta_corretamente():
    rows = [GOOD, dict(GOOD), dict(GOOD, order_id="B", status="zzz")]
    orders, rejected, n_read, n_valid = transform_stage(rows)
    assert (n_read, n_valid, len(rejected), len(orders)) == (3, 2, 1, 1)


def test_dry_run_nao_exige_banco():
    stats = run([GOOD], database_url=None, dry_run=True)
    assert stats.read == 1 and stats.loaded == 0


def test_gate_de_rejeicao_aborta_antes_de_carregar():
    ruins = [dict(GOOD, status="x", order_id=str(i)) for i in range(10)]
    with pytest.raises(RuntimeError, match="taxa de rejeição"):
        run(ruins, database_url="postgresql://nunca-conecta", max_reject_rate=0.2)


def test_gerador_e_pipeline_dry_run_ponta_a_ponta(tmp_path):
    csv_path = tmp_path / "o.csv"
    gen = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/generate_sample_data.py"),
            "--rows",
            "300",
            "--out",
            str(csv_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "linhas gravadas" in gen.stdout
    out = subprocess.run(
        [sys.executable, "-m", "basic_etl", "--csv", str(csv_path), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
    )
    assert out.returncode == 0, out.stderr
    assert "RunStats" in out.stdout
