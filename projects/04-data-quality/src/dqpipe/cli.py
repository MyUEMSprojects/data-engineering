"""CLI: `synth` (gera lote de teste), `run` (valida/publica), `demo` (cenários), `exporter`."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

from .contract import load_contract
from .runner import run_batch
from .synth import SCENARIOS, generate_batch, write_batch

DEFAULT_CONTRACT = Path("contracts/orders.yaml")


def _as_of_for(day: date) -> datetime:
    """No demo, o pipeline roda às 06:00 UTC do dia SEGUINTE à partição (como um job diário)."""
    return datetime.combine(day + timedelta(days=1), time(6, 0), tzinfo=UTC)


def _print_summary(r) -> None:
    flag = "🟢 PUBLICADO" if r.published else "🔴 BLOQUEADO"
    print(f"{flag}  {r.dataset} dt={r.partition}  lidas={r.rows_read} publicadas={r.rows_published}"
          f" quarentena={r.rows_quarantined}")  # fmt: skip
    for x in r.reasons:
        print(f"   ✖ {x}")
    for x in r.warnings:
        print(f"   ⚠ {x}")


def cmd_synth(a) -> int:
    path = write_batch(a.out, generate_batch(date.fromisoformat(a.day), a.scenario))
    print(f"lote '{a.scenario}' de {a.day} gravado em {path}")
    return 0


def cmd_run(a) -> int:
    contract = load_contract(a.contract)
    as_of = datetime.fromisoformat(a.as_of) if a.as_of else None
    r = run_batch(a.input, contract, date.fromisoformat(a.partition), a.out, as_of)
    _print_summary(r)
    print(f"relatório: {r.paths.get('report')}")
    return 0 if r.published else 2  # 2 = bloqueado (o orquestrador marca a task como falha)


def cmd_demo(a) -> int:
    contract = load_contract(a.contract)
    out = Path(a.out)
    start = date(2024, 1, 1)
    print("== Construindo histórico: 10 lotes saudáveis ==")
    for i in range(10):
        d = start + timedelta(days=i)
        src = write_batch(out / "inbox" / f"orders_{d}.csv", generate_batch(d, "clean"))
        r = run_batch(src, contract, d, out, _as_of_for(d))
        print(f"  {d}  {'publicado' if r.published else 'BLOQUEADO'}  linhas={r.rows_read}")
    print("\n== Cenários de falha (cada um em um dia novo) ==")
    for i, scenario in enumerate(s for s in SCENARIOS if s != "clean"):
        d = start + timedelta(days=10 + i)
        src = write_batch(out / "inbox" / f"orders_{d}.csv", generate_batch(d, scenario))
        print(f"\n--- {d}  cenário: {scenario} ---")
        _print_summary(run_batch(src, contract, d, out, _as_of_for(d)))
    return 0


def cmd_exporter(a) -> int:
    from .exporter import serve

    serve(Path(a.metrics), port=a.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dqpipe", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("synth", help="gera um lote sintético")
    s.add_argument("--day", required=True, help="YYYY-MM-DD")
    s.add_argument("--scenario", default="clean", choices=SCENARIOS)
    s.add_argument("--out", type=Path, required=True)
    s.set_defaults(fn=cmd_synth)

    r = sub.add_parser("run", help="valida e publica/bloqueia um lote")
    r.add_argument("--input", type=Path, required=True)
    r.add_argument(
        "--partition", required=True, help="data lógica YYYY-MM-DD (vem do orquestrador)"
    )
    r.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    r.add_argument("--out", type=Path, default=Path("out"))
    r.add_argument("--as-of", help="'agora' ISO-8601 (padrão: relógio atual UTC)")
    r.set_defaults(fn=cmd_run)

    d = sub.add_parser("demo", help="10 lotes saudáveis + 8 cenários de falha")
    d.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    d.add_argument("--out", type=Path, default=Path("out"))
    d.set_defaults(fn=cmd_demo)

    e = sub.add_parser("exporter", help="serve out/metrics/dq.prom para o Prometheus")
    e.add_argument("--metrics", default="out/metrics/dq.prom")
    e.add_argument("--port", type=int, default=9108)
    e.set_defaults(fn=cmd_exporter)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
