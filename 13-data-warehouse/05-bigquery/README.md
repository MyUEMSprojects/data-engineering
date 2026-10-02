# BigQuery

> 🔵 Analytics Platforms · Parte de [13 — Data Warehouse](../README.md)

## O que é

**BigQuery** é o data warehouse **serverless** do Google Cloud. Você não gerencia servidores/
clusters: envia SQL e o BigQuery aloca automaticamente a capacidade de processamento. Separa
totalmente storage (colunar, no GCS internamente) de compute (slots), e é conhecido pela escala
e simplicidade operacional.

## Por que se destaca

- **Serverless** — sem cluster para provisionar/manter; escala "infinita" sob demanda.
- **Separação storage/compute** radical (ver [arquitetura](../01-concepts-architecture/README.md)).
- SQL padrão (GoogleSQL), funções analíticas ricas, suporte nativo a **arrays/structs** (dados
  aninhados — ver [JSON](../../08-data-formats/02-json-jsonl/README.md)) e a **ML no SQL**
  (BigQuery ML).
- Integração forte com o ecossistema GCP e ferramentas de BI.

## Modelo de cobrança (central para o design)

- **On-demand** — paga por **bytes processados** por query. → Reduzir bytes lidos (particionar,
  clusterizar, selecionar colunas) reduz **diretamente** a conta (ver
  [query optimization](../04-query-optimization/README.md)).
- **Capacity/slots (editions)** — paga por capacidade de compute reservada (previsível para uso
  intenso).
- **Storage** — cobrado à parte (ativo vs long-term, mais barato).

> Use **dry run** para estimar os bytes (e o custo) de uma query **antes** de rodá-la.

## Partição e clustering

```sql
CREATE TABLE ds.fct_vendas (dt DATE, uf STRING, valor NUMERIC)
PARTITION BY dt
CLUSTER BY uf, produto_id;
```

- **Partição** por data/inteiro/ingestion-time → *partition pruning*.
- **Clustering** por até 4 colunas → data skipping adicional. Ver
  [partitioning/clustering](../03-partitioning-clustering/README.md).

## Recursos úteis para DE

- **External tables / BigLake** — consultar arquivos [Parquet](../../08-data-formats/04-parquet/README.md)
  no GCS sem carregar (ponte com [data lake](../../14-data-lake/README.md)/
  [lakehouse](../../15-lakehouse/README.md), inclusive Iceberg).
- **Materialized views** (com atualização incremental automática em padrões suportados).
- **Scheduled queries** — agendamento simples de SQL.
- **Streaming inserts / Storage Write API** — ingestão em tempo quase real.
- **BigQuery ML** — treinar/servir modelos com SQL.
- Integra nativamente com [dbt](../../28-dbt/README.md).

## Carga de dados

```bash
bq load --source_format=PARQUET ds.tabela gs://bucket/dados/*.parquet
```

Ou `LOAD DATA`, Storage Write API, Dataflow, ou ferramentas de ingestão. Prefira carregar
[Parquet](../../08-data-formats/04-parquet/README.md) do [GCS](../../19-cloud/02-object-storage/README.md).

## Boas práticas específicas

- **Nunca `SELECT *`** em tabelas grandes (paga por todas as colunas).
- **Particione + clusterize** tabelas grandes; filtre pela coluna de partição diretamente.
- Use **dry run** e controle de custo (quotas, `maximum_bytes_billed`).
- Evite consultar many *small* unpartitioned tables; prefira external tables para o lake.
- Aproveite result cache (repetir query idêntica pode ser grátis).

## Trade-offs

- **Serverless** = menos controle de tuning de infra (você otimiza via SQL/partição, não via
  cluster).
- Cobrança por bytes pode **surpreender** com queries mal escritas (`SELECT *`, sem partição) —
  governe com quotas.
- *Lock-in* no GCP (mitigável com formatos abertos/external tables/Iceberg).

## Quando usar

Ótimo quando você quer **operação mínima**, escala elástica, está no GCP, e tem cargas analíticas
variáveis. A cobrança por bytes favorece cargas esporádicas; para uso muito intenso e constante,
avalie slots/editions.

## Erros comuns

- `SELECT *` e falta de partição → contas altas.
- `WHERE DATE(ts)=...` sobre coluna não particionada (sem pruning).
- Não usar dry run / não limitar `maximum_bytes_billed`.
- Carregar CSV onde Parquet seria melhor.

## Relação com outros conceitos

- Implementa [arquitetura de warehouse](../01-concepts-architecture/README.md),
  [columnar](../02-columnar-storage/README.md),
  [partition/cluster](../03-partitioning-clustering/README.md).
- Comparar com [Snowflake](../06-snowflake/README.md), [Redshift](../07-redshift/README.md).
- GCP: [cloud](../../19-cloud/10-gcp/README.md); transformação: [dbt](../../28-dbt/README.md).

## Exercícios

1. Crie uma tabela particionada por dia e clusterizada, carregue Parquet do GCS e rode uma query
   com dry run (observe os bytes).
2. Mostre a diferença de bytes entre `SELECT *` e colunas específicas.
3. Crie uma external table sobre Parquet no GCS e consulte sem carregar.
4. Configure `maximum_bytes_billed` para proteger contra queries caras.

## Referências

- Documentação oficial do BigQuery (cloud.google.com/bigquery).
