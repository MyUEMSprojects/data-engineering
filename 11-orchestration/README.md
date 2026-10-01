# 11 — Orquestração

> 🔵 Nível 3 — Pipelines · Pré: [10 — Data Pipelines](../10-data-pipelines/README.md) ·
> Próximo: [12 — Data Quality](../12-data-quality/README.md)

**Orquestração** é coordenar a execução de pipelines: *quando* rodar, em *que ordem*, com
*retries*, *monitoramento* e *recuperação*. É o que transforma um conjunto de scripts em uma
plataforma de dados operável. Este módulo trata primeiro os **conceitos** e depois as
**ferramentas** — porque a ferramenta é só a implementação de ideias que você já viu em
[DAGs](../10-data-pipelines/02-dags-dependencies/README.md) e
[scheduling](../10-data-pipelines/03-scheduling/README.md).

## Por que existe

[Cron](../02-linux-shell-environment/06-cron/README.md) agenda, mas não gerencia
dependências, retries, backfill, observabilidade nem estado. Quando você tem dezenas de
pipelines interdependentes rodando todo dia, precisa de um orquestrador: um sistema que
executa [DAGs](../10-data-pipelines/02-dags-dependencies/README.md), lida com falhas e dá
visibilidade.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Conceitos de orquestração](01-orchestration-concepts/README.md) | O que um orquestrador faz e por quê |
| 02 | [Apache Airflow](02-airflow/README.md) | O orquestrador mais difundido |
| 03 | [Dagster](03-dagster/README.md) | Orquestração orientada a assets/dados |
| 04 | [Prefect](04-prefect/README.md) | Orquestração "pythônica" e dinâmica |
| 05 | [Escolhendo um orquestrador](05-choosing-an-orchestrator/README.md) | Trade-offs e decisão |

## Dependências internas

```text
Conceitos de orquestração ─► Airflow
                           ├─► Dagster
                           └─► Prefect
                                 │
                                 ▼
                     Escolhendo um orquestrador
```

## Checkpoint

- [ ] Explicar o que um orquestrador faz além do cron (dependências, retries, backfill,
      observabilidade).
- [ ] Modelar um pipeline como DAG num orquestrador e configurar retries/schedule.
- [ ] Diferenciar a abordagem de **tarefas** (Airflow) da de **assets/dados** (Dagster).
- [ ] Executar um backfill e entender a *logical date*.
- [ ] Escolher um orquestrador justificando pelos trade-offs do contexto.

## Referências do módulo

- Documentação oficial de Airflow, Dagster e Prefect.
- Reis & Housley, *Fundamentals of Data Engineering* — orquestração.
