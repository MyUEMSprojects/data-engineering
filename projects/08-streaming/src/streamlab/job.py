"""O job de streaming: Kafka → parse → watermark → dedup → janelas de 1 min → PostgreSQL.

Trigger ``availableNow``: processa tudo que chegou desde o último checkpoint e PARA — o mesmo código de
um job contínuo, com custo de batch (e é o que torna o demo determinístico: 1 fase = 1 micro-lote).
O estado (janelas abertas, dedup, watermark) e os offsets vivem no CHECKPOINT; rodar de novo retoma de lá.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

from . import db
from .events import DELAY_S, WINDOW_S

SCHEMA = StructType(
    [StructField(n, StringType()) for n in ("event_id", "user_id", "page", "event_time")]
    + [StructField("_corrupt_record", StringType())]  # no modo PERMISSIVE, JSON malformado cai aqui
)


def read_kafka(spark: SparkSession, bootstrap: str, topic: str) -> DataFrame:
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "earliest")  # só vale na 1ª vez; depois manda o checkpoint
        .option("failOnDataLoss", "false")
        .load()
    )


def parse(raw: DataFrame) -> DataFrame:
    """value (bytes) → colunas tipadas. Inválida ⇔ JSON ruim, campo ausente/vazio ou data impossível."""
    # ⚠️ from_json é PERMISSIVE: JSON malformado NÃO devolve struct nulo, devolve struct com campos nulos.
    # Para distinguir "JSON quebrado" de "campo ausente" é preciso a coluna _corrupt_record.
    j = F.from_json(F.col("value").cast("string"), SCHEMA, {"columnNameOfCorruptRecord": "_corrupt_record"})
    return raw.select(
        F.col("partition").alias("kafka_partition"),
        F.col("offset").alias("kafka_offset"),
        F.col("value").cast("string").alias("raw"),
        j.alias("j"),
    ).select(
        "kafka_partition",
        "kafka_offset",
        "raw",
        (F.col("j").isNull() | F.col("j._corrupt_record").isNotNull()).alias("bad_json"),
        F.col("j.event_id").alias("event_id"),
        F.col("j.user_id").alias("user_id"),
        F.col("j.page").alias("page"),
        F.try_to_timestamp(F.col("j.event_time")).alias("event_time"),  # ANSI: inválida → NULL, não erro
    )


def _is_valid() -> F.Column:
    ok = F.lit(True)
    for c in ("event_id", "user_id", "page"):
        ok = ok & F.col(c).isNotNull() & (F.col(c) != "")
    return ok & F.col("event_time").isNotNull()


def valid_events(parsed: DataFrame) -> DataFrame:
    return parsed.where(_is_valid()).select("event_id", "user_id", "page", "event_time")


def rejected(parsed: DataFrame) -> DataFrame:
    reason = F.when(F.col("bad_json"), "invalid_json").otherwise("missing_or_bad_field")
    return parsed.where(~_is_valid()).select("kafka_partition", "kafka_offset", reason.alias("reason"), "raw")


def windowed_counts(valid: DataFrame, *, delay_s: int = DELAY_S, window_s: int = WINDOW_S) -> DataFrame:
    """Contagem por (janela de evento, página). A ORDEM importa: watermark → dedup → agregação."""
    return (
        valid.withWatermark("event_time", f"{delay_s} seconds")
        .dropDuplicatesWithinWatermark(["event_id"])
        .groupBy(F.window("event_time", f"{window_s} seconds").alias("w"), "page")
        .agg(F.count("*").alias("views"), F.size(F.collect_set("user_id")).alias("users"))
        .select(F.col("w.start").alias("window_start"), "page", "views", "users")
    )


@dataclass
class JobReport:
    batches: int = 0
    input_rows: int = 0
    dropped_late: int = 0
    watermarks: list[str] = field(default_factory=list)
    applied: dict[str, int] = field(default_factory=dict)  # query → micro-lotes aplicados no destino
    skipped: dict[str, int] = field(default_factory=dict)  # query → reexecuções absorvidas pelo livro-razão


def run_once(spark: SparkSession, bootstrap: str, topic: str, dsn: str, checkpoint_root: str) -> JobReport:
    """Processa o que há de novo e encerra. Devolve métricas lidas do `StreamingQueryProgress`."""
    report = JobReport()

    def sink_windows(batch_df: DataFrame, batch_id: int) -> None:
        conn = db.connect(dsn)
        try:
            rows = db.window_rows(batch_id, [r.asDict() for r in batch_df.collect()])
            ok = db.apply_batch(conn, "windows", batch_id, db.UPSERT_WINDOW, rows)
            bucket = report.applied if ok else report.skipped
            bucket["windows"] = bucket.get("windows", 0) + 1
        finally:
            conn.close()

    def sink_rejects(batch_df: DataFrame, batch_id: int) -> None:
        conn = db.connect(dsn)
        try:
            rows = [
                (r["kafka_partition"], r["kafka_offset"], r["reason"], r["raw"]) for r in batch_df.collect()
            ]
            ok = db.apply_batch(conn, "rejects", batch_id, db.INSERT_REJECT, rows)
            bucket = report.applied if ok else report.skipped
            bucket["rejects"] = bucket.get("rejects", 0) + 1
        finally:
            conn.close()

    q1 = (
        windowed_counts(valid_events(parse(read_kafka(spark, bootstrap, topic))))
        .writeStream.queryName("windows")
        .outputMode("update")
        .foreachBatch(sink_windows)
        .option("checkpointLocation", f"{checkpoint_root}/windows")
        .trigger(availableNow=True)
        .start()
    )
    q2 = (
        rejected(parse(read_kafka(spark, bootstrap, topic)))
        .writeStream.queryName("rejects")
        .outputMode("append")
        .foreachBatch(sink_rejects)
        .option("checkpointLocation", f"{checkpoint_root}/rejects")
        .trigger(availableNow=True)
        .start()
    )
    q1.awaitTermination()
    q2.awaitTermination()

    for p in q1.recentProgress:
        report.batches += 1
        report.input_rows += p.get("numInputRows", 0)
        report.dropped_late += sum(
            op.get("numRowsDroppedByWatermark", 0) for op in p.get("stateOperators", [])
        )
        wm = (p.get("eventTime") or {}).get("watermark")
        if wm:
            report.watermarks.append(wm)
    return report
