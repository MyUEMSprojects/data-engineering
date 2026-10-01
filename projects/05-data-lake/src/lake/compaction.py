"""Problema dos arquivos pequenos e sua correção (compaction).

Muitos arquivos minúsculos = muitas requisições ao object storage + muito metadado para o engine.
`build_silver(rows_per_file=…)` permite PRODUZIR o problema (para estudo); `compact_silver` o resolve
reescrevendo cada partição em poucos arquivos grandes — sem alterar nenhuma linha.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pyarrow as pa

from .publish import publish_dir
from .silver import silver_dir
from .storage import Lake


@dataclass(frozen=True)
class CompactionReport:
    partitions: int
    files_before: int
    files_after: int
    rows: int


def _partitions(lake: Lake) -> dict[date, list[str]]:
    parts: dict[date, list[str]] = {}
    for f in lake.list_files(silver_dir()):
        if f.path.endswith(".parquet"):
            d = date.fromisoformat(f.path.split("order_date=")[1].split("/")[0])
            parts.setdefault(d, []).append(f.path)
    return parts


def compact_silver(lake: Lake, *, target_rows_per_file: int = 1_000_000) -> CompactionReport:
    parts = _partitions(lake)
    before = sum(len(v) for v in parts.values())
    rows = 0
    for d, files in parts.items():
        table = pa.concat_tables([lake.read_parquet(p) for p in sorted(files)])
        rows += table.num_rows
        publish_dir(
            lake, silver_dir(d), table, sort_by="order_id", rows_per_file=target_rows_per_file
        )
    after = sum(len(v) for v in _partitions(lake).values())
    return CompactionReport(len(parts), before, after, rows)
