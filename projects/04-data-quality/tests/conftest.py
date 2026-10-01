from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pytest

from dqpipe.contract import load_contract
from dqpipe.runner import run_batch
from dqpipe.synth import generate_batch, write_batch

CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "orders.yaml"
START = date(2024, 1, 1)


def as_of(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), time(6, 0), tzinfo=UTC)


@pytest.fixture(scope="session")
def contract():
    return load_contract(CONTRACT)


@pytest.fixture()
def run(tmp_path, contract):
    """Executa um lote de um cenário em `tmp_path` e devolve o RunResult."""

    def _run(day: date, scenario: str = "clean", out: Path | None = None):
        src = write_batch(tmp_path / "in" / f"{day}.csv", generate_batch(day, scenario))
        return run_batch(src, contract, day, out or tmp_path / "out", as_of(day))

    _run.out = tmp_path / "out"
    return _run


@pytest.fixture()
def seeded(run):
    """Histórico de 8 lotes saudáveis publicados (acima de min_history=5)."""
    for i in range(8):
        assert run(START + timedelta(days=i)).published
    return run
