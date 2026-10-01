"""Carrega e VALIDA o contrato de dados (YAML) — um contrato inválido falha cedo e alto."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SEVERITIES = {"hard", "soft"}
LEVELS = {"row", "dataset"}
CHECK_TYPES = {
    "row": {"not_null", "range", "accepted_values", "regex"},
    "dataset": {
        "unique", "row_count_between", "freshness", "null_rate_max",
        "anomaly_row_count", "anomaly_mean",
    },
}  # fmt: skip
DUCKDB_TYPES = {"VARCHAR", "DOUBLE", "BIGINT", "INTEGER", "TIMESTAMP", "DATE", "BOOLEAN"}


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    required: bool = True


@dataclass(frozen=True)
class Check:
    id: str
    level: str
    type: str
    severity: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Contract:
    dataset: str
    version: str
    owner: str
    partition_column: str
    columns: list[Column]
    allow_extra_columns: bool
    max_quarantine_rate: float
    checks: list[Check]
    sla: dict[str, Any]

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]


def parse_contract(doc: dict[str, Any]) -> Contract:
    try:
        schema = doc["schema"]
        columns = [Column(c["name"], c["type"].upper(), c.get("required", True))
                   for c in schema["columns"]]  # fmt: skip
    except (KeyError, TypeError, AttributeError) as exc:
        raise ContractError(f"seção 'schema' inválida: {exc!r}") from exc
    for c in columns:
        if c.type not in DUCKDB_TYPES:
            raise ContractError(f"tipo não suportado na coluna {c.name}: {c.type}")
    names = [c.name for c in columns]
    if len(set(names)) != len(names):
        raise ContractError("colunas duplicadas no schema")
    part = doc.get("partition_column")
    if part not in names:
        raise ContractError(f"partition_column {part!r} não existe no schema")

    checks, seen = [], set()
    for raw in doc.get("checks", []):
        raw = dict(raw)
        cid, level, ctype = raw.pop("id", None), raw.pop("level", None), raw.pop("type", None)
        severity = raw.pop("severity", "hard")
        if not cid or cid in seen:
            raise ContractError(f"id de check ausente ou duplicado: {cid!r}")
        if level not in LEVELS:
            raise ContractError(f"{cid}: level deve ser um de {sorted(LEVELS)}")
        if ctype not in CHECK_TYPES[level]:
            raise ContractError(f"{cid}: tipo {ctype!r} inválido para level {level!r}")
        if severity not in SEVERITIES:
            raise ContractError(f"{cid}: severity deve ser um de {sorted(SEVERITIES)}")
        for col in [raw.get("column"), *raw.get("columns", [])]:
            if col is not None and col not in names:
                raise ContractError(f"{cid}: coluna {col!r} não existe no schema")
        seen.add(cid)
        checks.append(Check(cid, level, ctype, severity, raw))

    mqr = float(doc.get("max_quarantine_rate", 0.0))
    if not 0 <= mqr <= 1:
        raise ContractError("max_quarantine_rate deve estar entre 0 e 1")
    return Contract(
        dataset=doc["dataset"], version=str(doc.get("version", "0.0.0")),
        owner=doc.get("owner", ""), partition_column=part, columns=columns,
        allow_extra_columns=bool(schema.get("allow_extra_columns", False)),
        max_quarantine_rate=mqr, checks=checks, sla=doc.get("sla", {}),
    )  # fmt: skip


def load_contract(path: Path | str) -> Contract:
    with open(path, encoding="utf-8") as fh:
        return parse_contract(yaml.safe_load(fh))
