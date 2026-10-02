"""DAG `orders_daily` — pipeline diário idempotente, particionado por data lógica.

extract ─► validate ─► load ─► quality_checks ─► publish_summary

Princípios (ver módulos 10 e 11 do repositório):
* **Data lógica, nunca `now()`**: cada run processa UMA partição (o dia do intervalo).
* **Idempotente**: caminho determinístico + escrita atômica; carga = DELETE+INSERT da
  partição numa transação; resumo = upsert. Retry, re-run e backfill são seguros.
* **Orquestre, não transforme**: a lógica está em `include/orders_lib.py` (testada à parte).
* Passa só **referências** (caminho/contagens) entre tasks — nunca DataFrames via XCom.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pendulum
from airflow.exceptions import AirflowFailException
from airflow.sdk import Param, dag, get_current_context, task
from airflow.timetables.interval import CronDataIntervalTimetable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "include"))
import orders_lib as lib

DATA_ROOT = Path(os.environ.get("PIPELINE_DATA_ROOT", "/opt/airflow/data"))
WAREHOUSE_URI = os.environ.get(
    "WAREHOUSE_URI", "postgresql://de:de@postgres:5432/warehouse"
)
MAX_REJECT_RATE = float(os.environ.get("MAX_REJECT_RATE", "0.10"))


def _partition_day() -> date:
    """A partição é o INÍCIO do intervalo de dados do run (não o relógio da máquina).

    Em run MANUAL (`dags test`/trigger) o intervalo é pontual e a partição é a data lógica informada.
    """
    ctx = get_current_context()
    start = ctx["data_interval_start"]
    return date(start.year, start.month, start.day)


def _connect():
    import psycopg2

    return psycopg2.connect(WAREHOUSE_URI)


@dag(
    dag_id="orders_daily",
    description="ETL diário idempotente de pedidos (extract→validate→load→quality→summary)",
    # CronDataIntervalTimetable => cada run tem um INTERVALO [00:00 do dia D, 00:00 do dia D+1) e só dispara
    # ao FIM dele: o run das 00:00 do dia 2 processa a partição do dia 1 (já completa).
    # (O timetable cron "pontual", padrão do Airflow 3, tem data_interval_start == end.)
    schedule=CronDataIntervalTimetable("0 0 * * *", timezone="UTC"),
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,  # ligue só quando quiser backfill automático; use `airflow backfill create`
    max_active_runs=1,
    default_args={"owner": "dados", "retries": 2, "retry_delay": timedelta(seconds=10)},
    params={
        "rows": Param(
            200, type="integer", minimum=1, description="pedidos sintéticos por dia"
        ),
        "dirty_rate": Param(
            0.02,
            type="number",
            minimum=0,
            maximum=1,
            description="fração de linhas inválidas injetadas (teste do gate)",
        ),
    },
    tags=["projeto-03", "idempotente"],
)
def orders_daily():
    @task
    def extract() -> str:
        """Gera/baixa os dados do dia e grava a partição de forma atômica e determinística."""
        ctx = get_current_context()
        day = _partition_day()
        rows = lib.generate_orders(
            day, ctx["params"]["rows"], ctx["params"]["dirty_rate"]
        )
        path = lib.partition_path(DATA_ROOT, day)
        n = lib.write_csv_atomic(path, rows)
        print(f"extract: {n} linhas em {path}")
        return str(path)

    @task
    def validate(path: str) -> dict:
        """Valida o arquivo; **falha** (sem retry) se a taxa de rejeição passar do limite."""
        day = _partition_day()
        res = lib.validate(lib.read_csv_rows(path), day)
        stats = {
            "rows_read": res.total,
            "rows_valid": len(res.valid),
            "rows_rejected": len(res.rejected),
        }
        print(f"validate: {stats} (taxa={res.reject_rate:.1%})")
        if res.reject_rate > MAX_REJECT_RATE:
            # AirflowFailException = falha PERMANENTE (retry não ajuda: o dado está ruim)
            raise AirflowFailException(
                f"taxa de rejeição {res.reject_rate:.1%} > {MAX_REJECT_RATE:.0%}; dados não carregados"
            )
        return stats

    @task
    def load(path: str, stats: dict) -> int:
        """Overwrite da partição (DELETE+INSERT) numa transação: tudo-ou-nada e idempotente."""
        day = _partition_day()
        valid = lib.validate(lib.read_csv_rows(path), day).valid
        ctx = get_current_context()
        conn = _connect()
        try:
            with (
                conn
            ), conn.cursor() as cur:  # `with conn` = commit/rollback da transação
                cur.execute("DELETE FROM orders_daily WHERE order_date = %s", (day,))
                cur.executemany(
                    "INSERT INTO orders_daily (order_id, customer_id, amount, status, order_date,"
                    " created_at) VALUES (%(order_id)s, %(customer_id)s, %(amount)s, %(status)s,"
                    " %(order_date)s, %(created_at)s)",
                    valid,
                )
                cur.execute(
                    "INSERT INTO pipeline_runs (dag_run_id, order_date, rows_read, rows_valid,"
                    " rows_rejected) VALUES (%s, %s, %s, %s, %s)",
                    (
                        ctx["run_id"],
                        day,
                        stats["rows_read"],
                        stats["rows_valid"],
                        stats["rows_rejected"],
                    ),
                )
        finally:
            conn.close()
        print(f"load: partição {day} recarregada com {len(valid)} linhas")
        return len(valid)

    @task
    def quality_checks(loaded: int) -> None:
        """Testes de dados DEPOIS da carga: bloqueiam o resumo se algo estiver errado."""
        day = _partition_day()
        checks = {
            "tem_linhas": "SELECT count(*) > 0 FROM orders_daily WHERE order_date = %s",
            "chave_unica": "SELECT count(*) = count(DISTINCT order_id) FROM orders_daily"
            " WHERE order_date = %s",
            "sem_valor_negativo": "SELECT count(*) = 0 FROM orders_daily WHERE order_date = %s"
            " AND amount < 0",
            "contagem_bate_com_a_carga": f"SELECT count(*) = {int(loaded)} FROM orders_daily"
            " WHERE order_date = %s",
        }
        conn = _connect()
        failed = []
        try:
            with conn.cursor() as cur:
                for name, sql in checks.items():
                    cur.execute(sql, (day,))
                    ok = cur.fetchone()[0]
                    print(f"quality[{name}]: {'OK' if ok else 'FALHOU'}")
                    if not ok:
                        failed.append(name)
        finally:
            conn.close()
        if failed:
            raise AirflowFailException(f"checks de qualidade falharam: {failed}")

    @task
    def publish_summary() -> dict:
        """Upsert do resumo diário (idempotente por chave)."""
        day = _partition_day()
        conn = _connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO daily_summary (order_date, orders, revenue)
                    SELECT %s, count(*), coalesce(sum(amount) FILTER (WHERE status <> 'canceled'), 0)
                    FROM orders_daily WHERE order_date = %s
                    ON CONFLICT (order_date) DO UPDATE
                      SET orders = EXCLUDED.orders, revenue = EXCLUDED.revenue, updated_at = now()
                    RETURNING orders, revenue
                    """,
                    (day, day),
                )
                orders, revenue = cur.fetchone()
        finally:
            conn.close()
        out = {
            "order_date": day.isoformat(),
            "orders": orders,
            "revenue": float(revenue),
        }
        print(f"summary: {out}")
        return out

    path = extract()
    stats = validate(path)
    loaded = load(path, stats)
    quality_checks(loaded) >> publish_summary()


orders_daily()
