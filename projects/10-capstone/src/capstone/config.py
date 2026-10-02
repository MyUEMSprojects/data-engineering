from __future__ import annotations

import os
from pathlib import Path

LAKE = Path(os.environ.get("CAPSTONE_LAKE", "./lake")).resolve()
SEED = int(os.environ.get("CAPSTONE_SEED", "42"))

MAX_REJECT_RATE = 0.05  # acima disto o lote é BLOQUEADO (problema na origem, não "umas linhas")
MAX_STALENESS_H = 36  # dado mais novo do lote não pode ser mais velho que isto
MIN_HISTORY_FOR_ANOMALY = 3


def table(*parts: str) -> str:
    return str(LAKE.joinpath(*parts))


def ops(*parts: str) -> Path:
    p = LAKE.joinpath("_ops", *parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
