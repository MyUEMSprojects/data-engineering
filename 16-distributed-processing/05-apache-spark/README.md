# Apache Spark

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## O que é

**Apache Spark** é a engine de processamento distribuído mais usada em Data Engineering. Processa
grandes volumes de dados em memória (quando possível), de forma distribuída e tolerante a falhas, com
APIs em [Python (PySpark)](../07-pyspark/README.md), Scala, Java, R e [SQL](../06-spark-sql/README.md).
Sucedeu o [Hadoop MapReduce](../02-mapreduce/README.md) por ser mais rápido, mais rico e mais fácil de
usar.

## Por que Spark

- **Em memória** — mantém dados intermediários na RAM quando cabe (vs disco no MapReduce) → muito mais
  rápido, especialmente para pipelines iterativos.
- **Modelo rico** — DAG de operações (não só map/reduce), com APIs de alto nível
  ([DataFrame/SQL](../08-rdd-dataframe/README.md)) e um otimizador ([Catalyst](../09-catalyst-tungsten/README.md)).
- **Unificado** — batch, [streaming](../../17-streaming/08-spark-structured-streaming/README.md),
  SQL, ML (MLlib) e grafos numa só engine.
- **Tolerante a falhas** — recomputa partições perdidas via lineage.
- **Ecossistema** — lê/escreve de quase tudo (lake, warehouse, [Kafka](../../18-message-brokers/README.md),
  [lakehouse](../../15-lakehouse/README.md)).

## Arquitetura

```text
          ┌─────────────── Driver ───────────────┐
          │ SparkSession, plano, agenda as tasks  │
          └───────────────┬───────────────────────┘
                          │ (via Cluster Manager: YARN/Kubernetes/Standalone)
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   Executor 1        Executor 2        Executor 3    ← cada um roda tasks em paralelo
   (tasks + cache)   (tasks + cache)   (tasks + cache)
```

- **Driver** — o processo que roda seu programa, constrói o plano (DAG) e coordena os executors.
  Mantém o `SparkSession`.
- **Cluster Manager** — aloca recursos (YARN, **Kubernetes**, Standalone, ou Databricks).
- **Executors** — processos nos nós que executam as **tasks** e guardam dados em cache. Cada executor
  tem vários *cores* (slots de task).
- **Task** — unidade de trabalho sobre **uma partição**.

## Como um job é executado

```text
seu código (transformações lazy) ─► DAG lógico
     │ action (collect/write/count) dispara a execução
     ▼
Catalyst otimiza ─► plano físico ─► dividido em STAGES (nas fronteiras de shuffle)
     ▼
cada stage → TASKS (uma por partição) → executors rodam em paralelo
```

- **Transformations** (lazy) — `select`, `filter`, `join`, `groupBy`... **não** executam na hora;
  constroem o plano.
- **Actions** (eager) — `collect`, `count`, `write`, `show`... **disparam** a execução do plano.
- **Stages** são separadas por [shuffle](../03-partitioning-shuffle/README.md); dentro de uma stage,
  tasks rodam em pipeline.

Essa **lazy evaluation** permite ao [Catalyst](../09-catalyst-tungsten/README.md) otimizar o plano
inteiro antes de rodar.

## As APIs (do baixo ao alto nível)

- **[RDD](../08-rdd-dataframe/README.md)** — API de baixo nível (coleções distribuídas). Flexível, sem
  otimizador. Hoje raramente usada diretamente.
- **DataFrame / Dataset** — API de alto nível, tabular, **otimizada pelo Catalyst**. **Use esta.**
- **[Spark SQL](../06-spark-sql/README.md)** — SQL sobre DataFrames (mesma engine/otimizador).

> Regra: prefira **DataFrame/SQL**; só desça a RDD quando precisar de controle que a API alta não dá.

## Onde o Spark roda

- **Local** (`local[*]`) — para desenvolvimento/testes numa máquina.
- **Cluster** — YARN (Hadoop), **[Kubernetes](../../21-kubernetes/README.md)** (cada vez mais comum),
  Standalone.
- **Gerenciado** — Databricks, AWS EMR, GCP Dataproc (menos operação).

## Spark UI (sua melhor amiga)

A **Spark UI** mostra jobs, stages, tasks, durações, shuffle, cache e skew — é onde você diagnostica
performance (ver [tuning](../11-performance-tuning/README.md)). Olhe os `Exchange` (shuffles) e tasks
"fora da curva" ([skew](../04-distributed-joins-skew/README.md)).

## Spark vs alternativas (pragmatismo)

- Para dados que **cabem num servidor**, [polars](../../04-python-for-data-engineering/12-polars/README.md)/
  DuckDB costumam ser mais simples/rápidos (sem cluster).
- Spark brilha em **escala real** (TBs+), processamento distribuído, e no ecossistema
  [lakehouse](../../15-lakehouse/README.md)/Databricks.

## Erros comuns

- Usar Spark para dados pequenos (overhead de cluster sem ganho).
- `collect()` um DataFrame grande para o driver (OOM no driver!).
- Esperar que transformações rodem na hora (são lazy; precisa de action).
- Ignorar a Spark UI ao investigar lentidão.
- Usar RDD onde DataFrame (otimizado) serviria.

## Boas práticas

- Prefira DataFrame/SQL (Catalyst otimiza); evite `collect` de dados grandes.
- Entenda lazy/actions e as fronteiras de shuffle (stages).
- Dimensione executors/cores/memória ao job; ligue AQE.
- Use a Spark UI para diagnosticar; só use Spark na escala certa.

## Relação com outros conceitos

- [Fundamentos](../01-fundamentals/README.md), [MapReduce](../02-mapreduce/README.md),
  [shuffle](../03-partitioning-shuffle/README.md).
- [PySpark](../07-pyspark/README.md), [Spark SQL](../06-spark-sql/README.md),
  [RDD/DataFrame](../08-rdd-dataframe/README.md), [Catalyst](../09-catalyst-tungsten/README.md).
- Roda em [Kubernetes](../../21-kubernetes/README.md); escreve [lakehouse](../../15-lakehouse/README.md).

## Exercícios

1. Desenhe a arquitetura do Spark (driver, cluster manager, executors, tasks) e explique cada parte.
2. Diferencie transformations (lazy) de actions (eager) com exemplos.
3. Explique por que `collect()` de um DataFrame grande é perigoso.
4. Na Spark UI, o que você olharia para diagnosticar um job lento?

## Referências

- Chambers, B.; Zaharia, M. *Spark: The Definitive Guide*. O'Reilly.
- Documentação oficial do Apache Spark.
