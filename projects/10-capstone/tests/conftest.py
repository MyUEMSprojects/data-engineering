import os

import pytest


@pytest.fixture
def lake(tmp_path, monkeypatch):
    from capstone import config

    monkeypatch.setattr(config, "LAKE", tmp_path / "lake")
    return config.LAKE


def pytest_unconfigure(config):
    # deltalake+pyarrow: threads nativas no encerramento do interpretador podem abortar o processo (exit 134)
    # DEPOIS de os testes passarem. Saímos direto com o status correto (ver capstone/__main__.py).
    import sys

    sys.stdout.flush()
    sys.stderr.flush()
    status = getattr(config, "_capstone_exit", None)
    if status is not None:
        os._exit(int(status))


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    session.config._capstone_exit = int(exitstatus)
