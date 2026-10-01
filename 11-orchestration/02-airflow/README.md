# Apache Airflow

> 🔵 Pipelines · Parte de [11 — Orquestração](../README.md)

## O que é

**Apache Airflow** é o orquestrador de workflows mais difundido do mercado. Você define
pipelines como **DAGs em Python**, e o Airflow agenda, executa, faz retry, monitora e dá uma
UI web para acompanhar tudo. Criado no Airbnb (2014), hoje é um projeto Apache maduro
(Airflow 2.x/3.x).

## Por que é tão popular

- **DAGs como código Python** — versionável, testável, dinâmico.
- **Ecossistema enorme** de *providers* (conectores para bancos, cloud, Spark, dbt...).
- **UI rica** para monitorar runs, ver logs, reexecutar, fazer backfill.
- Comunidade grande e presença em quase todo lugar (saber Airflow é empregabilidade).

## Conceitos centrais

| Conceito | O que é |
| --- | --- |
| **DAG** | o pipeline (grafo de tarefas) — ver [DAGs](../../10-data-pipelines/02-dags-dependencies/README.md) |
| **Task** | uma unidade de trabalho (uma instância de operator) |
| **Operator** | template de tarefa: `PythonOperator`, `BashOperator`, `SQLExecuteQueryOperator`... |
| **Sensor** | espera uma condição (arquivo/partição pronta) |
| **Scheduler** | processo que decide o que rodar e quando |
| **Executor** | onde as tasks rodam: Local, Celery, **Kubernetes** |
| **XCom** | troca de pequenos dados entre tarefas (não para dados grandes!) |
| **logical_date** | a partição de dados do run (ver [scheduling](../../10-data-pipelines/03-scheduling/README.md)) |

## Exemplo de DAG (TaskFlow API, Airflow 2+)

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule="0 2 * * *", start_date=datetime(2024, 1, 1),
     catchup=False, default_args={"retries": 3})
def vendas_diarias():

    @task
    def extract(logical_date=None) -> str:
        # usa a data lógica, NÃO now()
        return extrair_para_raw(data=logical_date.date().isoformat())

    @task
    def transform(path: str) -> str:
        return transformar(path)

    @task
    def load(path: str):
        carregar(path)   # idempotente (overwrite por partição)

    load(transform(extract()))

vendas_diarias()
```

## Arquitetura (componentes)

```text
Scheduler ──► decide o que rodar       Metadata DB (Postgres) ──► estado de tudo
   │                                           ▲
Workers (Executor) ──► rodam as tasks ─────────┘
Webserver ──► UI de monitoramento
```

- O **metadata DB** guarda o estado (runs, tasks, XComs). O **scheduler** lê o DAG e enfileira
  tarefas; **workers** executam; o **webserver** mostra a UI.
- **Executor** define o paralelismo: `LocalExecutor` (um host), `CeleryExecutor` (fila
  distribuída), `KubernetesExecutor` (um pod por task — elástico, ver
  [Kubernetes](../../21-kubernetes/README.md)).

## Boas práticas específicas de Airflow

- **Não processe dados grandes dentro das tasks nem via XCom** — orquestre (dispare Spark/dbt/
  SQL) e passe **referências** (caminhos), não os dados. Ver
  [conceitos](../01-orchestration-concepts/README.md).
- **Tarefas idempotentes** — retries/backfill do Airflow só são seguros assim (ver
  [idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Use a `logical_date`**, nunca `datetime.now()` — senão backfill/catchup quebram.
- **`catchup=False`** por padrão (evite disparar centenas de runs sem querer).
- **Mantenha o DAG "leve"** — o arquivo do DAG é parseado com frequência; não faça I/O/
  queries pesadas no nível do módulo.
- **Dependências entre DAGs** via *datasets* (data-aware) ou sensors, não por horário.
- **Conexões/segredos** no backend de conexões/secret manager, não hardcoded.

## Backfill e reprocessamento

A UI e a CLI (`airflow dags backfill`) permitem reprocessar intervalos. Funciona bem **se** as
tasks forem idempotentes e usarem a data lógica (ver
[backfill](../../09-etl-elt/08-backfill/README.md)).

## Rodando localmente (Docker)

O projeto oficial fornece um `docker-compose` (Airflow + Postgres + scheduler + webserver). É
como você sobe Airflow nos [projetos](../../projects/03-orchestration/README.md).

## Limitações / trade-offs

- **Orientado a tarefas** (não a assets/dados) — lineage/observabilidade de dados exigem
  extras (ver [Dagster](../03-dagster/README.md)).
- Pipelines **muito dinâmicos** (nº de tasks dependente de runtime) são mais difíceis.
- Operacionalmente **pesado** de manter self-hosted (scheduler, workers, DB) — daí os
  gerenciados (Astronomer, AWS MWAA, GCP Composer).
- Não é para **baixa latência/streaming** (é batch).

## Quando usar / quando NÃO usar

- **Use** para orquestração batch de muitos pipelines, com ecossistema amplo e time que já
  conhece Airflow.
- **Considere alternativas** se quer abordagem asset-centric nativa ([Dagster](../03-dagster/README.md)),
  fluxos muito dinâmicos ([Prefect](../04-prefect/README.md)), ou se precisa de streaming (use
  [Flink/Kafka Streams](../../17-streaming/README.md)).

## Erros comuns

- Processar/transportar dados grandes via XCom.
- `now()` em vez de `logical_date`.
- I/O pesado no topo do arquivo do DAG (sobrecarrega o scheduler).
- Catchup acidental; tasks não-idempotentes.
- Usar Airflow como cron (sem aproveitar dependências/retries/UI).

## Boas práticas (resumo)

- Orquestre, delegue a transformação; passe referências.
- Idempotência + `logical_date` + `catchup` consciente.
- DAGs leves; dependências explícitas; segredos no backend.
- Escolha o executor conforme a escala (Local/Celery/Kubernetes).

## Relação com outros conceitos

- Implementa [conceitos de orquestração](../01-orchestration-concepts/README.md),
  [DAGs](../../10-data-pipelines/02-dags-dependencies/README.md),
  [scheduling](../../10-data-pipelines/03-scheduling/README.md).
- Dispara [dbt](../../28-dbt/README.md)/[Spark](../../16-distributed-processing/README.md);
  roda em [Kubernetes](../../21-kubernetes/README.md).
- Usado no [Projeto 03](../../projects/03-orchestration/README.md).

## Exercícios

1. Escreva um DAG (TaskFlow) extract→transform→load com retries e `catchup=False`.
2. Explique por que XCom não serve para passar um DataFrame grande entre tarefas.
3. Configure uma dependência entre dois DAGs via dataset/sensor (não por horário).
4. Faça um backfill de 3 dias e explique o papel da `logical_date`.

## Referências

- Documentação oficial do Apache Airflow (airflow.apache.org).
- Astronomer — guias de boas práticas de Airflow.
