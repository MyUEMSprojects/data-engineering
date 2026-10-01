#!/usr/bin/env bash
# Atalho: ./run.sh <comando do sparkjobs>  (ex.: ./run.sh bench --only e3)
# Variáveis: SPARK_MASTER (padrão local[4]), DRIVER_MEM (padrão 4g)
set -euo pipefail
cd "$(dirname "$0")"
exec docker compose run --rm spark \
  "/opt/spark/bin/spark-submit --master ${SPARK_MASTER:-local[4]} --driver-memory ${DRIVER_MEM:-4g} --conf spark.driver.host=\$(hostname -i) /app/main.py $*"
