"""Bronze: o dado EXATAMENTE como chegou. Imutável, particionado por data de INGESTÃO.

O nome do arquivo carrega o hash do conteúdo (``batch-<sha>.jsonl``). Consequências desejáveis:
- reingerir o mesmo lote é um **no-op** (idempotência de graça);
- um lote diferente nunca sobrescreve outro (imutabilidade);
- é sempre possível reconstruir silver/gold **do zero** a partir daqui (reprocessamento).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

from .storage import Lake

SOURCE = "orders"


@dataclass(frozen=True)
class IngestResult:
    path: str
    created: bool
    bytes: int


def bronze_prefix(ingest_date: date | None = None) -> str:
    base = f"bronze/{SOURCE}"
    return f"{base}/ingest_date={ingest_date.isoformat()}" if ingest_date else base


def ingest(lake: Lake, data: bytes, ingest_date: date) -> IngestResult:
    digest = hashlib.sha256(data).hexdigest()[:12]
    rel = f"{bronze_prefix(ingest_date)}/batch-{digest}.jsonl"
    if lake.exists(rel):
        return IngestResult(rel, created=False, bytes=len(data))
    lake.write(rel, data)
    return IngestResult(rel, created=True, bytes=len(data))
