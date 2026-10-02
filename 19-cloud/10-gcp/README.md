# GCP (Google Cloud Platform)

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)

## Visão geral

Nuvem do Google, forte em **dados e analytics** (origem do BigQuery, Bigtable, Spanner, Pub/Sub, Dataflow/
Beam). Stack típico: **GCS** (lake) + **BigQuery** (warehouse/lakehouse) + **Dataflow/Dataproc**
(processamento) + **Pub/Sub** (streaming) + **Composer** (Airflow) + **Dataplex** (governança).

> O foco é mapear serviços aos conceitos do repositório; consulte a documentação oficial para detalhes e
> preços atuais.

## Serviços de dados por função

| Função | Serviço | Notas |
| --- | --- | --- |
| **Object storage** | **Cloud Storage (GCS)** | classes Standard/Nearline/Coldline/Archive ([object storage](../02-object-storage/README.md)) |
| **Warehouse** | **BigQuery** | serverless, cobrança por bytes ou slots ([BigQuery](../../13-data-warehouse/05-bigquery/README.md)) |
| **Lakehouse** | **BigLake**, tabelas Iceberg no BigQuery | consultar lake com governança unificada |
| **Spark/Hadoop gerenciado** | **Dataproc** (e Serverless Spark) | [Spark](../../16-distributed-processing/README.md) |
| **Processamento batch/stream** | **Dataflow** (Apache Beam) | modelo unificado, autoscaling, exactly-once |
| **Streaming/mensageria** | **Pub/Sub**, Managed Service for Kafka | ver [brokers](../../18-message-brokers/README.md) |
| **Bancos relacionais** | **Cloud SQL**, **AlloyDB**, **Spanner** | [managed DBs](../04-managed-databases/README.md) |
| **NoSQL** | **Bigtable**, Firestore | wide-column / documento ([NoSQL](../../06-databases/04-nosql/README.md)) |
| **Orquestração** | **Cloud Composer** (Airflow), Workflows | [Airflow](../../11-orchestration/02-airflow/README.md) |
| **Transformação** | **Dataform** (SQL no BigQuery), dbt | [dbt](../../28-dbt/README.md) |
| **Catálogo/governança** | **Dataplex**, Data Catalog | metadados e qualidade |
| **CDC/migração** | **Datastream**, DMS | replicação de bancos p/ BigQuery/GCS |
| **Serverless compute** | **Cloud Run**, Cloud Functions | jobs/serviços |
| **ML** | **Vertex AI** | [DE + ML](../../31-data-engineering-and-ml/README.md) |
| **BI** | Looker, Looker Studio | |

## Arquitetura de referência

```text
Fontes ─► Datastream (CDC) / Pub/Sub / Dataflow / transfers ─► GCS (raw) e/ou BigQuery (raw)
                                                              │
                                   dbt / Dataform / Dataflow ─┤
                                                              ▼
                                                  BigQuery (staging → marts) ─► Looker
        (IAM + Dataplex + Cloud KMS + Audit Logs transversais; Composer orquestra)
```

Muitas arquiteturas GCP são **BigQuery-centric**: ingere direto (Storage Write API, load jobs de GCS) e
transforma com SQL/dbt dentro do BigQuery (padrão [ELT](../../09-etl-elt/01-etl-vs-elt/README.md)).

## Pontos de atenção

- **Custo BigQuery**: por bytes lidos — particione/clusterize, evite `SELECT *`, use dry run e
  `maximum_bytes_billed` ([otimização](../../13-data-warehouse/04-query-optimization/README.md)).
- **Dataflow**: modelo Beam (watermarks/janelas — ver [tempo e janelas](../../17-streaming/03-time-and-windows/README.md));
  ótimo p/ streaming gerenciado, com curva de aprendizado.
- **IAM**: service accounts + Workload Identity; evite chaves JSON baixadas ([IAM](../06-iam-secrets/README.md)).
- **Regiões/multi-região** do BigQuery e do GCS devem combinar (egress/latência).

## Boas práticas

- BigQuery + GCS (Parquet/Iceberg) com datasets por camada; Composer/dbt p/ orquestrar/transformar.
- Datastream p/ CDC; Dataflow/Pub/Sub p/ streaming; Dataproc Serverless p/ Spark esporádico.
- IaC (Terraform) ([IaC](../../22-infrastructure-as-code/README.md)); labels de custo e budgets.

## Equivalências rápidas

GCP ⇄ [AWS](../09-aws/README.md) ⇄ [Azure](../11-azure/README.md): GCS ⇄ S3 ⇄ ADLS · BigQuery ⇄ Redshift/Athena ⇄
Synapse · Dataflow ⇄ Managed Flink/Kinesis+Glue ⇄ Stream Analytics · Pub/Sub ⇄ SNS/SQS/Kinesis ⇄ Event
Grid/Hubs · Composer ⇄ MWAA ⇄ Data Factory · Dataplex ⇄ Glue Catalog+Lake Formation ⇄ Purview.

## Exercícios

1. Desenhe um pipeline GCP: Datastream (CDC do Postgres) → BigQuery → dbt → Looker.
2. Quando usar Dataflow vs Dataproc vs BigQuery SQL?
3. Como reduzir o custo de uma query BigQuery cara?
4. Mapeie cada serviço ao equivalente em AWS e Azure.

## Referências

- Documentação oficial do Google Cloud (cloud.google.com/docs); Architecture Framework (Data analytics).
