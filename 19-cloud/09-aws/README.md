# AWS (Amazon Web Services)

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)

## Visão geral

A maior nuvem do mercado, com o catálogo mais amplo. Para dados, um stack típico: **S3** (lake) + **Glue**
(catálogo/ETL) + **Athena/Redshift** (consulta) + **EMR/Glue** (Spark) + **MSK/Kinesis** (streaming) + **MWAA**
(Airflow) + **Lake Formation/IAM** (governança/segurança).

> Profundidade proposital: o foco é **mapear** serviços a conceitos que você já estudou; a documentação
> oficial é a referência para detalhes e preços.

## Serviços de dados por função

| Função | Serviço | Notas |
| --- | --- | --- |
| **Object storage** | **S3** | base do lake; classes, lifecycle, versioning ([object storage](../02-object-storage/README.md)) |
| **Catálogo/metadados** | **Glue Data Catalog** | metastore compatível com Hive; usado por Athena/EMR/Redshift Spectrum |
| **ETL serverless** | **AWS Glue** (Spark) | jobs Spark gerenciados, crawlers, Glue Studio |
| **Spark/Hadoop gerenciado** | **EMR** (EC2/EKS/Serverless) | clusters efêmeros; [Spark](../../16-distributed-processing/README.md) |
| **Query serverless no lake** | **Athena** (Trino/Presto) | SQL sobre S3, paga por dados lidos; suporta Iceberg |
| **Warehouse** | **Redshift** (+ Spectrum, Serverless) | ver [Redshift](../../13-data-warehouse/07-redshift/README.md) |
| **Bancos relacionais** | **RDS / Aurora** | ver [databases gerenciados](../04-managed-databases/README.md) |
| **NoSQL / cache** | **DynamoDB**, ElastiCache | key-value; Redis |
| **Streaming/mensageria** | **MSK** (Kafka), **Kinesis**, **SQS/SNS** | ver [brokers](../../18-message-brokers/README.md) |
| **Stream processing** | **Managed Flink** (Kinesis Data Analytics), EMR | [Flink](../../17-streaming/07-flink/README.md) |
| **Orquestração** | **MWAA** (Airflow), Step Functions | [Airflow](../../11-orchestration/02-airflow/README.md) |
| **Migração/CDC** | **DMS** | replicação/CDC de bancos |
| **Governança de lake** | **Lake Formation** | permissões finas em tabelas/colunas |
| **Serverless compute** | **Lambda**, Fargate | triggers por evento |
| **ML** | **SageMaker** | ver [DE + ML](../../31-data-engineering-and-ml/README.md) |
| **BI** | QuickSight | |

## Arquitetura de referência (lakehouse na AWS)

```text
Fontes ─► DMS/MSK/Kinesis/Glue ─► S3 (bronze) ─► Glue/EMR/dbt ─► S3 (silver/gold, Iceberg/Parquet)
                                                       │
                              Glue Data Catalog ◄──────┤
                                                       ▼
                                      Athena / Redshift Spectrum / EMR ─► BI (QuickSight)
              (IAM + Lake Formation + KMS + CloudTrail transversais; MWAA orquestra)
```

## Pontos de atenção

- **IAM** em tudo ([IAM](../06-iam-secrets/README.md)): roles para Glue/EMR/Athena; Lake Formation para
  permissões de coluna/linha.
- **Custo**: Athena por dados lidos (particione/Parquet); Glue por DPU-hora; EMR por instância (use spot);
  **egress/NAT** ([cost](../08-cost-management/README.md)).
- **Região única** para dado e compute; **VPC endpoints** para S3.
- Iceberg é suportado no Athena/Glue/EMR/Redshift — caminho p/ [lakehouse](../../15-lakehouse/README.md).

## Boas práticas

- S3 + Glue Catalog + Parquet/Iceberg particionado como base; Athena para ad-hoc.
- EMR/Glue efêmeros com spot; MWAA ou Step Functions para orquestrar.
- IaC (Terraform/CDK) para tudo ([IaC](../../22-infrastructure-as-code/README.md)).
- Tags e budgets desde o início.

## Equivalências rápidas

AWS ⇄ [GCP](../10-gcp/README.md) ⇄ [Azure](../11-azure/README.md): S3 ⇄ GCS ⇄ ADLS/Blob · Athena ⇄ BigQuery ⇄
Synapse serverless · EMR ⇄ Dataproc ⇄ HDInsight/Synapse Spark · MSK ⇄ Managed Kafka ⇄ Event Hubs · MWAA ⇄
Composer ⇄ Data Factory/MWAA-like.

## Exercícios

1. Desenhe um pipeline na AWS: API → S3 → Glue → Athena, citando IAM e catálogo.
2. Quando usar Athena vs Redshift vs EMR?
3. Estime como reduzir custo de Athena com Parquet + partição.
4. Mapeie cada serviço acima ao equivalente em GCP e Azure.

## Referências

- Documentação oficial AWS (docs.aws.amazon.com); AWS Well-Architected Framework (Data Analytics Lens).
