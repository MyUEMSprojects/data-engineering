# Spark avançado

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: aprofundamento de ferramenta essencial*

> Pré-requisito: [módulo 16](../../16-distributed-processing/README.md) (Spark, shuffle, Catalyst, tuning).
> Aqui, o que aparece quando os jobs ficam **grandes, caros e críticos**. Confira versões (comportamentos
> e configs mudam entre Spark 3.x e 4.x).

## 1. Entendendo a execução em profundidade

### Plano de execução e Spark UI
- `df.explain("formatted")` / `explain("cost")`: leia **plano lógico → otimizado → físico**, `Exchange`,
  `BroadcastHashJoin`/`SortMergeJoin`, `PushedFilters`, `AQE`.
- **Spark UI**: aba **SQL/DataFrame** (métricas por operador: linhas, spill, tempo), **Stages** (skew por
  distribuição de tempos de task, *shuffle read/write*), **Executors** (GC, memória), **Storage** (cache).
- **Event logs + History Server** para pós-análise; ferramentas (Dr. Elephant-like, métricas Prometheus,
  Datadog) para tendências.

### Modelo de memória (executor)
```text
Heap do executor = reservada + (spark.memory.fraction) {execução ⇄ storage (compartilhadas)} + user memory
+ memoryOverhead (off-heap: PySpark/Arrow, buffers, native)
```
- **Execução** (shuffle/join/sort/agg) e **storage** (cache/broadcast) disputam a região unificada.
- **OOM** frequentes vêm de: partições grandes/skew, `collect`, broadcast grande, **PySpark** sem
  `memoryOverhead` suficiente, UDFs/pandas UDFs com batches grandes.
- Ajuste `spark.executor.memory`, `spark.executor.memoryOverhead`, `spark.sql.shuffle.partitions`,
  `spark.sql.files.maxPartitionBytes`.

## 2. Joins avançados e skew

- **Estratégias**: broadcast hash, shuffle hash, **sort-merge**, broadcast nested loop/cartesian (evite).
  *Hints*: `/*+ BROADCAST(t) */`, `MERGE`, `SHUFFLE_HASH`, `SHUFFLE_REPLICATE_NL`.
- **AQE** (Spark 3+): coalesce de partições, **skew join** (`spark.sql.adaptive.skewJoin.*`), troca
  dinâmica de estratégia — **mantenha ligado** ([Catalyst/AQE](../../16-distributed-processing/09-catalyst-tungsten/README.md)).
- **Salting manual** quando AQE não basta; **tratar chaves quentes/NULL** separadamente; **pré-agregar** antes
  do join; **bucketing** (co-particionar tabelas pela chave de join para evitar shuffle em joins repetidos).
- **Dynamic partition pruning (DPP)**: usa o lado pequeno do join para podar partições do lado grande.
- Evite joins desnecessários: **denormalize** onde fizer sentido.

## 3. Particionamento e layout de dados

- **`repartition` vs `coalesce` vs `repartitionByRange`**; ajuste por **tamanho de partição** (~128 MB).
- **Escrita**: controle de arquivos de saída (`maxRecordsPerFile`, `repartition` antes de `partitionBy`),
  **evite over-partitioning** ([small files](../../14-data-lake/06-small-files-compaction/README.md)),
  **`sortWithinPartitions`**/**Z-order/clustering** para data skipping
  ([Delta/Iceberg](../../15-lakehouse/README.md)).
- **Compaction**: `OPTIMIZE`/`rewrite_data_files`; *auto compaction* e *optimized writes* (Delta).
- **Partition overwrite dinâmico**: `spark.sql.sources.partitionOverwriteMode=dynamic` para
  [overwrite idempotente por partição](../../09-etl-elt/04-loading/README.md).
- **Bucketing e sort buckets** para joins/agregações recorrentes (com custo de manutenção).

## 4. Agregações, windows e UDFs

- **Agregações em duas fases** (parcial → final) são automáticas em DataFrame; evite `groupByKey`/RDD manual.
- **`approx_count_distinct`/HyperLogLog**, `percentile_approx`, sketches (Datasketches) para cardinalidades/
  quantis grandes.
- **Window functions**: cuidado com **partições gigantes** (uma window sem `PARTITION BY` coloca tudo num nó).
- **UDFs**: preferir funções nativas → **pandas UDFs / Arrow** → **Scala/Java UDFs** (mais rápidas que Python
  linha-a-linha). `mapInPandas`/`applyInPandas`/`mapInArrow` para lógica por lote.
- **Evite `explode` explosivo** e `collect_list` de chaves enormes (memória).

## 5. Caching e reuso

- `persist` com **StorageLevel** adequado (`MEMORY_AND_DISK`, serializado `_SER`); `unpersist` ao terminar.
- **Checkpoint** (`checkpoint()`/`localCheckpoint()`) para **truncar lineage longa** (iterativo/ML) e reduzir
  recomputação — diferente de cache.
- **Reuse de exchange/subquery** do Catalyst; materialize intermediários caros em tabela quando reusados
  entre jobs.

## 6. Spark Structured Streaming avançado

- **Estado**: `mapGroupsWithState`/`flatMapGroupsWithState`/**`transformWithState`** (Spark 4) com TTL; **RocksDB
  state store** para estado grande (`spark.sql.streaming.stateStore.providerClass`).
- **Joins stream-stream** (watermarks nos dois lados), **stream-static**; **deduplicação** com watermark
  (`dropDuplicatesWithinWatermark`).
- **`foreachBatch` + `MERGE`** (upsert idempotente) para lakehouse; **`trigger(availableNow=True)`** para
  incremental barato.
- **Checkpoint** compatível ao evoluir a query; planejar migração de estado
  ([stateful](../../17-streaming/05-stateful-processing/README.md), [SS](../../17-streaming/08-spark-structured-streaming/README.md)).
- **Real-time mode / latência**: avalie Flink se ms importam.

## 7. Spark em produção: infraestrutura e custo

- **Cluster managers**: **Kubernetes** (cada vez mais comum: Spark Operator, pod templates, spot nodes),
  YARN, ou gerenciados (**Databricks, EMR, Dataproc**).
- **Dynamic Allocation** (`spark.dynamicAllocation.*` + **shuffle tracking** ou serviço de shuffle externo)
  para escalar executors conforme a carga.
- **Spot/preemptible**: tolerar perda de executors (shuffle recomputado; considere **push-based shuffle**/
  armazenamento remoto de shuffle, ex.: Celeborn/Uniffle) — jobs idempotentes e checkpoints.
