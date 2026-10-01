# Azure

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)

## Visão geral

Nuvem da Microsoft, muito presente em empresas que já usam o ecossistema Microsoft (Entra ID/AD,
Office, SQL Server, Power BI). Para dados, o hub atual é o **Microsoft Fabric** (plataforma unificada) ao
lado de serviços clássicos: **ADLS Gen2** (lake), **Synapse**, **Data Factory**, **Databricks**, **Event
Hubs**, **Purview**.

> Foco em mapear serviços aos conceitos já vistos; a oferta de dados da Azure evolui rápido — confirme na
> documentação oficial os nomes/recursos vigentes.

## Serviços de dados por função

| Função | Serviço | Notas |
| --- | --- | --- |
| **Object storage / lake** | **Azure Blob Storage / ADLS Gen2** | namespace hierárquico, ACLs; base do lake ([object storage](../02-object-storage/README.md)) |
| **Plataforma unificada** | **Microsoft Fabric** (OneLake, Lakehouse, Warehouse, Data Factory, Real-Time) | SaaS integrado; OneLake em formato Delta |
| **Warehouse** | **Synapse (dedicated/serverless SQL)**, Fabric Warehouse | [warehouse](../../13-data-warehouse/README.md) |
| **Spark/lakehouse** | **Azure Databricks**, Synapse Spark, Fabric | [Spark](../../16-distributed-processing/README.md), [Delta](../../15-lakehouse/04-delta-lake/README.md) |
| **ETL/orquestração** | **Azure Data Factory** (e Fabric pipelines) | pipelines visuais/conectores; [orquestração](../../11-orchestration/README.md) |
| **Streaming/mensageria** | **Event Hubs** (compatível com protocolo Kafka), Service Bus, Event Grid | [brokers](../../18-message-brokers/README.md) |
| **Stream processing** | **Stream Analytics**, Fabric Real-Time, Databricks/Flink | [streaming](../../17-streaming/README.md) |
| **Bancos relacionais** | **Azure SQL**, Azure Database for PostgreSQL/MySQL | [managed DBs](../04-managed-databases/README.md) |
| **NoSQL multi-modelo** | **Cosmos DB** | consistência ajustável (5 níveis) |
| **Catálogo/governança** | **Microsoft Purview** | catálogo, lineage, classificação ([governance](../../25-data-governance/README.md)) |
| **Segredos/chaves** | **Key Vault** | [IAM/secrets](../06-iam-secrets/README.md) |
| **Identidade** | **Microsoft Entra ID** + RBAC, Managed Identities | |
| **Serverless compute** | Functions, Container Apps | |
| **ML** | Azure ML | [DE + ML](../../31-data-engineering-and-ml/README.md) |
| **BI** | **Power BI** | |

## Arquitetura de referência

```text
Fontes ─► Data Factory / Event Hubs / Fabric pipelines ─► ADLS Gen2 / OneLake (bronze)
                                                          │
                          Databricks / Synapse Spark / dbt ─┤
                                                          ▼
                              Delta (silver/gold) ─► Synapse/Fabric Warehouse ─► Power BI
        (Entra ID/RBAC + Key Vault + Purview + Monitor transversais)
```

## Pontos de atenção

- **Identidade**: Entra ID/RBAC + **Managed Identities** (sem segredos no código) — ver
  [IAM](../06-iam-secrets/README.md). ACLs do ADLS somam-se ao RBAC.
- **Delta como formato central** (Databricks/Fabric): ecossistema forte em [Delta Lake](../../15-lakehouse/04-delta-lake/README.md).
- **Fabric** unifica experiência (SaaS, capacidade compartilhada) — modelo de custo por *capacity*;
  avalie vs serviços separados.
- **Event Hubs** com endpoint Kafka facilita migração de apps Kafka.
- Integração nativa com Power BI/Microsoft 365 é um diferencial.

## Boas práticas

- ADLS Gen2 particionado (Parquet/Delta); Databricks/Synapse/Fabric conforme maturidade e orçamento.
- Managed Identities + Key Vault; Purview para catálogo/lineage.
- IaC (Terraform/Bicep) ([IaC](../../22-infrastructure-as-code/README.md)); tags e budgets (Cost Management).

## Equivalências rápidas

Azure ⇄ [AWS](../09-aws/README.md) ⇄ [GCP](../10-gcp/README.md): ADLS/Blob ⇄ S3 ⇄ GCS · Synapse/Fabric Warehouse ⇄
Redshift ⇄ BigQuery · Data Factory ⇄ Glue/MWAA ⇄ Composer · Event Hubs ⇄ MSK/Kinesis ⇄ Pub/Sub · Purview ⇄
Glue Catalog+Lake Formation ⇄ Dataplex · Key Vault ⇄ Secrets Manager ⇄ Secret Manager.

## Exercícios

1. Desenhe um pipeline Azure: Event Hubs → ADLS (Delta) → Databricks → Power BI.
2. Explique Managed Identity vs chave/segredo para acessar o ADLS.
3. Compare Fabric vs montar Synapse+Data Factory+Databricks separados.
4. Mapeie os serviços ao equivalente em AWS e GCP.

## Referências

- Documentação oficial da Azure (learn.microsoft.com/azure); Azure Architecture Center (Analytics).
