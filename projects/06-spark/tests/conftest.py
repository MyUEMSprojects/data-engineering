import pytest

from sparkjobs.datagen import make_events, make_users
from sparkjobs.session import get_spark


@pytest.fixture(scope="session")
def spark():
    s = get_spark("tests", master="local[2]", shuffle_partitions=4, ui=True)
    yield s
    s.stop()


@pytest.fixture(scope="session")
def tiny_lake(spark, tmp_path_factory):
    """Lake minúsculo (20 mil eventos, 30% de um usuário quente) em Parquet, como o `generate` faz."""
    root = str(tmp_path_factory.mktemp("lake"))
    make_users(spark, 500).coalesce(1).write.parquet(f"{root}/users")
    make_events(spark, 20_000, 500, hot_share=0.3).repartition(4).write.parquet(f"{root}/events")
    return root
