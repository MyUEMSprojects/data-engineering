from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date, timedelta

from . import config, metrics, steps
from . import lakehouse as lh
from .quality import parse_line
from .synth import generate_extract


def _d(s: str) -> date:
    return date.fromisoformat(s)


def run_day(ds: date, scenario: str = "clean", *, quiet: bool = False) -> int:
    """ingest → gate → silver → gold → observe. Código de saída: 0 ok · 2 bloqueado pelo gate."""
    say = (lambda *_: None) if quiet else print
    durations: dict[str, float] = {}
    r, durations["ingest"] = steps.timed(steps.ingest, ds, scenario)
    say(f"  ingest   {r['rows']} linhas → raw ({'novo' if r['raw_created'] else 'já existia'}) + bronze")
    g, durations["gate"] = steps.timed(steps.gate, ds)
    say(
        f"  gate     lidas={g.rows_read} válidas={len(g.valid)} rejeitadas={len(g.rejects)} ({g.reject_rate:.1%}) → "
        f"{'🔴 BLOQUEADO' if g.blocked else '🟢 aprovado'}"
    )
    for c in g.checks:
        if not c.passed and not c.skipped:
            say(f"           {'✖' if c.level == 'hard' else '⚠'} {c.name}: {c.detail}")
    status = "success"
    if g.blocked:
        status = "blocked"
    else:
        s, durations["silver"] = steps.timed(steps.silver, ds)
        say(f"  silver   MERGE: +{s['inserted']} novos · {s['updated']} atualizados (de {s['batch_orders']} pedidos do lote)")
        o, durations["gold"] = steps.timed(steps.gold)
        say(f"  gold     {o}")
    metrics.collect(ds, durations, status)
    config.ops("runs", f"{ds}.json").write_text(
        json.dumps({"ds": ds.isoformat(), "scenario": scenario, "status": status, "durations": durations})
    )
    return 2 if status == "blocked" else 0


def expected_silver(published: list[tuple[date, str]]) -> dict[str, tuple]:
    """Gabarito independente (Python puro): evento de maior updated_at por pedido, só dos dias publicados."""
    best: dict[str, tuple] = {}
    for ds, sc in published:
        for n, line in enumerate(generate_extract(ds, sc, seed=config.SEED).decode().split("\n")):
            rec, _ = parse_line(line) if line.strip() else (None, None)
            if rec and (rec["order_id"] not in best or (rec["updated_at"], n) > best[rec["order_id"]][0]):
                best[rec["order_id"]] = ((rec["updated_at"], n), rec)
    return {k: (v[1]["status"], str(v[1]["amount"])) for k, v in best.items()}


