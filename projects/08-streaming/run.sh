#!/usr/bin/env bash
# ./run.sh <demo|report|reset|produce --phase N|job>   (roda dentro do contêiner, na rede do Compose)
set -euo pipefail
cd "$(dirname "$0")"
exec docker compose run --rm app "/opt/spark/bin/spark-submit --master local[2] --driver-memory 2g --conf spark.driver.host=\$(hostname -i) /app/main.py $*"
