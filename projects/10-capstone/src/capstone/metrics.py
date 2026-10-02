"""Observabilidade: métricas em formato de exposição do Prometheus (textfile collector) + relatório de execução."""

from __future__ import annotations

import json
import time
from datetime import UTC, date, datetime, timedelta

from . import config
from . import lakehouse as lh


def collect(ds: date, durations: dict[str, float], status: str) -> str:
    rep = json.loads(config.ops("reports", f"{ds}.json").read_text())
    silver = lh.read(*lh.T_SILVER) if lh.exists(*lh.T_SILVER) else None
    end = datetime(ds.year, ds.month, ds.day, tzinfo=UTC) + timedelta(days=1)
    fresh = None
    if silver is not None and silver.num_rows:
        newest = max(silver.column("updated_at").to_pylist())
        fresh = (end - newest).total_seconds()
    g: list[tuple[str, str, dict, float]] = [
        (
            "capstone_gate_blocked",
            "1 se o gate de qualidade bloqueou o lote do ds",
            {},
            1.0 if rep["status"] == "blocked" else 0.0,
        ),
        ("capstone_batch_rows", "linhas lidas da bronze no ds", {"state": "read"}, rep["rows_read"]),
        ("capstone_batch_rows", "", {"state": "valid"}, rep["valid"]),
        ("capstone_batch_rows", "", {"state": "rejected"}, rep["rejected"]),
        ("capstone_reject_rate", "taxa de rejeição do lote", {}, rep["reject_rate"]),
        (
            "capstone_run_success",
            "1 se o pipeline do ds terminou sem erro (bloqueio por qualidade conta como 0)",
            {},
            1.0 if status == "success" else 0.0,
        ),
        ("capstone_last_run_timestamp_seconds", "epoch da última execução (relógio real)", {}, time.time()),
    ]
    for c in rep["checks"]:
        g.append(
            (
                "capstone_check_passed",
                "1 se o check passou",
                {"check": c["name"], "level": c["level"]},
                1.0 if c["passed"] else 0.0,
            )
        )
    if silver is not None:
        g.append(("capstone_table_rows", "linhas por tabela Delta", {"table": "silver_orders"}, silver.num_rows))
        g.append(
            (
                "capstone_delta_version",
                "versão atual da tabela Delta",
                {"table": "silver_orders"},
                lh.open_table(*lh.T_SILVER).version(),
            )
        )
    if fresh is not None:
        g.append(("capstone_data_freshness_seconds", "idade do dado mais novo da silver em relação ao fim do ds", {}, fresh))
    for step, d in durations.items():
        g.append(("capstone_step_duration_seconds", "duração de cada passo", {"step": step}, round(d, 3)))

    out, seen = [], set()
    for name, helptxt, labels, val in g:
        if name not in seen:
            seen.add(name)
            out += [f"# HELP {name} {helptxt or name}", f"# TYPE {name} gauge"]
        lab = ",".join(f'{k}="{v}"' for k, v in labels.items())
        out.append(f"{name}{{{lab}}} {val}" if lab else f"{name} {val}")
    text = "\n".join(out) + "\n"
    config.ops("metrics", "capstone.prom").write_text(text)
    return text
