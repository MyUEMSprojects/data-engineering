"""Medir em vez de achar: planos, tamanho de partições e tempo de tarefas (REST API do Spark UI)."""

from __future__ import annotations

import contextlib
import io
import json
import statistics
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def plan_text(df: DataFrame, mode: str = "formatted") -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        df.explain(mode=mode)
    return buf.getvalue()


def plan_lines(plan: str, *prefixes: str) -> str:
    """Extrai linhas relevantes (ex.: ``PushedFilters``, ``ReadSchema``) de um plano."""
    keep = [ln.strip() for ln in plan.splitlines() if any(p in ln for p in prefixes)]
    return " | ".join(dict.fromkeys(keep))


def timed(fn: Callable[[], object]) -> tuple[object, float]:
    t0 = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t0


@dataclass(frozen=True)
class PartitionSkew:
    partitions: int
    max_rows: int
    median_rows: float

    @property
    def ratio(self) -> float:
        return self.max_rows / max(self.median_rows, 1)


def partition_skew(df: DataFrame, *by: str, n: int | None = None) -> PartitionSkew:
    """Linhas por partição APÓS particionar por ``by`` (o que um shuffle por essa chave faria)."""
    parted = df.repartition(n, *by) if n else df.repartition(*by)
    counts = [r["count"] for r in parted.groupBy(F.spark_partition_id().alias("p")).count().collect()]
    return PartitionSkew(len(counts), max(counts), statistics.median(counts))


# ---------------------------------------------------------------- REST API (stages)
def _get(url: str):
    with urllib.request.urlopen(url, timeout=10) as r:  # noqa: S310 — URL do próprio driver
        return json.load(r)


def completed_stage_ids(spark: SparkSession) -> set[int]:
    sc = spark.sparkContext
    base = f"{sc.uiWebUrl}/api/v1/applications/{sc.applicationId}"
    return {s["stageId"] for s in _get(f"{base}/stages?status=complete")}


@dataclass(frozen=True)
class StageTasks:
    stage_id: int
    tasks: int
    median_ms: float
    max_ms: float

    @property
    def ratio(self) -> float:
        return self.max_ms / max(self.median_ms, 1)

    def describe(self) -> str:
        return (
            f"stage mais lento: {self.tasks} tarefas · mediana={self.median_ms:.0f} ms · "
            f"máx={self.max_ms:.0f} ms (≈{self.ratio:.1f}× a mediana)"
        )


def slowest_stage(spark: SparkSession, before: set[int]) -> StageTasks | None:
    """Entre os stages de REDUCE (que leram shuffle) concluídos depois de ``before``: o de tarefa mais lenta."""
    sc = spark.sparkContext
    base = f"{sc.uiWebUrl}/api/v1/applications/{sc.applicationId}"
    best: StageTasks | None = None
    for s in _get(f"{base}/stages?status=complete"):
        if s["stageId"] in before or s["numTasks"] < 2 or s.get("shuffleReadBytes", 0) == 0:
            continue
        q = _get(f"{base}/stages/{s['stageId']}/{s['attemptId']}/taskSummary?quantiles=0.5,1.0")
        med, mx = q["executorRunTime"]
        cand = StageTasks(s["stageId"], s["numTasks"], med, mx)
        if best is None or cand.max_ms > best.max_ms:
            best = cand
    return best
