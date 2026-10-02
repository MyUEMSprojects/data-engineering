# Testes

`test_orders_lib.py` roda no host (9 testes, sem Airflow); `test_dag_integrity.py` roda **dentro** do contêiner (importação do DAG, 5 tasks, `max_active_runs=1`, ordem topológica).
