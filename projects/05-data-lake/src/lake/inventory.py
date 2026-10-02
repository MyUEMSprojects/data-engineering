"""Inventário do lake lido só dos METADADOS (rodapé do Parquet) — sem varrer os dados."""

from __future__ import annotations

from dataclasses import dataclass

from .storage import Lake


@dataclass(frozen=True)
class TableInventory:
    layer: str
    table: str
    files: int
    bytes: int
    rows: int | None  # None p/ JSONL (não há rodapé; contar exigiria ler)
    partitions: int


def inventory(lake: Lake) -> list[TableInventory]:
    groups: dict[tuple[str, str], list] = {}
    for f in lake.list_files():
        parts = f.path.split("/")
        if len(parts) >= 3:
            groups.setdefault((parts[0], parts[1]), []).append(f)
    out = []
    for (layer, table), files in sorted(groups.items()):
        parquet = [f for f in files if f.path.endswith(".parquet")]
        rows = sum(lake.parquet_metadata(f.path).num_rows for f in parquet) if parquet else None
        partitions = len({f.path.rsplit("/", 1)[0] for f in files})
        out.append(
            TableInventory(layer, table, len(files), sum(f.size for f in files), rows, partitions)
        )
    return out
