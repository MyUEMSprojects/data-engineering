from datetime import date

import pytest
from pyspark.sql import functions as F

from sparkjobs.datagen import COUNTRIES, EVENT_TYPES, HOT_USER_ID, make_events, make_users
from sparkjobs.transforms import (
    clean_events,
    daily_country_metrics,
    detect_hot_keys,
    enrich,
    salted_join,
)


def _events(spark, rows):
    return spark.createDataFrame(
        rows, "event_id long, user_id long, event_type string, amount double, event_ts timestamp"
    )


def _ts(day, hour=12):
    from datetime import datetime

    return datetime(2024, 1, day, hour)


# ---------------------------------------------------------------- datagen
def test_users_are_unique_and_valid(spark):
    u = make_users(spark, 100)
    assert u.count() == u.select("user_id").distinct().count() == 100
    assert {r.country for r in u.select("country").distinct().collect()} <= set(COUNTRIES)


def test_events_are_deterministic_and_have_the_requested_skew(spark):
    a = make_events(spark, 30_000, 1000, hot_share=0.4)
    b = make_events(spark, 30_000, 1000, hot_share=0.4)
    assert a.agg(F.sum("amount")).first()[0] == b.agg(F.sum("amount")).first()[0]
    hot = a.where(F.col("user_id") == HOT_USER_ID).count() / 30_000
    assert hot == pytest.approx(0.4, abs=0.03)
    assert {r.event_type for r in a.select("event_type").distinct().collect()} <= set(EVENT_TYPES)
    lo, hi = a.agg(F.min("amount"), F.max("amount")).first()
    assert 0 <= lo and hi <= 200


# ---------------------------------------------------------------- transforms
def test_clean_events_removes_junk_dedups_and_derives_utc_date(spark):
    df = _events(
        spark,
        [
            (1, 10, "purchase", 50.0, _ts(1)),
            (1, 10, "purchase", 50.0, _ts(1)),  # duplicata exata
            (2, None, "click", 1.0, _ts(1)),  # sem usuário
            (3, 11, "click", -5.0, _ts(1)),  # valor negativo
            (4, 12, "teleport", 5.0, _ts(1)),  # tipo inválido
            (5, 13, "view", 0.0, _ts(2, 23)),
        ],
    )
    out = clean_events(df)
    assert sorted(r.event_id for r in out.collect()) == [1, 5]
    assert {r.event_date for r in out.collect()} == {date(2024, 1, 1), date(2024, 1, 2)}


def test_enrich_left_join_fills_unknown_and_never_multiplies_rows(spark):
    ev = _events(spark, [(1, 10, "view", 1.0, _ts(1)), (2, 99, "view", 1.0, _ts(1))])
    users = spark.createDataFrame([(10, "BR", "x")], "user_id long, country string, name string")
    out = enrich(ev, users).collect()
    assert {r.user_id: r.country for r in out} == {10: "BR", 99: "UNKNOWN"}


def test_enrich_broadcast_flag_controls_the_join_strategy(spark):
    ev = _events(spark, [(1, 10, "view", 1.0, _ts(1))])
    users = spark.createDataFrame([(10, "BR", "x")], "user_id long, country string, name string")
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
    try:
        from sparkjobs.diagnostics import plan_text

        assert "BroadcastHashJoin" in plan_text(enrich(ev, users, broadcast_users=True))
        assert "SortMergeJoin" in plan_text(enrich(ev, users, broadcast_users=False))
    finally:
        spark.conf.unset("spark.sql.autoBroadcastJoinThreshold")


def test_daily_metrics_net_revenue_is_purchases_minus_refunds(spark):
    ev = _events(
        spark,
        [
            (1, 10, "purchase", 100.0, _ts(1)),
            (2, 10, "purchase", 50.0, _ts(1)),
            (3, 11, "refund", 30.0, _ts(1)),
            (4, 11, "view", 999.0, _ts(1)),  # view não conta como receita
            (5, 12, "purchase", 70.0, _ts(2)),
        ],
    )
    users = spark.createDataFrame(
        [(10, "BR", "a"), (11, "BR", "b"), (12, "US", "c")], "user_id long, country string, name string"
    )
    rows = {
        (r.event_date, r.country): r for r in daily_country_metrics(enrich(clean_events(ev), users)).collect()
    }
    br = rows[(date(2024, 1, 1), "BR")]
    assert (br.events, br.active_users, br.purchases, br.net_revenue) == (4, 2, 2, 120.0)
    assert rows[(date(2024, 1, 2), "US")].net_revenue == 70.0


# ---------------------------------------------------------------- skew
def test_hot_key_detection(spark):
    skewed = make_events(spark, 20_000, 500, hot_share=0.3)
    uniform = make_events(spark, 20_000, 500, hot_share=0.0)
    assert detect_hot_keys(skewed, "user_id", sample=1.0) == [HOT_USER_ID]
    assert detect_hot_keys(uniform, "user_id", sample=1.0) == []


def test_salted_join_is_equivalent_to_the_plain_join(spark):
    ev = make_events(spark, 20_000, 500, hot_share=0.3)
    users = make_users(spark, 500)
    plain = ev.join(users.select("user_id", "country"), "user_id", "left")
    salted = salted_join(ev, users, [HOT_USER_ID], buckets=8)
    assert salted.count() == plain.count() == 20_000  # nenhuma linha multiplicada/perdida

    def agg(d):
        return {
            r.country: round(r.t, 2) for r in d.groupBy("country").agg(F.sum("amount").alias("t")).collect()
        }

    assert agg(salted) == agg(plain)
