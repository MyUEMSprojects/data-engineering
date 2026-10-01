# Apache Hudi

> 🔵 Analytics Platforms · Parte de [15 — Lakehouse](../README.md)

## O que é

**Apache Hudi** (Hadoop Upserts Deletes and Incrementals) é um *table format* open source (criado no
Uber, hoje Apache) para lakehouse, com **foco histórico em upserts eficientes, deletes e consumo
incremental** — ideal para cenários de [CDC](../../09-etl-elt/06-cdc/README.md) e dados que mudam
muito. É o terceiro grande formato, junto de [Delta](../04-delta-lake/README.md) e
[Iceberg](../05-apache-iceberg/README.md).

## Por que surgiu

O Uber precisava **ingerir mudanças (upserts/deletes) continuamente** em tabelas enormes no lake e
**consumir só o que mudou** (incremental), de forma eficiente — algo que o lake cru e o formato Hive
não faziam bem. Hudi nasceu para resolver *mutable data* + *incremental processing* no lake.

## Os dois table types (a decisão central do Hudi)

Hudi oferece dois modos de armazenamento, com trade-offs opostos entre custo de escrita e de leitura:

### Copy-on-Write (CoW)

Ao fazer upsert, **reescreve** os arquivos Parquet afetados imediatamente.

- Leitura **rápida** (só Parquet colunar).
- Escrita **mais cara** (reescreve arquivos a cada update).
- Bom quando há **mais leitura que escrita**.

### Merge-on-Read (MoR)

Grava as mudanças em **log files (delta logs)** e as **mescla na leitura**; a compaction consolida os
logs em Parquet depois.

- Escrita **rápida** (append em logs) — ótimo para ingestão/CDC de alta frequência.
- Leitura **mais cara** (precisa mesclar base + logs), a menos que compactado.
- Bom quando há **muita escrita/updates** e baixa latência de ingestão.

```text
CoW:  upsert → reescreve Parquet          (leitura rápida, escrita cara)
MoR:  upsert → append em log → compaction  (escrita rápida, leitura mescla logs)
```

## Recursos

- **Upserts/Deletes** eficientes por **record key** (+ precombine key para resolver duplicatas).
- **Incremental queries** — consumir apenas os registros que mudaram desde um commit (pull
  incremental nativo) → pipelines incrementais poderosos.
- **ACID** via timeline de commits; snapshot/time travel.
- **Indexes** (Bloom, record-level) para localizar rapidamente os arquivos de um record key em
  upserts.
- **Compaction, clustering e cleaning** gerenciados.
- Integração com Spark, Flink, Presto/Trino, Hive.

## Exemplo (Spark, conceitual)

```python
(df.write.format("hudi")
   .option("hoodie.table.name", "vendas")
   .option("hoodie.datasource.write.recordkey.field", "id")
   .option("hoodie.datasource.write.precombine.field", "updated_at")
   .option("hoodie.datasource.write.table.type", "MERGE_ON_READ")   # ou COPY_ON_WRITE
   .option("hoodie.datasource.write.operation", "upsert")
   .mode("append").save("s3://bucket/lake/vendas"))
```

## Pontos fortes

- **Upserts/CDC de alta frequência** — o caso de uso onde mais brilha (MoR).
- **Incremental queries nativas** — consumir deltas facilmente.
- Indexação por record key para upserts rápidos em tabelas grandes.

## Trade-offs / limitações

- **Mais opções/complexidade de configuração** (table type, index, precombine, compaction) — curva
  de aprendizado maior.
- MoR exige gerenciar **compaction** para não degradar leituras.
- Menos "neutralidade de engine" e tração de convergência que o
  [Iceberg](../05-apache-iceberg/README.md) atualmente; forte no ecossistema Spark/Flink.

## Quando usar

- Ingestão/**CDC** contínuo com muitos **upserts/deletes** e necessidade de **baixa latência de
  escrita** (MoR).
- Pipelines que consomem **incrementalmente** o que mudou.
- Quando a mutabilidade frequente é o requisito dominante.

## Delta vs Iceberg vs Hudi (resumo)

| | [Delta](../04-delta-lake/README.md) | [Iceberg](../05-apache-iceberg/README.md) | Hudi |
| --- | --- | --- | --- |
| Forte em | ecossistema Spark/Databricks, CDF | neutralidade de engine, convergência | **upserts/CDC/incremental** |
| Table types | — | — | **CoW / MoR** |
| Complexidade | menor | média | **maior** (mais tuning) |

Não há vencedor universal. Regra prática: **Iceberg** para neutralidade/convergência, **Delta** se
você vive no Spark/Databricks, **Hudi** se o caso é upsert/CDC intensivo de baixa latência.

## Erros comuns

- Usar MoR sem agendar compaction → leituras lentas (logs acumulados).
- Escolher CoW para ingestão de alta frequência (escritas caras).
- Record/precombine keys mal definidos → upserts/dedupe incorretos.
- Subestimar a complexidade de configuração.

## Boas práticas

- Escolha CoW (leitura-pesada) vs MoR (escrita/CDC-pesada) conforme a carga.
- Defina record key + precombine key com cuidado.
- Agende compaction (MoR), clustering e cleaning.
- Use incremental queries para pipelines downstream eficientes.

## Relação com outros conceitos

- [ACID sobre object storage](../03-acid-on-object-storage/README.md),
  [CDC](../../09-etl-elt/06-cdc/README.md),
  [incremental](../../09-etl-elt/05-full-vs-incremental/README.md),
  [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md).
- Compara com [Delta](../04-delta-lake/README.md) e [Iceberg](../05-apache-iceberg/README.md).

## Exercícios

1. Explique a diferença CoW vs MoR e dê um caso de uso para cada.
2. Configure um upsert Hudi com record key e precombine key.
3. Descreva uma query incremental (consumir só o que mudou desde um commit) e seu uso num pipeline.
4. Compare Hudi, Delta e Iceberg para um pipeline de CDC de alta frequência.

## Referências

- Documentação oficial do Apache Hudi (hudi.apache.org).
