"""Camada lakehouse: tabelas Delta (ACID, schema enforcement, time travel) com `deltalake` (delta-rs)."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from . import config

BRONZE_SCHEMA = pa.schema(
    [
        ("raw", pa.string()),
        ("_ingest_ds", pa.string()),
        ("_source_file", pa.string()),
        ("_line_no", pa.int32()),
        ("_ingested_at", pa.timestamp("us", tz="UTC")),
    ]
)
SILVER_SCHEMA = pa.schema(
    [
        ("order_id", pa.string()),
        ("customer_id", pa.string()),
        ("country", pa.string()),
        ("category", pa.string()),
        ("amount", pa.decimal128(12, 2)),
        ("status", pa.string()),
        ("order_date", pa.date32()),
        ("updated_at", pa.timestamp("us", tz="UTC")),
        ("_ingest_ds", pa.string()),
        ("_source_file", pa.string()),
    ]
)
REJECT_SCHEMA = pa.schema(
    [
        ("ds", pa.string()),
        ("source_file", pa.string()),
        ("line_no", pa.int32()),
        ("reason", pa.string()),
        ("raw", pa.string()),
    ]
)
T_BRONZE, T_SILVER, T_QUAR = ("bronze/orders",), ("silver/orders",), ("quarantine/orders",)


def path(*t: str) -> str:
    return config.table(*t)


def exists(*t: str) -> bool:
    return DeltaTable.is_deltatable(path(*t))


def open_table(*t: str, version: int | None = None) -> DeltaTable:
    return DeltaTable(path(*t), version=version)


def read(*t: str, version: int | None = None) -> pa.Table:
    return open_table(*t, version=version).to_pyarrow_table()


def overwrite_partition(t: tuple[str, ...], table: pa.Table, ds: str, col: str) -> None:
    """Reescreve SÓ a partição do dia (idempotente): `replaceWhere` do Delta."""
    write_deltalake(path(*t), table, mode="overwrite", partition_by=[col], predicate=f"{col} = '{ds}'")


def merge_silver(batch: pa.Table) -> dict:
    """MERGE: insere novos e atualiza SÓ se o evento é mais NOVO (updated_at maior) — reentrega e atraso são inofensivos."""
    if not exists(*T_SILVER):
        write_deltalake(path(*T_SILVER), batch)
        return {"num_target_rows_inserted": batch.num_rows, "num_target_rows_updated": 0}
    cols = SILVER_SCHEMA.names
    return (
        open_table(*T_SILVER)
        .merge(batch, "t.order_id = s.order_id", source_alias="s", target_alias="t")
        .when_matched_update({c: f"s.{c}" for c in cols}, predicate="s.updated_at > t.updated_at")
        .when_not_matched_insert({c: f"s.{c}" for c in cols})
        .execute()
    )


def now_utc() -> datetime:
    return datetime.now(UTC)


def lake_exists() -> bool:
    return os.path.isdir(config.LAKE)
