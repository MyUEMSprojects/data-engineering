# Conceitos de Data Lake

> 🔵 Analytics Platforms · Parte de [14 — Data Lake](../README.md)

## O que é

Um **data lake** é um repositório que armazena **grandes volumes de dados em formato bruto** —
estruturados (tabelas), semiestruturados ([JSON](../../08-data-formats/02-json-jsonl/README.md),
logs) e não-estruturados (imagens, texto, áudio) — tipicamente sobre
[object storage](../02-object-storage/README.md) barato. A ideia central: **armazenar tudo agora,
decidir como usar depois** ([schema-on-read](../04-schema-on-read-write/README.md)).

## Por que existe / que problema resolve

O [data warehouse](../../13-data-warehouse/README.md) é ótimo para dados estruturados e modelados,
mas:

- Exige schema definido **na entrada** (schema-on-write) — ruim para dados variáveis/brutos.
- Storage é mais caro.
- Não lida bem com dados não-estruturados (imagens, texto para ML).

O lake resolve: aceita **qualquer formato**, custa pouco (object storage), preserva o **bruto**
(para reprocessar/auditar) e serve dados a [Spark](../../16-distributed-processing/README.md), ML
e ao próprio warehouse.

## Características

- **Armazena bruto** — o dado como chegou, sem transformação obrigatória.
- **Schema-on-read** — a estrutura é interpretada na leitura, não imposta na escrita (ver
  [schema-on-read/write](../04-schema-on-read-write/README.md)).
- **Barato e escalável** — object storage (S3/GCS/ADLS) a centavos por GB.
- **Desacoplado** — storage separado de qualquer engine; muitos motores lêem os mesmos arquivos.
- **Formatos abertos** — [Parquet](../../08-data-formats/04-parquet/README.md)/
  [Avro](../../08-data-formats/05-avro/README.md)/JSON/CSV (sem lock-in de formato).

## Lake vs Warehouse

| | Data Lake | [Warehouse](../../13-data-warehouse/README.md) |
| --- | --- | --- |
| Dados | brutos, qualquer formato | modelados, estruturados |
| Schema | on-read | on-write |
| Custo de storage | baixo | maior |
| Otimizado para | guardar tudo, ML, big data | SQL analítico rápido |
| Governança/qualidade | mais frágil (precisa esforço) | mais forte |
| Transações/ACID | não (cru) | sim |

Não são rivais: muitas arquiteturas usam **lake + warehouse** (o lake guarda o bruto/ML; o
warehouse serve o analítico modelado), ou um [lakehouse](../../15-lakehouse/README.md) que une os
dois.

## O risco: data swamp (pântano de dados)

Sem organização e governança, um lake vira um **data swamp**: um amontoado de arquivos que ninguém
sabe o que são, de onde vieram ou se são confiáveis. É o fracasso clássico de data lakes. Evitar
exige:

- **Organização** em camadas ([medallion](../03-medallion-architecture/README.md)).
- **[Metadados/catálogo](../07-metadata/README.md)** — saber o que existe.
- **[Qualidade](../../12-data-quality/README.md)** e **[governança](../../25-data-governance/README.md)**.
- **[Partitioning](../05-partitioning/README.md)** e controle de
  [small files](../06-small-files-compaction/README.md).

> Um lake sem governança não é um ativo — é um passivo. Disciplina é o que separa "lake" de
> "swamp".

## O que vive num lake

- **Dados brutos** de todas as fontes (camada bronze) — a fonte para reprocessar.
- **Dados refinados** intermediários (silver) e às vezes agregados (gold).
- **Dados para ML** (datasets de treino, features, embeddings).
- **Não-estruturados** (imagens, texto) que não cabem no warehouse.

## Como se acessa

- **Engines de processamento** — [Spark](../../16-distributed-processing/README.md), Flink, Trino/
  Presto, DuckDB, [polars](../../04-python-for-data-engineering/12-polars/README.md) lendo
  Parquet.
- **Query federada** — warehouses consultam o lake (BigQuery external tables, Redshift Spectrum,
  Athena).
- **Lakehouse** — camada de tabela ([Delta/Iceberg/Hudi](../../15-lakehouse/README.md)) traz
  SQL/ACID sobre o lake.

## Erros comuns

- Virar data swamp (sem organização/catálogo/governança).
- Jogar tudo bruto sem camadas (ninguém acha/confia nos dados).
- Milhões de arquivos pequenos ([small files](../06-small-files-compaction/README.md)).
- Esperar transações/qualidade de warehouse num lake cru (precisa de lakehouse para isso).

## Boas práticas

- Organize em camadas ([medallion](../03-medallion-architecture/README.md)) com contratos.
- Catalogue e governe desde o início (evite o swamp).
- Particione, use Parquet, controle small files.
- Para ACID/updates/SQL robusto, use [lakehouse](../../15-lakehouse/README.md) por cima.

## Relação com outros conceitos

- [Object storage](../02-object-storage/README.md),
  [medallion](../03-medallion-architecture/README.md),
  [formats/Parquet](../../08-data-formats/04-parquet/README.md).
- [Warehouse](../../13-data-warehouse/README.md),
  [lakehouse](../../15-lakehouse/README.md), [Spark](../../16-distributed-processing/README.md).

## Exercícios

1. Explique 3 motivos para ter um data lake além do warehouse.
2. Descreva como um lake vira data swamp e 4 práticas para evitá-lo.
3. Compare lake vs warehouse em schema, custo e governança.
4. Dê um caso de dado que faz mais sentido no lake que no warehouse.

## Referências

- Reis & Housley, *Fundamentals of Data Engineering* — storage.
- Armbrust et al. "Lakehouse" (Databricks) — contexto.
