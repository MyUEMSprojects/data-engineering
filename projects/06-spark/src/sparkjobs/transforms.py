"""Transformações PURAS (DataFrame → DataFrame): testáveis com uma sessão local pequena."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

VALID_TYPES = ["view", "click", "add_to_cart", "purchase", "refund"]


def clean_events(events: DataFrame) -> DataFrame:
    """Remove lixo, deduplica por event_id e deriva a data (UTC) — a silver."""
    return (
        events.where(F.col("user_id").isNotNull() & (F.col("amount") >= 0))
        .where(F.col("event_type").isin(VALID_TYPES))
        .dropDuplicates(["event_id"])
        .withColumn("event_date", F.to_date("event_ts"))
    )


def enrich(events: DataFrame, users: DataFrame, *, broadcast_users: bool = True) -> DataFrame:
    """Junta com a dimensão. ``broadcast`` evita o shuffle do lado grande (dimensão pequena)."""
    dim = users.select("user_id", "country")
    if broadcast_users:
        dim = F.broadcast(dim)
    return events.join(dim, "user_id", "left").fillna({"country": "UNKNOWN"})


def daily_country_metrics(enriched: DataFrame) -> DataFrame:
    """Gold: métricas por dia e país. Receita = compras − reembolsos."""
    return (
        enriched.groupBy("event_date", "country")
        .agg(
            F.count("*").alias("events"),
            F.countDistinct("user_id").alias("active_users"),
            F.sum(F.when(F.col("event_type") == "purchase", 1).otherwise(0)).alias("purchases"),
            F.round(
                F.sum(
                    F.when(F.col("event_type") == "purchase", F.col("amount"))
                    .when(F.col("event_type") == "refund", -F.col("amount"))
                    .otherwise(0.0)
                ),
                2,
            ).alias("net_revenue"),
        )
        .orderBy("event_date", "country")
    )


def detect_hot_keys(df: DataFrame, key: str, *, min_share: float = 0.05, sample: float = 0.1) -> list:
    """Chaves que concentram >= min_share das linhas (em uma amostra)."""
    s = df.sample(fraction=sample, seed=1) if sample < 1 else df
    total = s.count()
    rows = s.groupBy(key).count().where(F.col("count") >= min_share * total).collect()
    return [r[key] for r in rows]


def salted_join(events: DataFrame, users: DataFrame, hot_keys: list, *, buckets: int = 16) -> DataFrame:
    """Join com *salting*: espalha as chaves QUENTES por ``buckets`` partições.

    - lado grande (events): chave quente ganha um sal aleatório 0..B-1; as demais, sal 0;
    - lado pequeno (users): a linha da chave quente é REPLICADA B vezes (uma por sal).
    Custo: B× linhas só para as chaves quentes — por isso salgamos só elas.
    """
    is_hot = F.col("user_id").isin(hot_keys)
    ev = events.withColumn("salt", F.when(is_hot, F.floor(F.rand(3) * buckets).cast("int")).otherwise(0))
    dim = users.select("user_id", "country").withColumn(
        "salt",
        F.explode(F.when(is_hot, F.sequence(F.lit(0), F.lit(buckets - 1))).otherwise(F.array(F.lit(0)))),
    )
    return ev.join(dim, ["user_id", "salt"], "left").drop("salt")