def cmd_demo(_a) -> int:
    shutil.rmtree(config.LAKE, ignore_errors=True)
    days = [("clean"), ("clean"), ("dirty"), ("heavy_dirty"), ("clean")]
    start, published, codes = date(2024, 3, 1), [], []
    for i, sc in enumerate(days):
        ds = start + timedelta(days=i)
        print(f"\n=== {ds}  cenário: {sc} ===")
        code = run_day(ds, sc)
        codes.append(code)
        if code == 0:
            published.append((ds, sc))
    print("\n=== reexecução do último dia (idempotência) ===")
    v_before = lh.open_table(*lh.T_SILVER).version()
    rows_before = lh.read(*lh.T_SILVER).num_rows
    run_day(start + timedelta(days=4), "clean")
    s = lh.open_table(*lh.T_SILVER)
    print(
        f"  silver: versão {v_before} → {s.version()} (MERGE sem mudanças não altera as linhas: {rows_before} → {lh.read(*lh.T_SILVER).num_rows})"
    )

    print("\n=== lakehouse: histórico (time travel) ===")
    hist = lh.open_table(*lh.T_SILVER).history()
    for h in reversed(hist[:6]):
        print(
            f"  v{h['version']:<2} {h['operation']:<6} {h.get('operationMetrics', {}).get('num_target_rows_inserted', h.get('operationMetrics', {}).get('num_added_rows', ''))}"
        )
    n_by_v = {v: lh.read(*lh.T_SILVER, version=v).num_rows for v in range(0, lh.open_table(*lh.T_SILVER).version() + 1)}
    print(f"  linhas por versão: {n_by_v}")

    print("\n=== rollback: restore da silver para a versão anterior ao último MERGE com mudanças ===")
    dt = lh.open_table(*lh.T_SILVER)
    bad_version = dt.version()  # supomos que o ÚLTIMO MERGE foi um deploy ruim
    target = bad_version - 1
    dt.restore(target)
    after_restore = lh.read(*lh.T_SILVER).num_rows
    print(f"  restore → v{target}: {after_restore} linhas (antes do restore: {n_by_v[bad_version]})")
    run_day(start + timedelta(days=4), "clean", quiet=True)  # reaplicar o dia corrige o estado
    final = lh.read(*lh.T_SILVER)

    exp = expected_silver(published)
    got = {r["order_id"]: (r["status"], str(r["amount"])) for r in final.to_pylist()}
    gold = lh.read("gold", "daily_revenue")
    exp_rev = sum(float(amt) for (st, amt) in exp.values() if st != "canceled")
    got_rev = float(sum(gold.column("revenue").to_pylist()))
    quar = lh.read(*lh.T_QUAR)
    q_days = sorted(set(quar.column("ds").to_pylist()))
    checks = [
        ("exit codes por dia = [0,0,0,2,0] (dia 4 bloqueado)", codes == [0, 0, 0, 2, 0]),
        ("silver == gabarito independente (todos os pedidos, status e valor)", got == exp),
        (
            "nenhuma linha da silver veio do arquivo do dia BLOQUEADO",
            all("ds=2024-03-04" not in f for f in final.column("_source_file").to_pylist()),
        ),
        ("gold.daily_revenue soma == receita esperada (sem cancelados)", abs(got_rev - exp_rev) < 0.05),
        ("quarentena tem os dias 03 e 04 (dirty e heavy_dirty)", q_days == ["2024-03-03", "2024-03-04"]),
        ("reexecução não alterou as linhas da silver", rows_before == lh.read(*lh.T_SILVER).num_rows),
        ("restore voltou a silver a um estado anterior (menos linhas)", after_restore < rows_before),
        ("reaplicar o dia restaurou a silver ao gabarito", got == exp),
    ]
    print("\n=== verificações ===")
    for label, ok in checks:
        print(f"  {'✔' if ok else '✖'} {label}")
    print(f"\nmétricas Prometheus: {config.ops('metrics', 'capstone.prom')}")
    return 0 if all(ok for _, ok in checks) else 1


def cmd_ops(a) -> int:
    t = tuple(a.table.split("/"))
    dt = lh.open_table(*t)
    if a.action == "history":
        for h in reversed(dt.history()):
            print(h["version"], h["operation"], h.get("operationMetrics", {}))
    elif a.action == "version":
        print(lh.read(*t, version=a.version).num_rows, "linhas na versão", a.version)
    elif a.action == "optimize":
        print(dt.optimize.compact())
    elif a.action == "vacuum":
        print(dt.vacuum(retention_hours=0, dry_run=True, enforce_retention_duration=False))
    elif a.action == "restore":
        dt.restore(a.version)
        print("restaurada para", a.version)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="capstone")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("ingest", "gate", "silver", "observe", "run"):
        s = sub.add_parser(name)
        s.add_argument("--ds", type=_d, required=True)
        s.add_argument("--scenario", default="clean", choices=["clean", "dirty", "heavy_dirty"])
    sub.add_parser("gold")
    sub.add_parser("demo")
    sub.add_parser("serve-metrics")
    o = sub.add_parser("ops")
    o.add_argument("action", choices=["history", "version", "optimize", "vacuum", "restore"])
    o.add_argument("--table", default="silver/orders")
    o.add_argument("--version", type=int)
    a = p.parse_args(argv)
    if a.cmd == "run":
        return run_day(a.ds, a.scenario)
    if a.cmd == "ingest":
        print(steps.ingest(a.ds, a.scenario))
    elif a.cmd == "gate":
        g = steps.gate(a.ds)
        print("BLOQUEADO" if g.blocked else "aprovado", [c.name for c in g.checks if not c.passed])
        return 2 if g.blocked else 0
    elif a.cmd == "silver":
        print(steps.silver(a.ds))
    elif a.cmd == "gold":
        print(steps.gold())
    elif a.cmd == "observe":
        metrics.collect(a.ds, {}, "success")
    elif a.cmd == "demo":
        return cmd_demo(a)
    elif a.cmd == "serve-metrics":
        serve_metrics()
    elif a.cmd == "ops":
        return cmd_ops(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())


def serve_metrics(port: int = 9109) -> None:
    """Serve o arquivo de métricas em /metrics (padrão 'textfile'): o Prometheus faz o scrape."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            f = config.ops("metrics", "capstone.prom")
            if self.path != "/metrics" or not f.exists():
                self.send_response(404)
                self.end_headers()
                return
            body = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    HTTPServer(("0.0.0.0", port), H).serve_forever()  # noqa: S104 — dentro da rede do Compose