- **Rightsizing**: relação **cores/executor** (≈4–5), memória por core, número de executors; GC (G1) e
  tuning se necessário.
- **Custo**: formatos colunares, filtros cedo, evitar shuffle, ajustar partições, desligar clusters ociosos
  ([cost](../../19-cloud/08-cost-management/README.md), [spot](../../19-cloud/03-compute/README.md)).
- **Aceleração nativa**: **Photon** (Databricks), **Velox/Gluten**, **Apache DataFusion Comet**, **NVIDIA
  RAPIDS** — vetorização nativa/GPU (avalie ganho vs compatibilidade).

## 8. Diagnóstico de problemas clássicos

| Sintoma | Causa provável | Ação |
| --- | --- | --- |
| Uma task muito mais lenta (stage "arrasta") | **skew** | AQE skew join, salting, tratar NULL/chave quente |
| `OutOfMemoryError` executor | partição grande, broadcast, `collect_list`, pouca overhead | mais partições, reduzir broadcast, `memoryOverhead`, filtrar |
| `OutOfMemoryError` driver | `collect`/`toPandas`/broadcast grande | agregar antes, escrever em vez de coletar |
| Muitos *spills* | memória insuficiente/partição grande | ↑ partições, ↑ memória, filtrar antes |
| Job lento com muitos arquivos pequenos | small files na leitura/escrita | compactar, `maxPartitionBytes`, ajustar escrita |
| Shuffle enorme | joins/groupBy sem filtro/pré-agg | pushdown, broadcast, pré-agregar, bucketing |
| Falhas "FetchFailed"/executor perdido | spot/OOM/disco do shuffle | retry, mais disco/memória, shuffle externo |
| Resultados diferentes entre runs | não determinismo (`first`, ordem, floats) | ordenar/determinismo, `ROW_NUMBER` explícito |
| Query lenta após mudar versão | planos/AQE/config mudaram | comparar `explain`, regressão de config |

## 9. Boas práticas de engenharia

- **Testes** de transformações (Spark local, dados pequenos, `chispa`/`pyspark.testing`)
  ([pipeline testing](../../10-data-pipelines/07-pipeline-testing/README.md)).
- **Idempotência** (overwrite dinâmico por partição, MERGE) e **parametrização por data**.
- **Observabilidade**: métricas de job (linhas, duração, spill), `StreamingQueryListener`, alertas
  ([observability](../../24-observability/README.md)).
- **Configuração versionada** e por ambiente; **pin de versões** (Spark/connectors).
- **Evite lógica de negócio opaca** (Python puro por linha); mantenha no Catalyst.
- **Documente decisões de tuning** (por que 400 partições? qual skew?).

## Erros comuns

- Tunar às cegas (sem Spark UI/`explain`).
- Resolver tudo aumentando memória/cluster (custo) em vez de reduzir dados/shuffle.
- Cache excessivo; `checkpoint` confundido com `cache`.
- Over-partitioning na escrita (small files) ou poucas partições (OOM).
- UDF Python por linha em dados grandes; `collect` no driver.
- Ignorar mudanças de versão (AQE/configs) ao migrar.

## Relação com outros conceitos

- [Módulo 16](../../16-distributed-processing/README.md) (fundamentos),
  [tuning](../../16-distributed-processing/11-performance-tuning/README.md),
  [Catalyst/AQE](../../16-distributed-processing/09-catalyst-tungsten/README.md),
  [Structured Streaming](../../17-streaming/08-spark-structured-streaming/README.md),
  [lakehouse](../../15-lakehouse/README.md), [Kubernetes](../../21-kubernetes/README.md).

## Exercícios

1. Dado um job com uma task 50× mais lenta que a mediana, descreva o diagnóstico e 3 correções.
2. Calcule uma configuração de executors (cores/memória) para um job de 2 TB e justifique.
3. Explique `cache` vs `checkpoint` e quando usar cada um.
4. Implemente (conceitualmente) um upsert idempotente em streaming com `foreachBatch` + `MERGE` e checkpoint.

## Referências

- Documentação do Spark (Tuning, SQL performance, AQE, Structured Streaming); Karau & Warren,
  *High Performance Spark*; Chambers & Zaharia, *Spark: The Definitive Guide*; docs de Databricks/EMR (tuning).
