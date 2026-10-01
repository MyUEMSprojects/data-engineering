# Ferramentas de catálogo e metadados

> 🟣 Production · Parte de [27 — Catalog & Metadata](../README.md)

> Panorama para decisão — **não é endosso**. Funcionalidades, licenças e preços mudam rápido: confirme na
> documentação oficial de cada ferramenta antes de decidir.

## Panorama

| Categoria | Ferramentas |
| --- | --- |
| **Open source (plataformas de metadados)** | **DataHub**, **OpenMetadata**, **Apache Atlas**, Amundsen (mantido pela comunidade) |
| **Nativas de cloud/plataforma** | **AWS Glue Data Catalog + Lake Formation**, **Google Dataplex/Data Catalog**, **Microsoft Purview**, **Databricks Unity Catalog**, **Snowflake Horizon** |
| **Comerciais** | Collibra, Alation, Atlan, Informatica, data.world |
| **Lineage (padrão/backend)** | **OpenLineage** + **Marquez** |
| **Camada técnica do lake** | Hive Metastore, Glue, Iceberg REST/Nessie/Polaris |
| **Observabilidade de dados (com lineage)** | Monte Carlo, Elementary (dbt), Soda |

## Open source: comparação

### DataHub (LinkedIn → Acryl/DataHub Project)
- **Arquitetura**: metadados como **eventos em Kafka** (Metadata Change Proposals) + armazenamento
  (MySQL/Postgres) + **Elasticsearch** (busca) + grafo; modelo extensível (aspectos).
- **Pontos fortes**: lineage (inclusive column-level), ingestão ampla (recipes), **governança** (tags,
  termos de glossário, domínios, ownership), integração com dbt/Airflow/Spark, API/SDK, ações e eventos
  em tempo real.
- **Considerações**: infra mais pesada (Kafka, ES); curva de operação.

### OpenMetadata (Collate)
- **Arquitetura**: API unificada + armazenamento (MySQL/Postgres) + Elasticsearch; **esquema de metadados
  padronizado** (JSON Schema); conectores/ingestão via workflows (Airflow embutido/externo).
- **Pontos fortes**: UX moderna, **catálogo + lineage + qualidade de dados (testes embutidos) + observabilidade
  + glossário/governança** num produto só; menos peças que o DataHub; muitos conectores.
- **Considerações**: ecossistema/comunidade mais novos; avalie maturidade dos conectores que você precisa.

### Apache Atlas
- **Origem**: ecossistema **Hadoop** (Hive, HBase, Kafka); gerencia metadados e **classificações**/tags e
  **lineage** nesse mundo; integra com **Apache Ranger** (políticas de acesso por tag).
- **Pontos fortes**: forte em ambientes **Hadoop/on-prem**; modelo de tipos; classificação propagada por
  lineage + Ranger.
- **Considerações**: depende de JanusGraph/Solr/HBase/Kafka; UX e adoção em stacks **cloud-native/modernos**
  são menores; escolha usual quando já existe Hadoop/Cloudera.

### Amundsen
- Foco em **discovery** (busca por popularidade), projeto da Lyft; simples. Comunidade menos ativa que as
  alternativas; avalie o estado atual antes de adotar.

## Nativas de cloud / plataforma

| Ferramenta | Destaques | Quando faz sentido |
| --- | --- | --- |
| **AWS Glue Data Catalog + Lake Formation** | metastore Hive-compatível; permissões finas (tabela/coluna/linha) | stack AWS (Athena/EMR/Redshift Spectrum) ([AWS](../../19-cloud/09-aws/README.md)) |
| **Google Dataplex / Data Catalog** | descoberta automática, qualidade, lineage, governança unificada no BigQuery/GCS | stack GCP ([GCP](../../19-cloud/10-gcp/README.md)) |
| **Microsoft Purview** | catálogo, classificação, lineage, DLP, compliance | stack Azure/Fabric/Microsoft ([Azure](../../19-cloud/11-azure/README.md)) |
| **Databricks Unity Catalog** | governança + lineage (inclusive coluna) + ACLs unificados para dados e ML no lakehouse | Databricks ([Delta](../../15-lakehouse/04-delta-lake/README.md)) |
| **Snowflake Horizon** | governança nativa (tags, masking, lineage, access history) | Snowflake ([warehouse](../../13-data-warehouse/06-snowflake/README.md)) |

**Vantagem**: integração profunda, enforcement de políticas e menos operação. **Limite**: cobertura
focada no ecossistema do fornecedor (visão fim-a-fim multi-plataforma pode exigir complemento).

## Comerciais

Collibra, Alation, Atlan, Informatica: recursos de **governança corporativa** (workflows de aprovação,
glossário, políticas, stewardship), suporte e integrações — custo e *lock-in* maiores; úteis em grandes
organizações com processos formais de governança.

