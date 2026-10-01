from __future__ import annotations

import argparse
import sys

from pyspark.sql import functions as F

from sparkjobs.datagen import make_events, make_users
from sparkjobs.diagnostics import partition_skew
from sparkjobs.experiments import EXPERIMENTS, Ctx
from sparkjobs.session import get_spark
from sparkjobs.transforms import clean_events, daily_country_metrics, enrich


def cmd_generate(a) -> None:
    spark = get_spark("generate", ui=False)
    users = make_users(spark, a.users)
    events = make_events(spark, a.events, a.users, hot_share=a.hot_share)
    users.coalesce(1).write.mode("overwrite").parquet(f"{a.lake}/users")
    events.repartition(a.files).write.mode("overwrite").parquet(f"{a.lake}/events")
    ev = spark.read.parquet(f"{a.lake}/events")
    sk = partition_skew(ev, "user_id", n=16)
    print(
        f"events={ev.count():,} users={a.users:,} · shuffle por user_id em 16 partições: "
        f"máx={sk.max_rows:,} linhas vs mediana={sk.median_rows:,.0f} ({sk.ratio:.1f}×)"
    )


def cmd_pipeline(a) -> None:
    """Pipeline real: raw → silver (limpo, particionado por data) → gold (métricas diárias por país)."""
    spark = get_spark("pipeline", ui=False)
    raw = spark.read.parquet(f"{a.lake}/events")
    users = spark.read.parquet(f"{a.lake}/users")

    silver = clean_events(raw)
    silver.write.mode("overwrite").partitionBy("event_date").parquet(f"{a.lake}/silver/events")

    silver = spark.read.parquet(f"{a.lake}/silver/events")
    gold = daily_country_metrics(enrich(silver, users))
    gold.coalesce(1).write.mode("overwrite").parquet(f"{a.lake}/gold/daily_country_metrics")

    g = spark.read.parquet(f"{a.lake}/gold/daily_country_metrics")
    total_events = g.agg(F.sum("events")).first()[0]
    print(f"raw={raw.count():,} · silver={silver.count():,} · gold={g.count():,} linhas")
    assert total_events == silver.count(), "gold deve reconciliar com a silver"
    print("reconciliação gold × silver: OK")
    g.orderBy(F.desc("net_revenue")).show(5, truncate=False)
    print(
        f"executores/paralelismo padrão: {spark.sparkContext.defaultParallelism} · master={spark.sparkContext.master}"
    )


def cmd_bench(a) -> None:
    spark = get_spark("bench", shuffle_partitions=a.shuffle_partitions)
    ctx = Ctx(spark, a.lake)
    spark.read.parquet(f"{a.lake}/events").count()  # aquecimento (JIT + cache de arquivos)
    names = a.only.split(",") if a.only else list(EXPERIMENTS)
    for name in names:
        fn = EXPERIMENTS[name]
        print(f"\n### {name.upper()} — {(fn.__doc__ or '').strip()}")
        print("| variante | tempo (s) | evidência |\n| --- | ---: | --- |")
        for v in fn(ctx):
            print(f"| {v.label} | {v.seconds:.2f} | {v.evidence} |")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sparkjobs")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--lake", default="/data/lake")
    g.add_argument("--events", type=int, default=6_000_000)
    g.add_argument("--users", type=int, default=200_000)
    g.add_argument("--hot-share", type=float, default=0.4)
    g.add_argument("--files", type=int, default=8)
    s = sub.add_parser("pipeline")
    s.add_argument("--lake", default="/data/lake")
    b = sub.add_parser("bench")
    b.add_argument("--lake", default="/data/lake")
    b.add_argument("--only", help="ex.: e2,e3")
    b.add_argument("--shuffle-partitions", type=int, default=16)
    a = p.parse_args(argv)
    {"generate": cmd_generate, "pipeline": cmd_pipeline, "bench": cmd_bench}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
