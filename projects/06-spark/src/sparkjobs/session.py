from __future__ import annotations

from pyspark.sql import SparkSession


def get_spark(
    app: str = "sparkjobs",
    *,
    master: str | None = None,
    shuffle_partitions: int | None = None,
    ui: bool = True,
    **conf: str,
) -> SparkSession:
    """Cria (ou reaproveita) a sessão. ``master=None`` respeita o ``--master`` do spark-submit."""
    b = SparkSession.builder.appName(app)
    if master:
        b = b.master(master)
    b = b.config("spark.ui.enabled", str(ui).lower()).config("spark.ui.showConsoleProgress", "false")
    b = b.config("spark.sql.session.timeZone", "UTC")
    if shuffle_partitions is not None:
        b = b.config("spark.sql.shuffle.partitions", str(shuffle_partitions))
    for k, v in conf.items():
        b = b.config(k.replace("__", "."), v)
    spark = b.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark
