from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from collections import Counter

import psycopg

from . import admin as adm
from .config import BOOTSTRAP, DLQ_TOPIC, PARTITIONS, PG_DSN, TOPIC
from .consumer import make_consumer
from .events import expected_state, generate_events
from .pipeline import Pipeline
from .producer import make_producer, produce_events
from .sink import PostgresSink


# ------------------------------------------------------------------ comandos
def cmd_topics(_a) -> None:
    adm.ensure_topics(BOOTSTRAP, {TOPIC: PARTITIONS, DLQ_TOPIC: 1})
    print(f"tópicos prontos: {TOPIC} ({PARTITIONS} partições) · {DLQ_TOPIC} (1 partição)")


def cmd_produce(a) -> None:
    adm.ensure_topics(BOOTSTRAP, {TOPIC: PARTITIONS, DLQ_TOPIC: 1})
    evs = list(generate_events(a.orders, seed=a.seed))
    t0 = time.time()
    s = produce_events(BOOTSTRAP, TOPIC, evs, poison=a.poison, seed=a.seed)
    print(
        f"produzidas {s.sent} mensagens ({len(evs)} eventos + {s.poison} veneno) · "
        f"entregues={s.delivered} falhas={s.failed} · {time.time() - t0:.1f}s"
    )
    if s.failed:
        sys.exit(1)


def cmd_consume(a) -> None:
    stop = {"flag": False}
    t_start = time.time()

    def say(msg: str) -> None:
        print(f"[{a.name} +{time.time() - t_start:5.1f}s] {msg}", flush=True)

    signal.signal(signal.SIGTERM, lambda *_: stop.update(flag=True))
    signal.signal(signal.SIGINT, lambda *_: stop.update(flag=True))

    def on_assign(_c, parts):
        say(f"ATRIBUÍDAS: {sorted(p.partition for p in parts)}")

    def on_revoke(_c, parts):
        say(f"REVOGADAS: {sorted(p.partition for p in parts)}")

    consumer = make_consumer(
        BOOTSTRAP, a.group, TOPIC, assignor=a.assignor, on_assign=on_assign, on_revoke=on_revoke
    )
    sink = PostgresSink(PG_DSN)

    def crash(batch_no: int) -> None:
        if a.crash_at_batch and batch_no == a.crash_at_batch:
            say(f"💥 CRASH entre gravar no destino e commitar o offset (lote {batch_no})")
            os._exit(1)  # morte brusca: sem close(), sem commit, sem flush

    pipe = Pipeline(
        consumer,
        sink,
        make_producer(BOOTSTRAP),
        DLQ_TOPIC,
        batch_size=a.batch_size,
        before_commit=crash,
    )
    try:
        stats = pipe.run(max_idle_s=a.max_idle, stop=lambda: stop["flag"])
        say("ocioso/encerrando: fechando o consumidor (sai do grupo)")
    finally:
        consumer.close()
        sink.close()
    say(f"STATS {json.dumps(dict(stats))}")


def cmd_lag(a) -> None:
    rows = adm.lag(BOOTSTRAP, a.group, TOPIC)
    print("partição  commitado  fim    lag")
    for r in rows:
        print(f"{r.partition:>8}  {r.committed:>9}  {r.end:>5}  {r.lag:>4}")
    print(f"LAG TOTAL = {sum(r.lag for r in rows)}")


def _sql_one(q: str):
    with psycopg.connect(PG_DSN) as c, c.cursor() as cur:
        cur.execute(q)
        return cur.fetchone()[0]


def check_state(orders: int, seed: int) -> dict:
    """Compara o estado do destino com o gabarito calculado a partir dos eventos gerados."""
    evs = list(generate_events(orders, seed=seed))
    exp = expected_state(evs)
    with psycopg.connect(PG_DSN) as c, c.cursor() as cur:
        cur.execute("select order_id, status, seq from orders_current")
        got = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
        cur.execute("select count(*), count(distinct event_id) from order_events")
        n_events, n_distinct = cur.fetchone()
    return {
        "expected_events": len(evs),
        "events_in_sink": n_events,
        "duplicate_event_ids": n_events - n_distinct,
        "expected_orders": len(exp),
        "orders_in_sink": len(got),
        "wrong_state": sum(1 for k, v in exp.items() if got.get(k) != v),
    }


def cmd_report(a) -> None:
    r = check_state(a.orders, a.seed)
    print(json.dumps(r, indent=2))
    ok = (
        r["expected_events"] == r["events_in_sink"]
        and r["duplicate_event_ids"] == 0
        and r["wrong_state"] == 0
        and r["expected_orders"] == r["orders_in_sink"]
    )
    print("CONSISTENTE ✔" if ok else "INCONSISTENTE ✖")
    sys.exit(0 if ok else 1)


def _fresh() -> None:
    adm.delete_topics(BOOTSTRAP, [TOPIC, DLQ_TOPIC])
    with psycopg.connect(PG_DSN) as c:
        c.execute("truncate order_events, orders_current")