## Como escolher (critérios)

| Critério | Pergunta |
| --- | --- |
| **Stack** | onde estão os dados (AWS/GCP/Azure/Databricks/Snowflake/Hadoop/multi)? |
| **Escopo** | só discovery? governança + qualidade + lineage? |
| **Lineage** | precisa de **column-level** e de OpenLineage? |
| **Operação** | time para operar infra (Kafka/ES) ou prefere gerenciado/SaaS? |
| **Integrações** | dbt, Airflow, Spark, BI, Kafka, streaming |
| **Governança** | workflows de aprovação, tags→políticas (ABAC), mascaramento |
| **Custo/licença** | open source vs comercial; TCO (inclui operação) |
| **Aderência a padrões** | OpenLineage, REST catalogs, formatos abertos (evitar lock-in) |
| **Maturidade/comunidade** | atividade, roadmap, suporte |

### Recomendações pragmáticas

```text
Stack único e gerenciado (AWS/GCP/Azure/Databricks/Snowflake)      → comece pelo catálogo NATIVO + OpenLineage
Multi-plataforma, quer plataforma aberta e extensível               → DataHub ou OpenMetadata
Quer produto "tudo-em-um" simples de subir (catálogo+qualidade)     → OpenMetadata
Ecossistema Hadoop/Cloudera com Ranger                              → Apache Atlas
Grande empresa com processos formais de governança e orçamento      → Collibra/Alation/Atlan/Purview
```

> Evite escolher pelo marketing: faça uma **prova de conceito** com 1–2 domínios reais, medindo cobertura
> de conectores, qualidade do lineage, esforço de operação e adoção pelos usuários.

## Padrões e interoperabilidade (reduzindo lock-in)

- **OpenLineage** para lineage (emitir de Airflow/Spark/dbt para qualquer backend).
- **Iceberg REST Catalog / Unity Catalog OSS / Polaris / Nessie** para metadados técnicos de tabelas
  ([Iceberg](../../15-lakehouse/05-apache-iceberg/README.md)).
- **dbt** como fonte de metadados/lineage/docs ([dbt docs](../../28-dbt/07-documentation-lineage/README.md)).
- APIs/SDKs para exportar metadados; evite armazenar o conhecimento só numa ferramenta proprietária.

## Exemplo: ingestão automatizada (conceitual, DataHub)

```yaml
# recipe.yml — ingere metadados do Snowflake e do dbt
source:
  type: snowflake
  config: { account_id: "...", warehouse: "...", role: "DATAHUB_READER", include_column_lineage: true }
sink:
  type: datahub-rest
  config: { server: "http://datahub-gms:8080" }
```
```bash
datahub ingest -c recipe.yml          # agendar via orquestrador (Airflow/CronJob)
```
(Confira a sintaxe exata na documentação da versão que você usar.)

## Erros comuns

- Escolher pela marca sem prova de conceito.
- Subestimar o **custo operacional** de self-hosting (Kafka, Elasticsearch, grafo).
- Comprar suíte enterprise sem processo/donos/adoção.
- Lock-in sem exportação/padrões abertos.
- Instalar a ferramenta e esperar que "catalogue sozinha" sem curadoria.
- Ignorar permissões/RBAC do próprio catálogo (metadados também podem ser sensíveis).

## Boas práticas

- Defina requisitos e critérios; faça POC; priorize integração com dbt/orquestrador/warehouse.
- Prefira padrões abertos (OpenLineage); automatize ingestão agendada/streaming.
- Comece por tier-1; meça adoção; combine nativo + aberto quando fizer sentido.
- Trate o catálogo como produto interno (dono, roadmap, suporte).

## Relação com outros conceitos

- [Tipos de metadados](../01-metadata-types/README.md), [lineage](../02-lineage-column-lineage/README.md),
  [catálogos/discovery](../03-catalogs-discovery/README.md), [governança](../../25-data-governance/08-governance-architecture/README.md),
  [lakehouse](../../15-lakehouse/README.md), [cloud](../../19-cloud/README.md).

## Exercícios

1. Escolha uma ferramenta para: (a) startup 100% BigQuery; (b) empresa multi-cloud com Spark+dbt+Kafka;
   (c) data center Cloudera on-prem — justifique.
2. Desenhe uma POC de 2 semanas para comparar DataHub e OpenMetadata.
3. Liste 5 critérios de decisão e como medi-los na POC.
4. Explique como OpenLineage reduz lock-in e dê um exemplo de integração.

## Referências

- Documentação oficial: DataHub (datahubproject.io), OpenMetadata (open-metadata.org), Apache Atlas,
  OpenLineage/Marquez, AWS Glue/Lake Formation, Dataplex, Purview, Unity Catalog, Snowflake Horizon.
