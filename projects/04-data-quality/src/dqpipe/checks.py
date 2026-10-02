"""Execução dos checks de qualidade sobre um lote carregado no DuckDB.

Dois níveis (ver módulo 12):
* **row**     — avalia cada linha; as ruins vão para a QUARENTENA (o resto pode ser publicado);
* **dataset** — avalia o lote inteiro (unicidade, volume, frescor, anomalias vs histórico).

Cada check devolve um `CheckResult` estruturado (observado vs limite) — nada de `assert` opaco.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import duckdb

from .anomaly import is_anomalous
from .contract import Check, Contract

BATCH = "batch"  # tabela tipada (TRY_CAST); inválidos viram NULL + flag `_castfail_<col>`
RAW = "raw_batch"  # tudo VARCHAR, exatamente como veio


def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def lit(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int | float):
        return repr(value)
    return "'" + str(value).replace("'", "''") + "'"


@dataclass
class CheckResult:
    id: str
    level: str
    type: str
    severity: str
    status: str  # "pass" | "fail" | "skipped"
    observed: float | int | None = None
    threshold: str = ""
    failed_rows: int | None = None
    detail: str = ""

    @property
    def failed(self) -> bool:
        return self.status == "fail"


@dataclass
class BatchContext:
    con: duckdb.DuckDBPyConnection
    contract: Contract
    as_of: datetime  # "agora" injetável => testes determinísticos
    history: list[dict[str, Any]] = field(default_factory=list)  # só lotes PUBLICADOS

    @property
    def n_rows(self) -> int:
        return self.con.execute(f"SELECT count(*) FROM {BATCH}").fetchone()[0]


# ----------------------------------------------------------------------------- nível LINHA
def row_predicate(check: Check) -> str:
    """SQL booleano que é TRUE quando a linha é RUIM para este check."""
    p, col = check.params, check.params.get("column")
    c = q(col) if col else ""
    if check.type == "not_null":
        return f"{c} IS NULL"
    if check.type == "range":
        parts = []
        if "min" in p:
            parts.append(f"{c} < {lit(p['min'])}")
        if "max" in p:
            parts.append(f"{c} > {lit(p['max'])}")
        return "(" + " OR ".join(parts) + ")" if parts else "FALSE"
    if check.type == "accepted_values":
        vals = ", ".join(lit(v) for v in p["values"])
        # NULL não é "valor fora do domínio" (nulos têm check próprio: not_null / null_rate_max)
        return f"({c} IS NOT NULL AND {c} NOT IN ({vals}))"
    if check.type == "regex":
        return f"({c} IS NOT NULL AND NOT regexp_matches({c}, {lit(p['pattern'])}))"
    raise ValueError(f"check de linha desconhecido: {check.type}")


def cast_predicates(contract: Contract) -> dict[str, str]:
    """Checks IMPLÍCITOS: valor presente mas não conversível ao tipo do contrato."""
    return {f"type_cast:{c.name}": f"_castfail_{c.name}" for c in contract.columns
            if c.type != "VARCHAR"}  # fmt: skip


def run_row_check(ctx: BatchContext, check: Check) -> CheckResult:
    bad = ctx.con.execute(f"SELECT count(*) FROM {BATCH} WHERE {row_predicate(check)}").fetchone()[
        0
    ]
    n = ctx.n_rows
    return CheckResult(
        check.id, check.level, check.type, check.severity,
        "fail" if bad else "pass", observed=bad, threshold="0 linhas ruins",
        failed_rows=bad, detail=f"{bad}/{n} linhas ({bad / n:.2%})" if n else "lote vazio",
    )  # fmt: skip


def run_cast_checks(ctx: BatchContext) -> list[CheckResult]:
    out = []
    for cid, flag in cast_predicates(ctx.contract).items():
        bad = ctx.con.execute(f"SELECT count(*) FROM {BATCH} WHERE {flag}").fetchone()[0]
        out.append(CheckResult(cid, "row", "type_cast", "hard", "fail" if bad else "pass",
                               observed=bad, threshold="0 linhas ruins", failed_rows=bad,
                               detail=f"{bad} valores não conversíveis"))  # fmt: skip
    return out


# -------------------------------------------------------------------------- nível DATASET
def _scalar(ctx: BatchContext, sql: str) -> Any:
    return ctx.con.execute(sql).fetchone()[0]


def _res(check: Check, passed: bool, observed, threshold: str, detail: str = "") -> CheckResult:
    return CheckResult(check.id, check.level, check.type, check.severity,
                       "pass" if passed else "fail", observed, threshold, detail=detail)  # fmt: skip


def run_dataset_check(ctx: BatchContext, check: Check) -> CheckResult:
    p, t = check.params, check.type
    if t == "unique":
        cols = ", ".join(q(c) for c in p["columns"])
        dups = _scalar(ctx, f"SELECT count(*) - count(DISTINCT ({cols})) FROM {BATCH}")
        return _res(
            check, dups == 0, dups, "0 duplicatas", f"{dups} linhas repetem a chave ({cols})"
        )

    if t == "row_count_between":
        n = ctx.n_rows
        ok = p.get("min", 0) <= n <= p.get("max", float("inf"))
        return _res(check, ok, n, f"{p.get('min')}..{p.get('max')} linhas")

    if t == "null_rate_max":
        c = q(p["column"])
        rate = _scalar(
            ctx,
            f"SELECT coalesce(avg(CASE WHEN {c} IS NULL THEN 1.0 ELSE 0.0 END), 0) FROM {BATCH}",
        )
        return _res(
            check,
            rate <= p["max"],
            round(rate, 4),
            f"<= {p['max']:.2%}",
            f"{rate:.2%} nulos em {p['column']}",
        )  # noqa: E501

    if t == "freshness":
        newest = _scalar(ctx, f"SELECT max({q(p['column'])}) FROM {BATCH}")
        if newest is None:
            return _res(check, False, None, f"<= {p['max_age_hours']}h", "sem dados")
        age_h = (ctx.as_of.replace(tzinfo=None) - newest).total_seconds() / 3600
        return _res(check, age_h <= p["max_age_hours"], round(age_h, 2),
                    f"<= {p['max_age_hours']}h", f"dado mais recente tem {age_h:.1f}h")  # fmt: skip

    if t in ("anomaly_row_count", "anomaly_mean"):
        if t == "anomaly_row_count":
            value, key = float(ctx.n_rows), "rows"
        else:
            col = p["column"]
            value = _scalar(ctx, f"SELECT avg({q(col)}) FROM {BATCH}")
            key = f"mean_{col}"
        past = [h[key] for h in ctx.history if h.get(key) is not None]
        anomalous, z = is_anomalous(value, past, p["z_max"], p["min_history"])
        if anomalous is None:
            return CheckResult(check.id, check.level, t, check.severity, "skipped", value,
                               f"|z| <= {p['z_max']}",
                               detail=f"histórico insuficiente ({len(past)}/{p['min_history']})")  # fmt: skip
        return _res(check, not anomalous, round(value, 2), f"|z| <= {p['z_max']}",
                    f"z={z:+.1f} vs {len(past)} lotes publicados")  # fmt: skip
    raise ValueError(f"check de dataset desconhecido: {t}")


def run_all(ctx: BatchContext) -> list[CheckResult]:
    results = run_cast_checks(ctx)
    for check in ctx.contract.checks:
        results.append(run_row_check(ctx, check) if check.level == "row"
                       else run_dataset_check(ctx, check))  # fmt: skip
    return results
