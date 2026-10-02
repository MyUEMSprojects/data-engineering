"""Geração de dados SINTÉTICOS direto no Spark (sem arquivos de entrada), com SKEW controlado.

``hot_share`` é a fração dos eventos que pertence a UM único usuário (o "usuário quente"):
é o que cria o desbalanceamento clássico de chaves em joins/agregações.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

COUNTRIES = ["BR", "US", "PT", "AR", "MX", "DE", "FR", "JP"]
EVENT_TYPES = ["view", "click", "add_to_cart", "purchase", "refund"]
HOT_USER_ID = 0


def make_users(spark: SparkSession, n_users: int) -> DataFrame:
    countries = F.array(*[F.lit(c) for c in COUNTRIES])
    return spark.range(n_users).select(
        F.col("id").alias("user_id"),
        countries[(F.col("id") % len(COUNTRIES)).cast("int")].alias("country"),
        F.date_add(F.lit("2023-01-01").cast("date"), (F.col("id") % 365).cast("int")).alias("signup_date"),
        F.concat(F.lit("user_"), F.col("id").cast("string")).alias("name"),
    )


def make_events(
    spark: SparkSession,
    n_events: int,
    n_users: int,
    *,
    hot_share: float = 0.4,
    days: int = 30,
    seed: int = 7,
) -> DataFrame:
    types = F.array(*[F.lit(t) for t in EVENT_TYPES])
    r_user, r_type, r_amt, r_day, r_sec = (F.rand(seed + i) for i in range(5))
    user_id = (
        F.when(F.rand(seed + 10) < hot_share, F.lit(HOT_USER_ID))
        .otherwise((r_user * n_users).cast("long"))
        .alias("user_id")
    )
    return spark.range(n_events).select(
        F.col("id").alias("event_id"),
        user_id,
        types[(r_type * len(EVENT_TYPES)).cast("int")].alias("event_type"),
        F.round(r_amt * 200, 2).alias("amount"),
        F.timestamp_seconds(
            F.lit(1704067200) + F.floor(r_day * days) * 86400 + F.floor(r_sec * 86400)  # 2024-01-01T00:00:00Z
        ).alias("event_ts"),
    )
