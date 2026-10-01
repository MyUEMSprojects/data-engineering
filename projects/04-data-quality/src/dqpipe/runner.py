"""Executa UM lote: carrega -> valida schema -> checks -> decide (publicar/bloquear) -> grava saídas.

Decisão (gate):
  BLOQUEIA  se: schema incompatível · lote vazio · QUALQUER check de DATASET `hard` falhou ·
            fração em quarentena > `max_quarantine_rate`.
  PUBLICA   caso contrário — as linhas ruins vão para a quarentena; falhas `soft` viram avisos.

Idempotente por (dataset, partição): reexecutar sobrescreve a publicação/quarentena daquela partição.
Um lote BLOQUEADO nunca apaga a última publicação boa (consumidores continuam servidos).
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import duckdb

from . import checks as chk
from .contract import Contract


@dataclass
class RunResult:
    dataset: str
    contract_version: str
    partition: str
    decision: str  # "published" | "blocked"
    reasons: list[str] = field(default_factory=list)  # por que bloqueou
    warnings: list[str] = field(default_factory=list)  # falhas soft
    results: list[chk.CheckResult] = field(default_factory=list)
    rows_read: int = 0
    rows_published: int = 0
    rows_quarantined: int = 0
    as_of: str = ""
    paths: dict[str, str] = field(default_factory=dict)

    @property
    def published(self) -> bool:
        return self.decision == "published"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ------------------------------------------------------------------------------ utilitários
def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _copy_parquet_atomic(con: duckdb.DuckDBPyConnection, query: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".parquet.tmp")
    try:
        con.execute(f"COPY ({query}) TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        os.replace(tmp, dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


# ------------------------------------------------------------------------------ histórico
def load_history(state_dir: Path, dataset: str, exclude_partition: str) -> list[dict[str, Any]]:
    """Estatísticas dos lotes JÁ PUBLICADOS (baseline das anomalias), exceto a própria partição."""
    f = state_dir / "history.json"
    if not f.exists():
        return []
    data = json.loads(f.read_text(encoding="utf-8")).get(dataset, {})
    return [v for k, v in sorted(data.items()) if k != exclude_partition]


def save_history(state_dir: Path, dataset: str, partition: str, stats: dict[str, Any]) -> None:
    f = state_dir / "history.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    data.setdefault(dataset, {})[partition] = stats
    _atomic_write_text(f, json.dumps(data, indent=2, sort_keys=True))


# ------------------------------------------------------------------------------ carga + schema
def _load(con: duckdb.DuckDBPyConnection, csv_path: Path, contract: Contract):
    """Carrega o CSV (tudo VARCHAR) e devolve (resultado do check de schema, colunas presentes)."""
    # `_rn`: índice de linha materializado UMA vez — liga RAW <-> BATCH (para a quarentena)
    con.execute(f"CREATE TABLE {chk.RAW} AS SELECT row_number() OVER () AS _rn, * FROM "
                f"read_csv({chk.lit(csv_path.as_posix())}, all_varchar=true, header=true)")  # fmt: skip
    present = [r[0] for r in con.execute(f"DESCRIBE {chk.RAW}").fetchall() if r[0] != "_rn"]
    expected = contract.column_names
    missing = [c.name for c in contract.columns if c.required and c.name not in present]
    extra = [c for c in present if c not in expected]
    problems = []
    if missing:
        problems.append(f"colunas obrigatórias ausentes: {missing}")
    if extra and not contract.allow_extra_columns:
        problems.append(f"colunas não previstas no contrato: {extra}")
    res = chk.CheckResult("schema_matches_contract", "dataset", "schema", "hard",
                          "fail" if problems else "pass", observed=len(missing) + len(extra),
                          threshold="schema idêntico ao contrato",
                          detail="; ".join(problems) or "ok")  # fmt: skip
    return res, present, bool(missing)


def _build_typed(con: duckdb.DuckDBPyConnection, contract: Contract, present: list[str]) -> None:
    sel = ["_rn"]
    for c in contract.columns:
        if c.name in present:
            raw = f"NULLIF(TRIM({chk.q(c.name)}), '')"
            sel.append(f"TRY_CAST({raw} AS {c.type}) AS {chk.q(c.name)}")
            sel.append(f"({raw} IS NOT NULL AND TRY_CAST({raw} AS {c.type}) IS NULL)"
                       f" AS {chk.q('_castfail_' + c.name)}")  # fmt: skip
        else:  # coluna opcional ausente => NULL
            sel.append(f"CAST(NULL AS {c.type}) AS {chk.q(c.name)}")
            sel.append(f"FALSE AS {chk.q('_castfail_' + c.name)}")
    con.execute(f"CREATE TABLE {chk.BATCH} AS SELECT {', '.join(sel)} FROM {chk.RAW}")


# ------------------------------------------------------------------------------ execução
def run_batch(
    csv_path: Path | str,
    contract: Contract,
    partition: date,
    out_dir: Path | str,
    as_of: datetime | None = None,
) -> RunResult:
    csv_path, out_dir = Path(csv_path), Path(out_dir)
    as_of = as_of or datetime.now(UTC)
    part = partition.isoformat()
    state_dir = out_dir / "state"
    ds = contract.dataset
    result = RunResult(ds, contract.version, part, "blocked", as_of=as_of.isoformat())

    con = duckdb.connect(":memory:")
    try:
        schema_res, present, missing_required = _load(con, csv_path, contract)
        result.results.append(schema_res)
        result.rows_read = con.execute(f"SELECT count(*) FROM {chk.RAW}").fetchone()[0]
        if missing_required:
            result.reasons.append("schema incompatível: " + schema_res.detail)
            return _finish(result, contract, out_dir, state_dir, None, None)
        if result.rows_read == 0:
            result.reasons.append("lote vazio")
            return _finish(result, contract, out_dir, state_dir, None, None)

        _build_typed(con, contract, present)
        ctx = chk.BatchContext(con, contract, as_of, load_history(state_dir, ds, part))
        result.results += chk.run_all(ctx)

        # ---- decisão -------------------------------------------------------------------
        if schema_res.failed:
            result.reasons.append("schema: " + schema_res.detail)
        for r in result.results:
            if r.level == "dataset" and r.failed and r.type != "schema":
                (result.reasons if r.severity == "hard" else result.warnings).append(
                    f"{r.id}: {r.detail or r.observed}"
                )
            elif r.level == "row" and r.failed and r.severity == "soft":
                result.warnings.append(f"{r.id}: {r.detail}")  # soft de linha: só avisa
        reasons_sql, bad_sql = _quarantine_exprs(contract)
        result.rows_quarantined = con.execute(
            f"SELECT count(*) FROM {chk.BATCH} WHERE {bad_sql}").fetchone()[0]  # fmt: skip
        rate = result.rows_quarantined / result.rows_read
        if rate > contract.max_quarantine_rate:
            result.reasons.append(
                f"quarentena {rate:.1%} > limite {contract.max_quarantine_rate:.1%}"
            )

        if not result.reasons:
            result.decision = "published"
            result.rows_published = result.rows_read - result.rows_quarantined
        stats = _batch_stats(con, contract, result) if result.published else None
        return _finish(result, contract, out_dir, state_dir, (con, reasons_sql, bad_sql), stats)
    finally:
        con.close()


def _quarantine_exprs(contract: Contract) -> tuple[str, str]:
    """(expressão de motivos, predicado de linha ruim) — só checks de linha `hard` + casts."""
    parts = [(cid, flag) for cid, flag in chk.cast_predicates(contract).items()]
    parts += [(c.id, chk.row_predicate(c)) for c in contract.checks
              if c.level == "row" and c.severity == "hard"]  # fmt: skip
    cases = ", ".join(f"CASE WHEN {pred} THEN {chk.lit(cid)} END" for cid, pred in parts)
    reasons = f"list_filter([{cases}], x -> x IS NOT NULL)" if parts else "[]::VARCHAR[]"
    bad = " OR ".join(f"({pred})" for _, pred in parts) or "FALSE"
    return reasons, f"COALESCE({bad}, FALSE)"


def _batch_stats(con, contract: Contract, result: RunResult) -> dict[str, Any]:
    """Estatísticas do lote PUBLICADO — baseline para as anomalias dos próximos lotes."""
    stats: dict[str, Any] = {"rows": result.rows_read, "published_at": result.as_of}
    for c in contract.checks:
        if c.type == "anomaly_mean":
            col = c.params["column"]
            stats[f"mean_{col}"] = con.execute(
                f"SELECT avg({chk.q(col)}) FROM {chk.BATCH}").fetchone()[0]  # fmt: skip
    return stats


def _finish(result, contract, out_dir: Path, state_dir: Path, ctx_sql, stats) -> RunResult:
    ds, part = contract.dataset, result.partition
    if ctx_sql is not None:
        con, reasons_sql, bad_sql = ctx_sql
        cols = ", ".join(chk.q(c.name) for c in contract.columns)
        if result.published:
            dest = out_dir / "publish" / ds / f"dt={part}" / "part.parquet"
            _copy_parquet_atomic(
                con, f"SELECT {cols} FROM {chk.BATCH} WHERE NOT ({bad_sql})", dest)  # fmt: skip
            result.paths["publish"] = str(dest)
        if result.rows_quarantined:
            qdest = out_dir / "quarantine" / ds / f"dt={part}" / "rejected.parquet"
            # linhas ORIGINAIS (tudo texto, como vieram) + a lista de checks que reprovaram cada uma
            query = (
                f"SELECT r.* EXCLUDE (_rn), b._dq_reasons FROM {chk.RAW} r JOIN "
                f"(SELECT _rn, {reasons_sql} AS _dq_reasons FROM {chk.BATCH} WHERE {bad_sql}) b "
                "USING (_rn) ORDER BY r._rn"
            )
            _copy_parquet_atomic(con, query, qdest)
            result.paths["quarantine"] = str(qdest)
    if stats is not None:
        save_history(state_dir, ds, part, stats)

    report_dir = out_dir / "reports" / ds / f"dt={part}"
    _atomic_write_text(
        report_dir / "report.json", json.dumps(result.to_dict(), indent=2, default=str)
    )
    _atomic_write_text(report_dir / "report.md", render_markdown(result))
    result.paths["report"] = str(report_dir / "report.md")

    from .metrics import render_metrics

    _atomic_write_text(out_dir / "metrics" / "dq.prom", render_metrics(result, contract))
    return result


def render_markdown(r: RunResult) -> str:
    icon = {"pass": "✅", "fail": "❌", "skipped": "⏭️"}
    head = "🟢 PUBLICADO" if r.published else "🔴 BLOQUEADO"
    lines = [
        f"# DQ — `{r.dataset}` v{r.contract_version} · partição {r.partition}: {head}", "",
        f"- linhas lidas: **{r.rows_read}** · publicadas: **{r.rows_published}** · "
        f"quarentena: **{r.rows_quarantined}**", f"- as-of: `{r.as_of}`", "",
    ]  # fmt: skip
    if r.reasons:
        lines += ["## Motivos do bloqueio", *[f"- {x}" for x in r.reasons], ""]
    if r.warnings:
        lines += ["## Avisos (soft)", *[f"- {x}" for x in r.warnings], ""]
    lines += ["## Checks", "", "| | check | nível | sev. | observado | limite | detalhe |",
              "|---|---|---|---|---|---|---|"]  # fmt: skip
    for c in r.results:
        lines.append(f"| {icon[c.status]} | `{c.id}` | {c.level} | {c.severity} | {c.observed} "
                     f"| {c.threshold} | {c.detail} |")  # fmt: skip
    return "\n".join(lines) + "\n"
