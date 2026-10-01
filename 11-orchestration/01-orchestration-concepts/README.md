# Conceitos de orquestração

> 🔵 Pipelines · Parte de [11 — Orquestração](../README.md)

## O que é

**Orquestração** é a coordenação automatizada da execução de pipelines: decidir *quando*
rodar, garantir a *ordem* das dependências, *reexecutar* o que falhou, *monitorar* e
*recuperar*. Um **orquestrador** é o sistema que faz isso — o "maestro" da plataforma de
dados.

## Por que não basta o cron

[Cron](../../02-linux-shell-environment/06-cron/README.md) só dispara comandos em horários.
Ele **não** sabe:

- que a tarefa B depende da A ter terminado com sucesso
  ([dependências/DAG](../../10-data-pipelines/02-dags-dependencies/README.md));
- como fazer **retry** com backoff de uma tarefa específica;
- como fazer **backfill** de um período histórico;
- o **estado** das execuções (o que rodou, o que falhou, há quanto tempo);
- como **alertar** e dar **observabilidade**.

Com 50 pipelines interdependentes, cron vira um emaranhado frágil. Orquestradores resolvem
isso.

## O que um orquestrador faz

| Capacidade | O que resolve |
| --- | --- |
| **Execução de DAGs** | roda tarefas na ordem das [dependências](../../10-data-pipelines/02-dags-dependencies/README.md) |
| **Scheduling** | agenda por tempo/evento/sensor; gerencia [logical date](../../10-data-pipelines/03-scheduling/README.md) |
| **Retries** | reexecuta tarefas falhas (backoff) — seguro se [idempotente](../../09-etl-elt/07-idempotency-retries/README.md) |
| **Backfill** | reprocessa [períodos históricos](../../09-etl-elt/08-backfill/README.md) |
| **Paralelismo** | roda tarefas independentes simultaneamente (com limites) |
| **Observabilidade** | status, logs, durações, alertas ([observability](../../10-data-pipelines/08-pipeline-observability/README.md)) |
| **Recuperação** | retomar do ponto de falha; reexecutar tarefas isoladas |
| **Parametrização** | passar data lógica/params às tarefas |

## Dois paradigmas de modelagem

Uma distinção conceitual importante entre orquestradores:

### Orientado a tarefas (task-centric) — ex.: Airflow

Você declara **tarefas** e suas dependências ("rode A, depois B"). O orquestrador se importa
com *o que executar e quando*. O dado produzido é um efeito colateral.

```text
extract >> transform >> load     (o foco são as TAREFAS)
```

### Orientado a dados/assets (data/asset-centric) — ex.: Dagster

Você declara os **assets de dados** (tabelas/datasets) e suas dependências de dados ("a tabela
fato depende da staging"). O orquestrador se importa com *quais dados devem existir e estar
atualizados*, e deriva a execução disso.

```text
dim_cliente ─┐
             ├─► fct_vendas     (o foco são os DADOS/ASSETS)
stg_pedidos ─┘
```

A visão *asset-centric* alinha-se melhor com [lineage](../../10-data-pipelines/06-data-lineage/README.md),
*data-aware scheduling* e observabilidade de dados — uma tendência moderna. Ambos os modelos
executam DAGs por baixo.

## Conceitos-chave (independentes de ferramenta)

- **DAG** — o grafo de tarefas/assets (ver [DAGs](../../10-data-pipelines/02-dags-dependencies/README.md)).
- **Task/Operator** — a unidade de trabalho (rodar SQL, chamar API, disparar Spark).
- **Schedule/Trigger** — o que inicia uma execução.
- **Logical/execution date** — a partição de dados que o run representa (ver
  [scheduling](../../10-data-pipelines/03-scheduling/README.md)).
- **Sensor** — espera uma condição (dado pronto) antes de prosseguir.
- **Retry/backoff, SLA, pool/concurrency** — resiliência e controle de recursos.
- **Executor/worker** — onde as tarefas de fato rodam (local, Celery, Kubernetes).

## Orquestração vs transformação (não confunda)

O orquestrador **coordena**; ele não **transforma** os dados (isso é
[dbt](../../28-dbt/README.md)/[Spark](../../16-distributed-processing/README.md)/SQL). O
orquestrador *dispara* a transformação na ordem certa, faz retry e monitora. Misturar lógica
de transformação pesada dentro de tarefas do orquestrador (em vez de delegar) é um
antipadrão comum.

## O pré-requisito: idempotência

Retries, backfill e recuperação só são seguros se as tarefas forem
[idempotentes](../../09-etl-elt/07-idempotency-retries/README.md). O orquestrador dá o
mecanismo; a idempotência dá a segurança.

## Erros comuns

- Colocar lógica de transformação pesada dentro do orquestrador em vez de delegar.
- Tarefas não-idempotentes → retries/backfill duplicam.
- Dependências por horário em vez de por sucesso/dados (ver
  [scheduling](../../10-data-pipelines/03-scheduling/README.md)).
- Usar orquestrador como cron glorificado (sem aproveitar dependências/observabilidade).
- Um DAG monstro com tudo acoplado.

## Boas práticas

- Orquestre, não transforme: delegue a SQL/dbt/Spark.
- Tarefas idempotentes e parametrizadas por data lógica.
- Dependências explícitas (DAG), retries e SLAs configurados.
- Observabilidade e alertas desde o início.

## Relação com outros conceitos

- Implementações: [Airflow](../02-airflow/README.md), [Dagster](../03-dagster/README.md),
  [Prefect](../04-prefect/README.md).
- [DAGs](../../10-data-pipelines/02-dags-dependencies/README.md),
  [scheduling](../../10-data-pipelines/03-scheduling/README.md),
  [idempotência](../../09-etl-elt/07-idempotency-retries/README.md).
- Evolui do [cron](../../02-linux-shell-environment/06-cron/README.md).

## Exercícios

1. Liste 5 coisas que um orquestrador faz e o cron não.
2. Diferencie o paradigma task-centric do asset-centric com um exemplo.
3. Explique por que a orquestração depende de tarefas idempotentes.
4. Dê um exemplo de lógica que **não** deveria estar dentro do orquestrador.

## Referências

- Reis & Housley, *Fundamentals of Data Engineering* — orquestração.
- Documentação de Airflow, Dagster e Prefect (conceitos).
