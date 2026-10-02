# Metadata (no data lake)

> 🔵 Analytics Platforms · Parte de [14 — Data Lake](../README.md)

## O que é

**Metadados** são "dados sobre os dados": o que existe no lake, onde está, qual o schema, como está
particionado, de onde veio. Como o [object storage](../02-object-storage/README.md) é só um monte
de arquivos num namespace plano, **sem uma camada de metadados o lake é ilegível** — engines e
pessoas não sabem que "aqueles arquivos Parquet formam a tabela `vendas` com tal schema". Esta é a
diferença técnica entre um lake e um [data swamp](../01-concepts/README.md).

> Este tópico cobre o metadado **técnico** que torna o lake consultável. O metadado de negócio,
> discovery e catálogos corporativos estão em [27 — Catalog & Metadata](../../27-data-catalog-metadata/README.md).

## Tipos de metadado relevantes no lake

- **Técnico** — schema (colunas/tipos), partições, localização dos arquivos, estatísticas
  (min/max, contagens), formato. É o que uma engine precisa para consultar.
- **Operacional** — quando foi carregado, por qual job, nº de linhas (ver
  [ingestão](../../09-etl-elt/02-ingestion-extraction/README.md),
  [observabilidade](../../10-data-pipelines/08-pipeline-observability/README.md)).
- **De negócio** — significado, dono, classificação (ver
  [governança](../../25-data-governance/README.md)).

## Hive Metastore: o catálogo técnico clássico

O **Hive Metastore (HMS)** é o padrão histórico: um banco de dados que mapeia **"tabelas lógicas" →
localização + schema + partições** dos arquivos no lake. Com ele, uma engine (Spark, Trino,
Presto, Hive) consulta `SELECT * FROM vendas` sem saber os caminhos físicos.

```text
Metastore:  tabela "vendas" → s3://.../lake/vendas/, schema (dt, uf, valor), partições [dt=...]
Engine (Trino/Spark):  "SELECT ... FROM vendas WHERE dt='...'"  → usa o metastore p/ achar os arquivos + pruning
```

Alternativas/sucessores: **AWS Glue Data Catalog** (HMS gerenciado na AWS), catálogos de cloud
(BigQuery, Unity Catalog da Databricks).

## O problema do "só arquivos + metastore"

Um lake cru = arquivos + metastore apontando para eles. Isso funciona, mas tem limites sérios:

- **Sem transações/ACID** — escrever arquivos e atualizar o metastore não é atômico → leituras
  podem ver estado parcial.
- **Partições gerenciadas à parte** — adicionar/remover arquivos exige sincronizar o metastore
  (`MSCK REPAIR`, partições "fantasma").
- **Sem time travel, sem schema enforcement robusto**, sem *upserts* eficientes.
- **Listagem cara** para descobrir arquivos/partições.

## A evolução: metadados de tabela (table formats)

Os **table formats** do [lakehouse](../../15-lakehouse/README.md) —
[Iceberg](../../15-lakehouse/05-apache-iceberg/README.md),
[Delta](../../15-lakehouse/04-delta-lake/README.md),
[Hudi](../../15-lakehouse/06-apache-hudi/README.md) — resolvem isso trazendo uma **camada de
metadados rica** junto dos dados:

- Um **manifesto/log** que lista exatamente **quais arquivos** compõem a tabela em cada **versão**
  (snapshot) → commits atômicos, time travel.
- **Estatísticas por arquivo** para *data skipping* eficiente (sem depender só de partições).
- **Schema e partition spec versionados** (evolução segura).

Ou seja: o metadado deixa de ser "um metastore apontando para um diretório" e passa a ser um
**log transacional** que define a tabela. É o que torna o lakehouse possível.

```text
Lake cru:    metastore → "diretório X"  (engine lista arquivos; sem ACID)
Lakehouse:   metadata log → "a tabela na versão N = estes arquivos exatos"  (ACID, time travel)
```

## Por que o DE deve ligar para isso

- **Descoberta** — sem metadados, ninguém acha/usa os dados (swamp).
- **Performance** — estatísticas de metadados habilitam *data skipping* além das partições.
- **Confiabilidade** — metadados transacionais (lakehouse) evitam leituras de estado parcial.
- **Lineage/governança** — metadados alimentam [catálogo](../../27-data-catalog-metadata/README.md)
  e [lineage](../../10-data-pipelines/06-data-lineage/README.md).

## Erros comuns

- Lake só com arquivos, sem catálogo/metastore → ninguém sabe o que existe (swamp).
- Depender de `MSCK REPAIR`/sincronização manual de partições (fonte de bugs).
- Esperar ACID/time travel de um lake cru (precisa de table format).
- Ignorar estatísticas de metadados (perde data skipping).

## Boas práticas

- Catalogue toda tabela do lake (HMS/Glue/catálogo da plataforma).
- Prefira **table formats** ([Iceberg/Delta/Hudi](../../15-lakehouse/README.md)) para metadados
  ricos, ACID e time travel.
- Registre metadados operacionais (carga, contagens) para observabilidade.
- Integre com [catálogo de dados](../../27-data-catalog-metadata/README.md) para discovery/negócio.

## Relação com outros conceitos

- Base do [lakehouse](../../15-lakehouse/README.md) e seus
  [table formats](../../15-lakehouse/05-apache-iceberg/README.md).
- [Catálogo/lineage](../../27-data-catalog-metadata/README.md),
  [partitioning](../05-partitioning/README.md), [object storage](../02-object-storage/README.md).

## Exercícios

1. Explique por que um lake de arquivos é ilegível sem uma camada de metadados.
2. Descreva o papel do Hive Metastore numa consulta do Trino sobre o lake.
3. Liste 3 limitações de "arquivos + metastore" que os table formats resolvem.
4. Explique como o metadado de um lakehouse habilita time travel e commits atômicos.

## Referências

- Documentação do Hive Metastore e AWS Glue Data Catalog.
- Apache Iceberg / Delta Lake — especificações de metadados.
- Reis & Housley, *Fundamentals of Data Engineering* — metadados.
