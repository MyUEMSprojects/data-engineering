# Snapshots dbt

`snap_customers.sql`: SCD tipo 2 automatizado (estratégia `timestamp`) sobre `stg_customers`. Rode via `dbt build`, não `dbt snapshot` isolado na primeira execução.
