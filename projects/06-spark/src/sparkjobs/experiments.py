"""Experimentos que MEDEM o que os livros afirmam: formatos, joins, skew, shuffle, cache, UDF, escrita.

Cada experimento devolve variantes ``(rótulo, segundos, evidência)``. O tempo é o MELHOR de 2
execuções (a 1.ª paga custos de JIT/cache de arquivos) — e é indicativo: o que NÃO varia entre
máquinas é a **evidência estrutural** (plano, nº de tarefas, razão máx/mediana, nº de arquivos).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

from .diagnostics import (
    _get,
    completed_stage_ids,
    plan_lines,
    plan_text,
    slowest_stage,
    timed,
)
from .transforms import detect_hot_keys, salted_join


@dataclass(frozen=True)
class Variant:
    label: str
    seconds: float
    evidence: str


@dataclass
class Ctx:
    spark: SparkSession
    lake: str  # raiz com events/ e users/ (Parquet)

    def events(self) -> DataFrame:
        return self.spark.read.parquet(f"{self.lake}/events")

    def users(self) -> DataFrame:
        return self.spark.read.parquet(f"{self.lake}/users")

    @property
    def work(self) -> str:
        path = f"{self.lake}/_bench"
        os.makedirs(path, exist_ok=True)
        return path


def best_of(build: Callable[[], DataFrame], n: int = 2) -> tuple[DataFrame, list, float]:
    """Executa ``build().collect()`` n vezes e devolve (último df, linhas, MELHOR tempo).

    ⚠️ Armadilha real: com AQE, chamar ``collect()`` de novo no MESMO objeto DataFrame reaproveita
    os stages de shuffle já materializados (2.ª execução ≈ 0,02 s, "de graça"). Por isso o DataFrame
    é RECONSTRUÍDO a cada repetição — senão o benchmark mede o cache, não a consulta.
    """
    df, rows, best = None, [], float("inf")
    for _ in range(n):
        df = build()
        rows, t = timed(df.collect)
        best = min(best, t)
    return df, rows, best


def _dir_stats(path: str, suffix: str) -> tuple[int, int]:
    files = [
        os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(path) for f in fs if f.endswith(suffix)
    ]
    return len(files), sum(files)


def _mb(n: int) -> str:
    return f"{n / 1e6:.1f} MB"


def _rounded(rows) -> dict:
    return {r["country"]: round(r["rev"], 2) for r in rows}


# --------------------------------------------------------------------------- E1
def e1_formats(c: Ctx) -> list[Variant]:
    """CSV vs Parquet vs Parquet particionado: poda de colunas, predicate pushdown, partition pruning."""
    sp = c.spark
    csv_dir, part_dir = f"{c.work}/events_csv", f"{c.work}/events_by_date"
    ev = c.events().withColumn("event_date", F.to_date("event_ts"))
    # sempre regrava as cópias a partir do Parquet atual (cópias velhas distorceriam a comparação)
    c.events().write.mode("overwrite").option("header", True).csv(csv_dir)
    ev.repartition("event_date").write.mode("overwrite").partitionBy("event_date").parquet(part_dir)

    def q(df: DataFrame, extra=None) -> DataFrame:
        d = df.where(F.col("event_type") == "purchase")
        if extra is not None:
            d = d.where(extra)
        return d.agg(F.sum("amount").alias("revenue"))

    def reader(kind: str) -> DataFrame:
        if kind == "csv":
            return sp.read.option("header", True).schema(c.events().schema).csv(csv_dir)
        return sp.read.parquet(part_dir if kind == "part" else f"{c.lake}/events")

    out = []
    for label, kind, path, suffix, extra in [
        ("CSV", "csv", csv_dir, ".csv", None),
        ("Parquet", "parquet", f"{c.lake}/events", ".parquet", None),
        (
            "Parquet particionado por data (filtro de 1 dia)",
            "part",
            part_dir,
            ".parquet",
            F.col("event_date") == "2024-01-15",
        ),
    ]:
        d, _, secs = best_of(lambda k=kind, e=extra: q(reader(k), e))
        n, size = _dir_stats(path, suffix)
        ev_txt = plan_lines(plan_text(d), "ReadSchema", "PartitionFilters", "PushedFilters")
        out.append(Variant(label, secs, f"{n} arquivos, {_mb(size)} em disco · {ev_txt}"))
    return out


# --------------------------------------------------------------------------- E2
def e2_join_strategies(c: Ctx) -> list[Variant]:
    """Sort-merge join (shuffle dos DOIS lados) vs broadcast hash join (sem shuffle do lado grande)."""
    sp = c.spark
    events = c.events().where(F.col("user_id") != 0)  # exclui o usuário quente: isola a ESTRATÉGIA
    users = c.users()
    out = []
    for label, aqe, threshold, hint in [
        ("sort-merge join (broadcast desligado)", "false", "-1", False),
        ("broadcast hash join (dica broadcast)", "false", "-1", True),
    ]:
        sp.conf.set("spark.sql.adaptive.enabled", aqe)
        sp.conf.set("spark.sql.autoBroadcastJoinThreshold", threshold)

        def build(hint=hint):
            dim = F.broadcast(users) if hint else users
            return (
                events.join(dim, "user_id").groupBy("country").agg(F.round(F.sum("amount"), 2).alias("rev"))
            )

        d, _, secs = best_of(build)
        p = plan_text(d)
        joins = [j for j in ("BroadcastHashJoin", "SortMergeJoin") if j in p]
        out.append(Variant(label, secs, f"{joins[0]} · {p.count('Exchange')} Exchange(s) no plano"))
    sp.conf.unset("spark.sql.autoBroadcastJoinThreshold")
    sp.conf.unset("spark.sql.adaptive.enabled")
    return out


# --------------------------------------------------------------------------- E3
def e3_skew(c: Ctx) -> list[Variant]:
    """Join com chave QUENTE: ingênuo × AQE (skew join) × salting manual. Resultados idênticos."""
    sp = c.spark
    events, users = c.events(), c.users()
    hot = detect_hot_keys(events, "user_id")
    sp.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")

    def agg(joined: DataFrame) -> DataFrame:
        return joined.groupBy("country").agg(F.sum("amount").alias("rev"))

    variants = [
        ("ingênuo (AQE desligado)", "false", lambda: agg(events.join(users, "user_id"))),
        (
            "AQE skew join (limiares reduzidos p/ o tamanho do demo)",
            "true",
            lambda: agg(events.join(users, "user_id")),
        ),
        (
            f"salting manual (chaves quentes={hot}, 16 baldes)",
            "false",
            lambda: agg(salted_join(events, users, hot)),
        ),
    ]
    out, reference = [], None
    for label, aqe, build in variants:
        sp.conf.set("spark.sql.adaptive.enabled", aqe)
        sp.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
        sp.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "8m")
        sp.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "4m")
        sp.conf.set("spark.sql.shuffle.partitions", "16")
        before = completed_stage_ids(sp)
        d, rows, secs = best_of(build, n=1)
        result = _rounded(rows)
        reference = reference or result
        assert result == reference, "variantes devem produzir o MESMO resultado"
        st = slowest_stage(sp, before)
        extra = ""
        if aqe == "true":
            extra = " · skew join no plano final" if "skew=true" in plan_text(d) else ""
        out.append(Variant(label, secs, (st.describe() if st else "?") + extra))
    for k in (
        "spark.sql.autoBroadcastJoinThreshold",
        "spark.sql.adaptive.enabled",
        "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes",
        "spark.sql.adaptive.advisoryPartitionSizeInBytes",
        "spark.sql.shuffle.partitions",
    ):
        sp.conf.unset(k)
    return out


# --------------------------------------------------------------------------- E4
def e4_shuffle_partitions(c: Ctx) -> list[Variant]:
    """Nº de partições de shuffle: poucas = tarefas gigantes/spill; demais = overhead de agendamento."""
    sp = c.spark
    d = c.events().groupBy("user_id").agg(F.count("*").alias("n"), F.sum("amount").alias("total"))
    out = []
    for label, n, aqe in [
        ("2000 partições, AQE desligado", 2000, "false"),
        ("200 partições (padrão), AQE desligado", 200, "false"),
        ("8 partições, AQE desligado", 8, "false"),
        ("2000 partições + AQE (coalesce automático)", 2000, "true"),
    ]:
        sp.conf.set("spark.sql.shuffle.partitions", str(n))
        sp.conf.set("spark.sql.adaptive.enabled", aqe)
        sp.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
        before = completed_stage_ids(sp)
        _, secs = timed(lambda: d.write.format("noop").mode("overwrite").save())
        tasks = _shuffle_read_tasks(sp, before)
        out.append(Variant(label, secs, f"stage de leitura do shuffle rodou com {tasks} tarefa(s)"))
    sp.conf.unset("spark.sql.shuffle.partitions")
    sp.conf.unset("spark.sql.adaptive.enabled")
    sp.conf.unset("spark.sql.adaptive.coalescePartitions.enabled")
    return out


def _shuffle_read_tasks(sp: SparkSession, before: set[int]) -> int:
    sc = sp.sparkContext
    base = f"{sc.uiWebUrl}/api/v1/applications/{sc.applicationId}"
    best = (0, 0)
    for s in _get(f"{base}/stages?status=complete"):
        if s["stageId"] not in before and s.get("shuffleReadBytes", 0) > 0:
            best = max(best, (s["shuffleReadBytes"], s["numTasks"]))
    return best[1]


# --------------------------------------------------------------------------- E5
def e5_cache(c: Ctx) -> list[Variant]:
    """Reuso de um DataFrame caro em 3 ações: sem cache recomputa 3×; com cache, 1×."""
    sp = c.spark
    sp.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
    base = (
        c.events()
        .join(c.users(), "user_id")
        .groupBy("user_id", "country", "event_type")
        .agg(F.sum("amount").alias("total"), F.count("*").alias("n"))
    )

    def three_actions(df: DataFrame):
        df.groupBy("country").agg(F.sum("total")).collect()
        df.groupBy("event_type").agg(F.sum("n")).collect()
        return df.count()

    _, t_plain = timed(lambda: three_actions(base))
    cached = base.persist()
    _, t_cached = timed(lambda: three_actions(cached))
    level = str(cached.storageLevel)
    cached.unpersist()
    sp.conf.unset("spark.sql.autoBroadcastJoinThreshold")
    return [
        Variant("sem cache (join+agg recomputados nas 3 ações)", t_plain, "3 execuções completas"),
        Variant("persist() — 1ª ação materializa, 2ª/3ª leem da memória", t_cached, f"nível: {level}"),
    ]


# --------------------------------------------------------------------------- E6
def e6_udf(c: Ctx) -> list[Variant]:
    """Função nativa (Catalyst/Tungsten, JVM) vs UDF Python (serializa linha a linha para o Python)."""
    ev = c.events()
    fee_py = F.udf(lambda a: a * 0.05 if a > 100 else a * 0.02, DoubleType())
    fee_native = F.when(F.col("amount") > 100, F.col("amount") * 0.05).otherwise(F.col("amount") * 0.02)
    out = []
    totals = []
    for label, expr in [("expressão nativa (F.when)", fee_native), ("UDF Python", fee_py("amount"))]:
        d, rows, secs = best_of(lambda e=expr: ev.agg(F.round(F.sum(e), 2).alias("fees")))
        totals.append(rows[0]["fees"])
        p = plan_text(d)
        marker = "BatchEvalPython" if "BatchEvalPython" in p else "sem nó de Python (tudo na JVM)"
        out.append(Variant(label, secs, marker))
    assert abs(totals[0] - totals[1]) < 0.01, "UDF e nativa devem dar o mesmo resultado"
    return out


# --------------------------------------------------------------------------- E7
def e7_write_layout(c: Ctx) -> list[Variant]:
    """Layout de escrita: partitionBy sem repartition = explosão de arquivos pequenos."""
    ev = c.events().withColumn("event_date", F.to_date("event_ts"))
    out = []
    for label, build in [
        ("partitionBy('event_date') direto", lambda d: d.write.partitionBy("event_date")),
        (
            "repartition('event_date') + partitionBy",
            lambda d: d.repartition("event_date").write.partitionBy("event_date"),
        ),
        ("coalesce(2) sem partitionBy", lambda d: d.coalesce(2).write),
    ]:
        path = f"{c.work}/write_layout"
        _, secs = timed(lambda b=build, p=path: b(ev).mode("overwrite").parquet(p))
        n, size = _dir_stats(path, ".parquet")
        out.append(Variant(label, secs, f"{n} arquivos · média {size / max(n, 1) / 1024:.0f} KB/arquivo"))
    return out


EXPERIMENTS: dict[str, Callable[[Ctx], list[Variant]]] = {
    "e1": e1_formats,
    "e2": e2_join_strategies,
    "e3": e3_skew,
    "e4": e4_shuffle_partitions,
    "e5": e5_cache,
    "e6": e6_udf,
    "e7": e7_write_layout,
}
