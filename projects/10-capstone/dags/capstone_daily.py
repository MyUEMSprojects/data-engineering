"""DAG diário do capstone (Airflow 3): ingest → gate → silver → gold → observe.

Os imports de `capstone` ficam DENTRO das tasks de propósito: o DAG é parseado pelo scheduler a cada poucos segundos
e não deve exigir deltalake/duckdb no processo dele. Em produção, execute as tasks em ambiente próprio
(`@task.external_python`, `DockerOperator` ou `KubernetesPodOperator`) com a imagem deste projeto.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from airflow.exceptions import AirflowFailException
from airflow.sdk import dag, task
from airflow.timetables.interval import CronDataIntervalTimetable


@dag(
    dag_id="capstone_daily",
    schedule=CronDataIntervalTimetable("0 2 * * *", timezone="UTC"),  # o run das 02:00 do dia D+1 processa o dia D inteiro
    start_date=datetime(2024, 3, 1, tzinfo=UTC),
    catchup=False,  # backfill é ação explícita: `airflow backfill create`
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["capstone", "lakehouse"],
)
def capstone_daily():
    @task
    def ingest(ds=None):
        from capstone import steps

        return steps.ingest(date.fromisoformat(ds))

    @task
    def gate(ds=None, ingested=None):
        from capstone import steps

        g = steps.gate(date.fromisoformat(ds))
        if g.blocked:  # dado ruim na origem: retry NÃO ajuda ⇒ falha sem retentar, e silver/gold nem iniciam
            raise AirflowFailException(
                f"gate bloqueou {ds}: "
                + "; ".join(f"{c.name} ({c.detail})" for c in g.checks if c.level == "hard" and not c.passed)
            )
        return {"rows": g.rows_read, "rejected": len(g.rejects)}

    @task
    def silver(ds=None, gated=None):
        from capstone import steps

        return steps.silver(date.fromisoformat(ds))

    @task
    def gold(silvered=None):
        from capstone import steps

        return steps.gold()

    @task(trigger_rule="all_done")  # métricas saem mesmo quando o gate bloqueia (é quando mais importam)
    def observe(ds=None):
        from capstone import metrics

        metrics.collect(date.fromisoformat(ds), {}, "success")

    i = ingest()
    g = gate(ingested=i)
    s = silver(gated=g)
    d = gold(silvered=s)
    d >> observe()


capstone_daily()