def _spawn(name: str, group: str, *extra: str):
    log = tempfile.NamedTemporaryFile("w+", prefix=f"kpipe-{name}-", suffix=".log", delete=False)
    p = subprocess.Popen(
        [sys.executable, "-m", "kpipe", "consume", "--name", name, "--group", group, *extra],
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return p, log.name


def cmd_demo(a) -> None:
    """Cenário completo: 2 consumidores no mesmo grupo, um deles MORRE no meio; nada se perde nem duplica."""
    group = f"demo-{int(time.time())}"
    t_start = time.time()

    def step(msg: str) -> None:
        print(f"[{time.time() - t_start:6.1f}s] {msg}", flush=True)

    print("== 1. ambiente limpo e tópicos ==")
    _fresh()
    step("ambiente limpo")
    adm.ensure_topics(BOOTSTRAP, {TOPIC: PARTITIONS, DLQ_TOPIC: 1})
    step("tópicos criados")
    print(f"== 2. produzindo {a.orders} pedidos (+{a.poison} mensagens-veneno) ==")
    evs = list(generate_events(a.orders, seed=a.seed))
    s = produce_events(BOOTSTRAP, TOPIC, evs, poison=a.poison, seed=a.seed)
    print(f"   enviadas={s.sent} entregues={s.delivered} falhas={s.failed}")
    step("produção concluída")

    print("== 3. dois consumidores, mesmo grupo; o 'A' morre no lote 2 (antes do commit) ==")
    pa, la = _spawn("A", group, "--crash-at-batch", "2", "--batch-size", "200", "--max-idle", "25")
    pb, lb = _spawn("B", group, "--batch-size", "200", "--max-idle", "25")
    pa.wait(timeout=180)
    step("A terminou (crash)")
    pb.wait(timeout=180)
    step("B terminou")
    lines = open(la).read().splitlines() + open(lb).read().splitlines()
    for ln in lines:
        if ln.startswith("[") and "STATS" not in ln:
            print("  ", ln)
    stats_b = next(
        (
            json.loads(ln.split("STATS ", 1)[1])
            for ln in lines
            if ln.startswith("[B") and "STATS" in ln
        ),
        {},
    )
    print(f"   B processou: {stats_b}")

    print("== 4. verificações ==")
    step("início das verificações")
    r = check_state(a.orders, a.seed)
    total_lag = sum(x.lag for x in adm.lag(BOOTSTRAP, group, TOPIC))
    dlq = adm.read_all(BOOTSTRAP, DLQ_TOPIC)
    hdr = [{k: v.decode() for k, v in m.headers()} for m in dlq]
    # a DLQ também é at-least-once: um lote reentregue reenvia seus venenos. Identidade = header "source".
    unique = {h["source"]: h["error"] for h in hdr}
    reasons = Counter(unique.values())
    checks = [
        ("o consumidor A realmente morreu (exit != 0)", pa.returncode != 0),
        ("todos os eventos válidos estão no destino", r["events_in_sink"] == r["expected_events"]),
        ("nenhum evento duplicado no destino", r["duplicate_event_ids"] == 0),
        (
            "estado atual de TODOS os pedidos correto",
            r["wrong_state"] == 0 and r["orders_in_sink"] == r["expected_orders"],
        ),
        (
            "houve REENTREGA (lote do crash reprocessado) e foi absorvida",
            stats_b.get("duplicates_ignored", 0) > 0,
        ),
        (
            f"DLQ recebeu as {a.poison} mensagens-veneno (distintas por origem)",
            len(unique) == a.poison,
        ),
        ("lag final = 0", total_lag == 0),
    ]
    for label, ok in checks:
        print(f"   {'✔' if ok else '✖'} {label}")
    print(
        f"   DLQ: {len(dlq)} mensagens ({len(unique)} distintas — a diferença são reentregas) · motivos: {dict(reasons)}"
    )
    sys.exit(0 if all(ok for _, ok in checks) else 1)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kpipe")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("topics")
    s = sub.add_parser("produce")
    s.add_argument("--orders", type=int, default=1000)
    s.add_argument("--poison", type=int, default=0)
    s.add_argument("--seed", type=int, default=42)
    s = sub.add_parser("consume")
    s.add_argument("--group", default="orders-sink")
    s.add_argument("--name", default="c1")
    s.add_argument("--batch-size", type=int, default=500)
    s.add_argument("--max-idle", type=float, default=10.0)
    s.add_argument(
        "--assignor", default="cooperative-sticky", help="range | roundrobin | cooperative-sticky"
    )
    s.add_argument("--crash-at-batch", type=int, default=0, help="injeção de falha (demo/testes)")
    s = sub.add_parser("lag")
    s.add_argument("--group", default="orders-sink")
    s = sub.add_parser("report")
    s.add_argument("--orders", type=int, default=1000)
    s.add_argument("--seed", type=int, default=42)
    s = sub.add_parser("demo")
    s.add_argument("--orders", type=int, default=1500)
    s.add_argument("--poison", type=int, default=7)
    s.add_argument("--seed", type=int, default=42)
    a = p.parse_args(argv)
    {
        "topics": cmd_topics,
        "produce": cmd_produce,
        "consume": cmd_consume,
        "lag": cmd_lag,
        "report": cmd_report,
        "demo": cmd_demo,
    }[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
