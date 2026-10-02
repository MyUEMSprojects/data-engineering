#!/usr/bin/env bash
# ./tf.sh <args do terraform>   — roda o Terraform num contêiner contra o emulador (Moto).
# Copia infra/ (somente leitura) para um volume de trabalho; o estado (terraform.tfstate) fica LÁ.
set -euo pipefail
cd "$(dirname "$0")"
exec docker compose --profile tools run --rm terraform \
  "mkdir -p /tfwork/.plugin-cache && cp -r /infra/. /tfwork/ && terraform $*"
