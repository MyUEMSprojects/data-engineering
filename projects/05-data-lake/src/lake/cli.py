from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from .bronze import ingest
from .compaction import compact_silver
from .gold import build_gold, connect
from .inventory import inventory
from .reader import pruning_report
from .silver import build_silver
from .storage import Lake, open_lake
from .synth import generate_batch


def _date(s: str) -> date:
    return date.fromisoformat(s)


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return str(n)


def _do_ingest(lake: Lake, day: date, file: str | None, n_new: int) -> None:
    data = Path(file).read_bytes() if file else generate_batch(day, n_new=n_new)
    r = ingest(lake, data, day)
    print(
        f"bronze  {'NOVO ' if r.created else 'JÁ EXISTIA (no-op)'} {r.path} ({_fmt_bytes(r.bytes)})"
    )


def _do_silver(lake: Lake, rows_per_file: int) -> None:
    r = build_silver(lake, rows_per_file=rows_per_file)
    print(
        f"silver  bronze={r.bronze_files} arquivos · linhas={r.lines_read} · válidas={r.valid} · "
        f"rejeitadas={r.rejected} · duplicatas/atualizações colapsadas={r.duplicates_removed} · "
        f"pedidos={r.orders}"
    )
    print(
        f"        partições: {r.partitions_written} escritas · {r.partitions_unchanged} inalteradas"
    )
    if r.reject_reasons:
        print("        rejeições:", dict(sorted(r.reject_reasons.items())))


def _do_gold(lake: Lake) -> None:
    for g in build_gold(lake):
        print(
            f"gold    {g.table:<15} {g.rows:>6} linhas  {'escrita' if g.written else 'inalterada'}"
        )


def cmd_inventory(lake: Lake) -> None:
    print(f"{'camada':<11}{'tabela':<17}{'arquivos':>9}{'tamanho':>11}{'linhas':>9}{'dirs':>6}")
    for t in inventory(lake):
        rows = "-" if t.rows is None else str(t.rows)
        print(
            f"{t.layer:<11}{t.table:<17}{t.files:>9}{_fmt_bytes(t.bytes):>11}{rows:>9}{t.partitions:>6}"
        )


def cmd_demo(lake: Lake, days: int, n_new: int) -> None:
    start = date(2024, 1, 1)
    for i in range(days):
        d = start + timedelta(days=i)
        print(f"\n=== dia de ingestão {d} ===")
        _do_ingest(lake, d, None, n_new)
        _do_silver(lake, 1_000_000)
    print("\n=== REEXECUÇÃO do último dia (idempotência: nada deve mudar) ===")
    _do_ingest(lake, start + timedelta(days=days - 1), None, n_new)
    _do_silver(lake, 1_000_000)
    print("\n=== gold ===")
    _do_gold(lake)
    print("\n=== inventário ===")
    cmd_inventory(lake)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="lake", description="Mini data lake: bronze → silver → gold")
    p.add_argument("--uri", help="file://./lake-data (padrão) ou s3://bucket  [env LAKE_URI]")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="cria o diretório/bucket do lake")

    s = sub.add_parser("ingest", help="grava um lote na bronze (gerado ou de --file)")
    s.add_argument("--date", type=_date, required=True)
    s.add_argument("--file")
    s.add_argument("--n-new", type=int, default=300)

    s = sub.add_parser("silver", help="bronze → silver (limpa, deduplica, particiona)")
    s.add_argument("--rows-per-file", type=int, default=1_000_000)

    sub.add_parser("gold", help="silver → gold (tabelas analíticas)")

    s = sub.add_parser("run", help="ingest + silver + gold de um dia")
    s.add_argument("--date", type=_date, required=True)
    s.add_argument("--n-new", type=int, default=300)

    s = sub.add_parser("demo", help="N dias de ingestão + reexecução + gold + inventário")
    s.add_argument("--days", type=int, default=7)
    s.add_argument("--n-new", type=int, default=300)

    sub.add_parser("inventory", help="arquivos/tamanho/linhas por tabela (só metadados)")

    s = sub.add_parser("prune", help="mostra o partition pruning de um filtro por data")
    s.add_argument("--from", dest="start", type=_date)
    s.add_argument("--to", dest="end", type=_date)

    s = sub.add_parser("compact", help="junta arquivos pequenos da silver")
    s.add_argument("--target-rows-per-file", type=int, default=1_000_000)

    s = sub.add_parser("query", help="SQL (DuckDB) sobre silver_orders / gold")
    s.add_argument("sql")

    a = p.parse_args(argv)
    lake = open_lake(a.uri)

    if a.cmd == "init":
        lake.init()
        print(f"lake pronto em {lake.root}")
    elif a.cmd == "ingest":
        lake.init()
        _do_ingest(lake, a.date, a.file, a.n_new)
    elif a.cmd == "silver":
        _do_silver(lake, a.rows_per_file)
    elif a.cmd == "gold":
        _do_gold(lake)
    elif a.cmd == "run":
        lake.init()
        _do_ingest(lake, a.date, None, a.n_new)
        _do_silver(lake, 1_000_000)
        _do_gold(lake)
    elif a.cmd == "demo":
        lake.init()
        cmd_demo(lake, a.days, a.n_new)
    elif a.cmd == "inventory":
        cmd_inventory(lake)
    elif a.cmd == "prune":
        r = pruning_report(lake, a.start, a.end)
        print(
            f"arquivos totais={r.files_total} · lidos={r.files_scanned} · "
            f"PULADOS={r.files_skipped} · linhas retornadas={r.rows_returned}"
        )
    elif a.cmd == "compact":
        r = compact_silver(lake, target_rows_per_file=a.target_rows_per_file)
        print(
            f"compaction: {r.partitions} partições · arquivos {r.files_before} → {r.files_after} "
            f"· {r.rows} linhas (inalteradas)"
        )
    elif a.cmd == "query":
        con = connect(lake)
        for name in ("daily_revenue", "customer_value", "status_funnel"):
            con.register(name, lake.read_parquet(_first(lake, f"gold/{name}")))
        con.sql(a.sql).show(max_rows=40, max_width=140)
    return 0


def _first(lake: Lake, prefix: str) -> str:
    files = [f.path for f in lake.list_files(prefix) if f.path.endswith(".parquet")]
    if not files:
        raise SystemExit(f"{prefix} vazio — rode `gold` antes")
    return files[0]


if __name__ == "__main__":
    sys.exit(main())
