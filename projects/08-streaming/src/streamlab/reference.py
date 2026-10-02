"""Implementação de REFERÊNCIA (Python puro) da semântica esperada — o 'gabarito' do job Spark.

Modelo (o mesmo do Spark Structured Streaming, em termos de micro-lote):
  • o watermark usado para DESCARTAR no lote N é  max(event_time dos lotes < N) − tolerância;
  • um evento é tardio se o FIM da janela dele ≤ watermark;
  • deduplicação por event_id vem ANTES da agregação.
Cada fase do cenário = 1 micro-lote.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .events import DELAY_S, WINDOW_S, Phase, parse_click


@dataclass
class Expected:
    windows: dict[tuple[datetime, str], tuple[int, int]] = field(
        default_factory=dict
    )  # (início, página) → (views, users)
    rejects: int = 0
    duplicates: int = 0
    dropped_late: int = 0
    watermarks: list[datetime | None] = field(
        default_factory=list
    )  # watermark vigente no INÍCIO de cada fase


def window_start(t: datetime) -> datetime:
    epoch = int(t.timestamp())
    return datetime.fromtimestamp(epoch - epoch % WINDOW_S, tz=t.tzinfo)


def expected_results(phases: list[Phase]) -> Expected:
    exp = Expected()
    users: dict[tuple[datetime, str], set[str]] = {}
    views: dict[tuple[datetime, str], int] = {}
    seen: set[str] = set()
    max_et: datetime | None = None
    for ph in phases:
        wm = max_et - timedelta(seconds=DELAY_S) if max_et else None
        exp.watermarks.append(wm)
        batch_max = None
        for raw in ph.messages:
            c = parse_click(raw)
            if c is None:
                exp.rejects += 1
                continue
            batch_max = c.event_time if batch_max is None else max(batch_max, c.event_time)
            if c.event_id in seen:
                exp.duplicates += 1
                continue
            seen.add(c.event_id)
            ws = window_start(c.event_time)
            if wm is not None and ws + timedelta(seconds=WINDOW_S) <= wm:
                exp.dropped_late += 1
                continue
            key = (ws, c.page)
            views[key] = views.get(key, 0) + 1
            users.setdefault(key, set()).add(c.user_id)
        if batch_max is not None:
            max_et = batch_max if max_et is None else max(max_et, batch_max)
    exp.windows = {k: (views[k], len(users[k])) for k in views}
    return exp
