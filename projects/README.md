# Projetos práticos

Dez projetos **progressivos** que consolidam os módulos teóricos em código **executável**. Cada projeto tem
seu próprio README (objetivo, arquitetura, requisitos, estrutura, execução, testes, decisões, trade-offs e
melhorias), `docker-compose` quando aplicável e testes.

> **Como usar:** faça os projetos na ordem. Cada um adiciona uma camada à anterior; o
> [Projeto 10](10-capstone/README.md) combina tudo. Leia o módulo indicado **antes**, implemente, e tente as
> "possíveis melhorias" como exercício.

## Trilha

| # | Projeto | Combina | Nível |
| --- | --- | --- | --- |
| 01 | [ETL básico](01-basic-etl/README.md) | Python + CSV/API + PostgreSQL; idempotência; quarentena | 🟢 |
| 02 | [Analytics Warehouse](02-analytics-warehouse/README.md) | modelagem dimensional + ELT + dbt + PostgreSQL | 🔵 |
| 03 | [Orquestração](03-orchestration/README.md) | Airflow; DAGs idempotentes; backfill | 🔵 |
| 04 | [Data Quality](04-data-quality/README.md) | validação + testes + quarentena + observabilidade | 🔵 |
| 05 | [Data Lake](05-data-lake/README.md) | object storage S3 (SeaweedFS local) + Parquet + partitioning + medallion | 🔵 |
| 06 | [Spark](06-spark/README.md) | processamento distribuído; shuffle/skew; tuning | 🟣 |
| 07 | [Kafka](07-kafka/README.md) | producer → Kafka → consumer → storage | 🟣 |
| 08 | [Streaming](08-streaming/README.md) | Kafka → processamento streaming → analytics | 🟣 |
| 09 | [Cloud](09-cloud/README.md) | pipeline em cloud com IaC (Terraform) e IAM mínimo | 🟣 |
| 10 | [Capstone](10-capstone/README.md) | ingestão → lakehouse → ELT → orquestração → qualidade → observabilidade → CI/CD | 🟣 |

## Mapa projeto ↔ módulos

```text
01 ─► módulos 04, 05, 09          02 ─► 05, 07, 13, 28          03 ─► 10, 11
04 ─► 12, 24                      05 ─► 08, 14, 15              06 ─► 16
07 ─► 17, 18                      08 ─► 17, 18, 30              09 ─► 19, 22, 26
10 ─► todos
```

## Convenções dos projetos

- **Código**: Python 3.11+, `ruff` + `black`, testes com `pytest`, tipagem em funções públicas
  ([convenções](../CONVENTIONS.md)).
- **Dados**: **sintéticos e gerados por script determinístico** (nenhum dado real/PII no repositório);
  amostras pequenas em `sample_data/`.
- **Ambiente**: tudo sobe com `docker compose up`; segredos de exemplo em `.env.example` (nunca `.env`).
  Se uma porta padrão estiver ocupada, os Compose aceitam sobrescrita por variável (ex.: `POSTGRES_PORT`).
- **Testes**: unitários **sem infraestrutura**; integração marcados e opcionais (`-m integration`).
- **Idempotência**: todo pipeline pode ser reexecutado sem duplicar ou corromper
  ([idempotência](../09-etl-elt/07-idempotency-retries/README.md)).

## Pré-requisitos gerais

Docker + Docker Compose, Python 3.11+, `git`. Alguns projetos têm requisitos extras (Terraform e uma conta
cloud no Projeto 09 — com opção de **emulação local** para estudar sem custo).
