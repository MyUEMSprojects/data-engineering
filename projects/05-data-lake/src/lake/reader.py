"""Leitura da silver como dataset particionado (Hive style) + relatório de *partition pruning*."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pyarrow as pa
import pyarrow.dataset as ds

from .silver import silver_dir
from .storage import Lake

PARTITIONING = ds.partitioning(pa.schema([("order_date", pa.date32())]), flavor="hive")


def silver_dataset(lake: Lake) -> ds.Dataset:
    return ds.dataset(
        lake.abs(silver_dir()),
        format="parquet",
        partitioning=PARTITIONING,
        filesystem=lake.fs,
    )


def read_silver(lake: Lake, start: date | None = None, end: date | None = None) -> pa.Table:
    """Lê a silver; o filtro em ``order_date`` poda partições (não abre os outros arquivos)."""
    return silver_dataset(lake).to_table(filter=_date_filter(start, end))


def _date_filter(start: date | None, end: date | None):
    expr = None
    if start:
        expr = ds.field("order_date") >= start
    if end:
        e = ds.field("order_date") <= end
        expr = e if expr is None else expr & e
    return expr


@dataclass(frozen=True)
class PruningReport:
    files_total: int
    files_scanned: int
    rows_returned: int

    @property
    def files_skipped(self) -> int:
        return self.files_total - self.files_scanned


def pruning_report(lake: Lake, start: date | None, end: date | None) -> PruningReport:
    dataset = silver_dataset(lake)
    total = sum(1 for _ in dataset.get_fragments())
    expr = _date_filter(start, end)
    scanned = sum(1 for _ in dataset.get_fragments(filter=expr))
    rows = dataset.count_rows(filter=expr)
    return PruningReport(total, scanned, rows)
