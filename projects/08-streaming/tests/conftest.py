import os

import pytest


@pytest.fixture(scope="session")
def spark():
    from pyspark.sql import SparkSession

    s = (
        SparkSession.builder.appName("tests")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    s.sparkContext.setLogLevel("ERROR")
    yield s
    s.stop()


@pytest.fixture
def pg():
    dsn = os.environ.get("PG_DSN")
    if not dsn:
        pytest.skip("defina PG_DSN (docker compose up -d postgres)")
    from streamlab import db

    conn = db.connect(dsn)
    db.reset(conn)
    yield conn
    conn.close()
