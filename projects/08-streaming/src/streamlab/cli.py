from __future__ import annotations

import argparse
import os
import shutil
import sys
import time

from confluent_kafka.admin import AdminClient, NewTopic

from . import db
from .events import build_scenario
from .reference import expected_results

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
PG_DSN = os.environ.get("PG_DSN", "postgresql://de:de@localhost:5432/analytics")
TOPIC = os.environ.get("STREAM_TOPIC", "clicks")
CHECKPOINTS = os.environ.get("CHECKPOINT_DIR", "/data/checkpoints")


def _spark():
    from pyspark.sql import SparkSession

    s = (
        SparkSession.builder.appName("streamlab")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    s.sparkContext.setLogLevel("ERROR")
    return s


def reset_all() -> None:
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP})
    if TOPIC in admin.list_topics(timeout=10).topics:
        for f in admin.delete_topics([TOPIC], operation_timeout=30).values():
            f.result()
        t0 = time.time()
        while TOPIC in admin.list_topics(timeout=10).topics and time.time() - t0 < 30:
            time.sleep(0.5)
    for f in admin.create_topics([NewTopic(TOPIC, num_partitions=3, replication_factor=1)]).values():
        f.result()
    shutil.rmtree(CHECKPOINTS, ignore_errors=True)
    conn = db.connect(PG_DSN)
    db.reset(conn)
    conn.close()


def _fmt(ts) -> str:
    return ts.strftime("%H:%M")


def cmd_demo(_a) -> None:
    from .job import run_once
    from .producer import produce_phase

    phases = build_scenario()
    exp = expected_results(phases)
    print("== ambiente limpo ==")
    reset_all()
    spark = _spark()
    total_dropped = 0
    for i, ph in enumerate(phases, 1):
        print(f"\n== FASE {ph.name} ==")
        n = produce_phase(BOOTSTRAP, TOPIC, ph)
        rep = run_once(spark, BOOTSTRAP, TOPIC, PG_DSN, CHECKPOINTS)
        total_dropped += rep.dropped_late
        wm_before = exp.watermarks[i - 1]
        print(
            f"   produzidas={n} · micro-lotes={rep.batches} · linhas lidas={rep.input_rows} · "
            f"descartadas por atraso (Spark)={rep.dropped_late} (esperado nesta fase: {ph.too_late})"
        )
        print(
            f"   watermark no início da fase: {_fmt(wm_before) if wm_before else '—'} · "
            f"watermarks reportados: {[w[11:19] for w in rep.watermarks]}"
        )
        print(f"   lotes aplicados no destino: {rep.applied} · reexecuções absorvidas: {rep.skipped}")

    print("\n== REEXECUÇÃO sem dados novos (retoma do checkpoint; nada deve mudar) ==")
    conn = db.connect(PG_DSN)
    before = db.fetch_windows(conn)
    rep = run_once(spark, BOOTSTRAP, TOPIC, PG_DSN, CHECKPOINTS)
    after = db.fetch_windows(conn)
    print(f"   linhas lidas={rep.input_rows} · janelas iguais antes/depois: {before == after}")

    got = db.fetch_windows(conn)
    rejects = db.count(conn, "stream_rejects")
    conn.close()
    exp_views = sum(v for v, _ in exp.windows.values())
    got_views = sum(v for v, _ in got.values())
    print("\n== VERIFICAÇÃO contra a implementação de referência (Python puro) ==")
    checks = [
        ("mesmas janelas (chaves)", set(got) == set(exp.windows)),
        ("mesmas contagens de views e usuários distintos em TODAS as janelas", got == exp.windows),
        (f"total de views = {exp_views}", got_views == exp_views),
        (
            f"eventos muito atrasados descartados pelo watermark = {exp.dropped_late}",
            total_dropped == exp.dropped_late,
        ),
        (f"mensagens inválidas guardadas em stream_rejects = {exp.rejects}", rejects == exp.rejects),
        ("reexecução sem dados novos não alterou o resultado", before == after),
    ]
    for label, ok in checks:
        print(f"   {'✔' if ok else '✖'} {label}")
    print(f"   (duplicatas removidas: {exp.duplicates})")
    sys.exit(0 if all(ok for _, ok in checks) else 1)


def cmd_report(_a) -> None:
    conn = db.connect(PG_DSN)
    rows = conn.execute(
        "SELECT to_char(window_start AT TIME ZONE 'UTC','HH24:MI') w, page, views, users "
        "FROM page_views_1m ORDER BY window_start, page"
    ).fetchall()
    for r in rows[:40]:
        print(f"{r[0]}  {r[1]:<9} views={r[2]:<4} users={r[3]}")
    print(
        f"... {len(rows)} janelas · rejects={db.count(conn, 'stream_rejects')} · lotes={db.count(conn, 'batch_log')}"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="streamlab")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="3 fases + verificação contra a referência")
    sub.add_parser("report", help="mostra o resultado analítico no PostgreSQL")
    sub.add_parser("reset", help="apaga tópico, checkpoint e tabelas")
    pr = sub.add_parser("produce", help="envia UMA fase para o Kafka")
    pr.add_argument("--phase", type=int, required=True, choices=[1, 2, 3])
    sub.add_parser("job", help="processa o que há de novo (availableNow) e encerra")
    a = p.parse_args(argv)
    if a.cmd == "demo":
        cmd_demo(a)
    elif a.cmd == "report":
        cmd_report(a)
    elif a.cmd == "reset":
        reset_all()
        print("ok")
    elif a.cmd == "produce":
        from .producer import produce_phase

        print(f"enviadas {produce_phase(BOOTSTRAP, TOPIC, build_scenario()[a.phase - 1])} mensagens")
    elif a.cmd == "job":
        from .job import run_once

        print(run_once(_spark(), BOOTSTRAP, TOPIC, PG_DSN, CHECKPOINTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
