# DAGs

`orders_daily.py`: DAG diário (Airflow 3, TaskFlow) `extract → validate → load → quality_checks → publish_summary`, com `CronDataIntervalTimetable`, retries e `AirflowFailException` para falhas permanentes. Só orquestra; a lógica está em `../include`.
