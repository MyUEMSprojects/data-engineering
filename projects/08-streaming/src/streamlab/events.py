"""Cenário DETERMINÍSTICO em 3 fases, desenhado para exercitar tempo de evento, watermark e deduplicação.

Eixo do tempo (minutos a partir de T0). Janela = 1 min · tolerância (watermark) = 2 min.

    fase 1  tráfego min 0..9 (desordem ≤ 50 s) + duplicatas + lixo         → WM ≈ 7m5x
    fase 2  tráfego min 10..13 + eventos ATRASADOS-MAS-TOLERADOS (min 8,9)  → WM ≈ 11m5x
    fase 3  tráfego min 14..15 + tolerados (min 12) + MUITO ATRASADOS (min 2 e 10) → dropados

"Atrasado" aqui é relativo ao *tempo de evento*, não ao relógio: o evento do min 9 chega na fase 2,
mas ainda cabe na tolerância; o do min 2 chega na fase 3 quando o watermark já passou da janela dele.
As margens são ≥ 30 s para o resultado NÃO depender de como o Spark divide os micro-lotes.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

UTC = timezone.utc  # `datetime.UTC` só existe no Python 3.11+ (a imagem do Spark usa 3.10)
T0 = datetime(2024, 3, 1, 12, 0, tzinfo=UTC)
PAGES = ("home", "search", "product", "cart", "checkout")
WEIGHTS = (30, 25, 25, 12, 8)
WINDOW_S = 60
DELAY_S = 120


@dataclass(frozen=True)
class Click:
    event_id: str
    user_id: str
    page: str
    event_time: datetime

    def to_bytes(self) -> bytes:
        return json.dumps(
            {
                "event_id": self.event_id,
                "user_id": self.user_id,
                "page": self.page,
                "event_time": self.event_time.isoformat(),
            },
            separators=(",", ":"),
        ).encode()


def parse_click(raw: bytes | None) -> Click | None:
    """Espelho Python da regra de parse do job Spark: válido ⇔ os 4 campos presentes e a data parseável."""
    try:
        d = json.loads(raw)
        if not isinstance(d, dict):
            return None
        for k in ("event_id", "user_id", "page", "event_time"):
            if not isinstance(d.get(k), str) or not d[k]:
                return None
        t = datetime.fromisoformat(d["event_time"])
    except (ValueError, TypeError):
        return None
    return Click(d["event_id"], d["user_id"], d["page"], t if t.tzinfo else t.replace(tzinfo=UTC))


@dataclass
class Phase:
    name: str
    messages: list[bytes] = field(default_factory=list)
    late_tolerated: int = 0
    too_late: int = 0


def _traffic(rng: random.Random, tag: str, minutes: range, per_minute: int) -> list[Click]:
    out = []
    for m in minutes:
        for i in range(per_minute):
            t = T0 + timedelta(minutes=m, seconds=rng.randint(0, 59), milliseconds=rng.randint(0, 999))
            out.append(
                Click(
                    f"{tag}-{m:02d}-{i:03d}", f"u{rng.randint(1, 40):02d}", rng.choices(PAGES, WEIGHTS)[0], t
                )
            )
    return out


def _arrival_order(rng: random.Random, clicks: list[Click], jitter_s: float = 50.0) -> list[Click]:
    """Ordem de chegada ≈ ordem de tempo + atraso aleatório (desordem de até `jitter_s`)."""
    return [
        c
        for _, c in sorted(
            ((c.event_time.timestamp() + rng.uniform(0, jitter_s), c) for c in clicks), key=lambda x: x[0]
        )
    ]


def _bad(kind: int, i: int) -> bytes:
    return [
        b'{"event_id": "bad-%d", "user_id": "u01", "page": "home"' % i,  # JSON truncado
        b'{"event_id":"bad-%d","user_id":"u01","event_time":"2024-03-01T12:05:00+00:00"}' % i,  # sem page
        b'{"event_id":"bad-%d","user_id":"u01","page":"home","event_time":"ontem"}' % i,  # data inválida
    ][kind % 3]


def build_scenario(seed: int = 7, per_minute: int = 40) -> list[Phase]:
    rng = random.Random(seed)

    # ---------------- fase 1
    p1c = _traffic(rng, "a", range(0, 10), per_minute)
    p1 = _arrival_order(rng, p1c)
    dups1 = rng.sample(p1, 10)  # duplicatas na MESMA fase (at-least-once do produtor)
    msgs1 = [c.to_bytes() for c in p1] + [c.to_bytes() for c in dups1]
    msgs1 = [*msgs1[:100], _bad(0, 1), *msgs1[100:300], _bad(1, 2), *msgs1[300:]]
    ph1 = Phase("1: tráfego em ordem aproximada (min 0-9) + 10 duplicatas + 2 mensagens inválidas", msgs1)

    # ---------------- fase 2
    p2c = _traffic(rng, "b", range(10, 14), per_minute)
    tol2 = [
        Click(
            f"lt2-{i:03d}",
            f"u{rng.randint(1, 40):02d}",
            rng.choices(PAGES, WEIGHTS)[0],
            T0 + timedelta(minutes=rng.choice((8, 9)), seconds=rng.randint(0, 59)),
        )
        for i in range(15)
    ]
    p2 = _arrival_order(rng, p2c)
    tail1 = [c for c in p1c if c.event_time >= T0 + timedelta(minutes=9, seconds=40)]
    xdups = rng.sample(tail1, min(5, len(tail1)))  # duplicatas ENTRE fases (cauda recente da fase 1)
    msgs2 = [c.to_bytes() for c in p2] + [c.to_bytes() for c in tol2] + [c.to_bytes() for c in xdups]
    rng.shuffle(msgs2)
    msgs2.insert(50, _bad(2, 3))
    ph2 = Phase(
        "2: tráfego min 10-13 + 15 atrasados-mas-tolerados (min 8-9) + 5 duplicatas entre fases + 1 inválida",
        msgs2,
        late_tolerated=len(tol2),
    )

    # ---------------- fase 3
    p3c = _traffic(rng, "c", range(14, 16), per_minute)
    tol3 = [
        Click(
            f"lt3-{i:03d}",
            f"u{rng.randint(1, 40):02d}",
            rng.choices(PAGES, WEIGHTS)[0],
            T0 + timedelta(minutes=12, seconds=rng.randint(0, 59)),
        )
        for i in range(8)
    ]
    late3 = [
        Click(
            f"vl3-{i:03d}",
            f"u{rng.randint(1, 40):02d}",
            rng.choices(PAGES, WEIGHTS)[0],
            T0 + timedelta(minutes=2, seconds=rng.randint(0, 59)),
        )
        for i in range(12)
    ]
    late3 += [
        Click(
            f"vl3-1{i:02d}",
            f"u{rng.randint(1, 40):02d}",
            rng.choices(PAGES, WEIGHTS)[0],
            T0 + timedelta(minutes=10, seconds=rng.randint(0, 59)),
        )
        for i in range(6)
    ]
    p3 = _arrival_order(rng, p3c)
    msgs3 = [c.to_bytes() for c in p3] + [c.to_bytes() for c in tol3] + [c.to_bytes() for c in late3]
    rng.shuffle(msgs3)
    ph3 = Phase(
        "3: tráfego min 14-15 + 8 tolerados (min 12) + 18 MUITO atrasados (min 2 e 10 → descartados)",
        msgs3,
        late_tolerated=len(tol3),
        too_late=len(late3),
    )
    return [ph1, ph2, ph3]
