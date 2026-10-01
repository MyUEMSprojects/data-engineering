"""Métricas no formato de exposição do Prometheus (texto) — observabilidade dos DADOS.

Mostram o estado do ÚLTIMO lote processado de cada dataset. Os alertas (monitoring/alerts.yml)
são escritos sobre estas séries: check hard falhou · dado velho · pipeline sem rodar (dead man's switch).
"""

from __future__ import annotations

from datetime import datetime

from .contract import Contract


def _esc(v: object) -> str:
    return str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _labels(**kw: object) -> str:
    return "{" + ",".join(f'{k}="{_esc(v)}"' for k, v in kw.items()) + "}"


def render_metrics(result, contract: Contract) -> str:
    ds = contract.dataset
    out: list[str] = []

    def metric(name: str, help_: str, samples: list[tuple[str, float]]) -> None:
        out.append(f"# HELP {name} {help_}")
        out.append(f"# TYPE {name} gauge")
        out.extend(f"{name}{lbl} {val}" for lbl, val in samples)

    metric("dq_check_passed", "1 se o check passou, 0 se falhou (checks pulados não são emitidos)", [
        (_labels(dataset=ds, check=c.id, level=c.level, severity=c.severity), 0 if c.failed else 1)
        for c in result.results if c.status != "skipped"])  # fmt: skip
    metric("dq_check_observed", "valor observado pelo check (quando numérico)", [
        (_labels(dataset=ds, check=c.id), c.observed)
        for c in result.results if isinstance(c.observed, int | float)])  # fmt: skip
    metric("dq_rows", "linhas do último lote por estado", [
        (_labels(dataset=ds, state="read"), result.rows_read),
        (_labels(dataset=ds, state="published"), result.rows_published),
        (_labels(dataset=ds, state="quarantined"), result.rows_quarantined)])  # fmt: skip
    metric("dq_gate_blocked", "1 se o último lote foi BLOQUEADO pelo gate de qualidade", [
        (_labels(dataset=ds), 0 if result.published else 1)])  # fmt: skip
    metric("dq_warnings", "nº de avisos (falhas soft) no último lote", [
        (_labels(dataset=ds), len(result.warnings))])  # fmt: skip
    fresh = next(
        (c for c in result.results if c.type == "freshness" and c.observed is not None), None
    )
    if fresh is not None:
        metric("dq_data_age_seconds", "idade do dado mais recente do último lote", [
            (_labels(dataset=ds), round(float(fresh.observed) * 3600, 1))])  # fmt: skip
    metric("dq_last_run_timestamp_seconds", "epoch (s) do último run do pipeline", [
        (_labels(dataset=ds), int(datetime.fromisoformat(result.as_of).timestamp()))])  # fmt: skip
    metric("dq_contract_info", "versão e dono do contrato em vigor", [
        (_labels(dataset=ds, version=contract.version, owner=contract.owner), 1)])  # fmt: skip
    return "\n".join(out) + "\n"
