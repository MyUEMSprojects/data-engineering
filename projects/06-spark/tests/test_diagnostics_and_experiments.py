from pyspark.sql import functions as F

from sparkjobs import experiments
from sparkjobs.cli import main
from sparkjobs.datagen import make_events
from sparkjobs.diagnostics import completed_stage_ids, partition_skew, plan_lines, plan_text, slowest_stage
from sparkjobs.experiments import Ctx, best_of


def test_partition_skew_detects_the_hot_key(spark):
    skewed = make_events(spark, 20_000, 500, hot_share=0.4)
    uniform = make_events(spark, 20_000, 500, hot_share=0.0)
    assert partition_skew(skewed, "user_id", n=8).ratio > 3
    assert partition_skew(uniform, "user_id", n=8).ratio < 1.5


def test_rest_api_reports_task_times_of_a_shuffle_stage(spark):
    spark.conf.set("spark.sql.adaptive.enabled", "false")  # com AQE, dado pequeno vira 1 tarefa só
    try:
        before = completed_stage_ids(spark)
        make_events(spark, 20_000, 500).groupBy("user_id").count().collect()
        st = slowest_stage(spark, before)
    finally:
        spark.conf.unset("spark.sql.adaptive.enabled")
    assert st is not None and st.tasks >= 2 and st.max_ms >= st.median_ms >= 0


def test_plan_helpers(spark):
    p = plan_text(make_events(spark, 100, 10).where(F.col("amount") > 5))
    assert "Filter" in p
    assert plan_lines("a\nReadSchema: x\nb", "ReadSchema") == "ReadSchema: x"


def test_best_of_rebuilds_the_dataframe_every_repetition(spark):
    """Regressão: repetir collect() no MESMO df (com AQE) reaproveita o shuffle e mede ~0 s."""
    calls = []

    def build():
        calls.append(1)
        return make_events(spark, 100, 10).groupBy("user_id").count()

    best_of(build, n=3)
    assert len(calls) == 3


def test_experiments_run_end_to_end_on_a_tiny_lake(spark, tiny_lake):
    ctx = Ctx(spark, tiny_lake)
    by_name = {name: fn(ctx) for name, fn in experiments.EXPERIMENTS.items()}
    assert all(len(v) >= 2 for v in by_name.values())
    # E2: as duas estratégias aparecem no plano
    assert "SortMergeJoin" in by_name["e2"][0].evidence and "BroadcastHashJoin" in by_name["e2"][1].evidence
    # E3: as 3 variantes dão o MESMO resultado (o experimento afirma isso internamente)
    assert len(by_name["e3"]) == 3
    # E6: o UDF Python aparece como BatchEvalPython; o nativo, não
    assert (
        "BatchEvalPython" in by_name["e6"][1].evidence and "BatchEvalPython" not in by_name["e6"][0].evidence
    )
    # E7: partitionBy direto gera >= arquivos que repartition+partitionBy; coalesce(2) gera 2
    n = [int(v.evidence.split()[0]) for v in by_name["e7"]]
    assert n[0] >= n[1] and n[2] == 2
    # E1: o filtro de partição aparece no plano do Parquet particionado
    assert "PartitionFilters: [isnotnull(event_date" in by_name["e1"][2].evidence


def test_pipeline_reconciles_gold_with_silver(spark, tiny_lake, capsys):
    main(["pipeline", "--lake", tiny_lake])
    assert "reconciliação gold × silver: OK" in capsys.readouterr().out
    gold = spark.read.parquet(f"{tiny_lake}/gold/daily_country_metrics")
    silver = spark.read.parquet(f"{tiny_lake}/silver/events")
    assert gold.agg(F.sum("events")).first()[0] == silver.count()
