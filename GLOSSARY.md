# Glossário

Termos recorrentes em Engenharia de Dados. Definições curtas para consulta
rápida; a explicação completa está no README do tópico correspondente.

> Convenção: termos técnicos consagrados são mantidos em inglês.

## A

- **ACID** — propriedades de transações: Atomicidade, Consistência, Isolamento,
  Durabilidade. Ver [transações](05-sql/08-transactions-isolation/README.md).
- **At-least-once / At-most-once / Exactly-once** — garantias de entrega em
  streaming. Ver [delivery semantics](17-streaming/04-delivery-semantics/README.md).
- **Avro** — formato de serialização *row-based* com schema embutido, comum em
  Kafka. Ver [Avro](08-data-formats/05-avro/README.md).

## B

- **Backfill** — reprocessar dados históricos de um pipeline. Ver
  [backfill](09-etl-elt/08-backfill/README.md).
- **Backpressure** — mecanismo pelo qual um consumidor lento sinaliza ao
  produtor para desacelerar.
- **Batch** — processamento de dados em lotes delimitados, por oposição a
  streaming.
- **Broadcast join** — join distribuído em que a tabela pequena é replicada a
  todos os nós. Ver [Spark joins](16-distributed-processing/10-caching-broadcast/README.md).

## C

- **CAP theorem** — em partição de rede, escolhe-se entre consistência e
  disponibilidade. Ver [CAP](01-foundations/README.md).
- **CDC (Change Data Capture)** — captura de mudanças de um banco de origem.
  Ver [CDC](09-etl-elt/06-cdc/README.md).
- **Columnar storage** — armazenamento orientado a colunas (Parquet, ORC),
  eficiente para analytics.
- **CTE (Common Table Expression)** — bloco `WITH` nomeado em SQL.

## D

- **DAG (Directed Acyclic Graph)** — grafo de tarefas sem ciclos; base de
  orquestração. Ver [DAGs](10-data-pipelines/02-dags-dependencies/README.md).
- **Data contract** — acordo versionado de schema/semântica entre produtor e
  consumidor. Ver [data contracts](29-data-contracts/README.md).
- **Data lake / warehouse / lakehouse** — ver os módulos
  [14](14-data-lake/README.md), [13](13-data-warehouse/README.md),
  [15](15-lakehouse/README.md).
- **Data mesh** — abordagem organizacional/descentralizada de dados como
  produto. Ver [advanced](30-advanced/README.md).
- **Deduplication** — remoção de registros duplicados.

## E

- **ETL / ELT** — Extract-Transform-Load vs Extract-Load-Transform. Ver
  [ETL/ELT](09-etl-elt/README.md).
- **Event time vs processing time** — quando o evento ocorreu vs quando foi
  processado. Ver [streaming](17-streaming/03-time-and-windows/README.md).

## I

- **Idempotência** — executar uma operação várias vezes produz o mesmo
  resultado de executá-la uma vez.
- **IAM** — Identity and Access Management.

## M

- **MapReduce** — modelo de computação distribuída (map → shuffle → reduce).
- **Medallion (bronze/silver/gold)** — camadas de refino em data lakes. Ver
  [medallion](14-data-lake/03-medallion-architecture/README.md).

## O

- **OLTP vs OLAP** — cargas transacionais vs analíticas.
- **ORC** — formato colunar otimizado para o ecossistema Hadoop/Hive.

## P

- **Parquet** — formato colunar amplamente usado em analytics.
- **Partitioning** — divisão de dados para paralelismo e *pruning*.

## S

- **SCD (Slowly Changing Dimension)** — estratégias para histórico de
  dimensões. Ver [SCD](07-data-modeling/10-slowly-changing-dimensions/README.md).
- **Schema evolution** — evolução compatível de schema ao longo do tempo.
- **Shuffle** — redistribuição de dados entre nós (custosa) em processamento
  distribuído.
- **Skew** — distribuição desigual de dados entre partições.
- **SLI / SLO / SLA** — indicador, objetivo e acordo de nível de serviço. Ver
  [observability](24-observability/05-sli-slo-sla/README.md).

## W

- **Watermark** — heurística de progresso do *event time* usada para fechar
  janelas em streaming.
- **Window function** — função SQL que opera sobre uma janela de linhas sem
  colapsá-las. Ver [window functions](05-sql/05-window-functions/README.md).
