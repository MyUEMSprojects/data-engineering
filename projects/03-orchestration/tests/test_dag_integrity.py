"""Integridade dos DAGs: importam sem erro e têm as propriedades esperadas.

Roda DENTRO do container do Airflow (precisa do pacote `airflow`):
    docker compose run --rm airflow-scheduler python -m pytest /opt/airflow/tests -q
Fora dele, é ignorado.
"""

import pytest

pytest.importorskip("airflow")
from airflow.models import DagBag


@pytest.fixture(scope="module")
def dagbag():
    return DagBag(dag_folder="/opt/airflow/dags", include_examples=False)


def test_sem_erros_de_importacao(dagbag):
    assert dagbag.import_errors == {}


def test_dag_orders_daily_estrutura(dagbag):
    dag = dagbag.get_dag("orders_daily")
    assert dag is not None
    assert dag.max_active_runs == 1
    assert dag.default_args["retries"] >= 1
    assert {t.task_id for t in dag.tasks} == {
        "extract",
        "validate",
        "load",
        "quality_checks",
        "publish_summary",
    }


def test_dependencias_formam_um_dag_sem_ciclos(dagbag):
    dag = dagbag.get_dag("orders_daily")
    order = [t.task_id for t in dag.topological_sort()]
    assert order.index("extract") < order.index("validate") < order.index("load")
    assert (
        order.index("load")
        < order.index("quality_checks")
        < order.index("publish_summary")
    )
