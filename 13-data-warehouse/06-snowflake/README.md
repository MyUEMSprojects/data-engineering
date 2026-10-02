# Snowflake

> 🔵 Analytics Platforms · Parte de [13 — Data Warehouse](../README.md)

## O que é

**Snowflake** é um data warehouse na nuvem **multi-cloud** (roda sobre AWS, GCP ou Azure), famoso
pela arquitetura que separa **storage**, **compute** e **serviços** em camadas independentes, e
pela facilidade de escalar compute de forma elástica e isolada por carga de trabalho.

## A arquitetura de três camadas

```text
┌─────────────── Cloud Services ───────────────┐  (metadados, otimizador, segurança, cache)
├─────────────── Compute (Virtual Warehouses) ─┤  (clusters elásticos e independentes)
├─────────────── Storage (object storage) ─────┤  (dados colunares, micro-partitions)
└────────────────────────────────────────────── ┘
```

- **Storage** — dados em [object storage](../../19-cloud/02-object-storage/README.md) do provedor,
  organizados em **micro-partitions** colunares (~16 MB) com min/max por coluna (data skipping
  automático — ver [columnar](../02-columnar-storage/README.md)).
- **Compute (Virtual Warehouses)** — clusters de computação **independentes**; você cria vários
  (ex.: um para ETL, um para BI), cada um escala/suspende sozinho, todos lendo o **mesmo** storage
  sem contenção.
- **Cloud Services** — otimizador, metadados, segurança, *result cache*.

## O conceito de Virtual Warehouse

Um "warehouse" no Snowflake é um **cluster de compute** (tamanhos XS, S, M, L...). Você paga por
**tempo que ele fica ativo** (créditos). Princípios:

- **Auto-suspend / auto-resume** — suspenda quando ocioso (para de cobrar) e retome na próxima
  query. **Essencial para controlar custo.**
- **Multi-cluster** — escala horizontalmente sob concorrência alta (mais clusters para filas).
- **Isolamento** — a carga de BI não compete com a de ETL (warehouses separados).

## Micro-partitions e clustering

- **Micro-partitions** são automáticas (você não as gerencia) e já dão pruning por min/max.
- **Clustering keys** reorganizam as micro-partitions por colunas de filtro frequentes em tabelas
  **muito grandes** (há *auto-clustering*). Para a maioria das tabelas, o automático basta (ver
  [partitioning/clustering](../03-partitioning-clustering/README.md)).

## Recursos úteis para DE

- **Time Travel** — consultar/restaurar dados de até N dias atrás (`AT`/`BEFORE`) → recuperação de
  erros (ver [backup/DR](../../06-databases/09-backup-recovery-dr/README.md)).
- **Zero-copy cloning** — clonar bancos/tabelas instantaneamente sem duplicar storage (ótimo para
  ambientes de dev/teste).
- **Streams & Tasks** — captura de mudanças ([CDC](../../09-etl-elt/06-cdc/README.md) interno) +
  agendamento de SQL → pipelines incrementais nativos.
- **Snowpipe** — ingestão contínua de arquivos.
- **Dynamic Tables** — tabelas declarativas que se atualizam automaticamente a partir de uma query
  (materialização incremental gerenciada).
- Suporte a **semiestruturados** (`VARIANT` para JSON) e a tabelas **Iceberg**.
- Integra nativamente com [dbt](../../28-dbt/README.md).

## Carga de dados

```sql
COPY INTO fct_vendas FROM @meu_stage/dados/ FILE_FORMAT = (TYPE = PARQUET);
```

`COPY INTO` a partir de um *stage* (object storage) é o carregador em massa; Snowpipe para
contínuo.

## Boas práticas específicas

- **Auto-suspend** agressivo nos warehouses (custo = tempo ativo).
- **Separe warehouses por carga** (ETL vs BI vs ad-hoc) para isolamento e custo claro.
- Dimensione o warehouse ao certo (tamanho maior = mais rápido e mais caro/hora — às vezes
  compensa por terminar antes).
- Use **result cache** e cuidado com *spilling* (ver [query optimization](../04-query-optimization/README.md)).
- Clustering keys só em tabelas realmente grandes.

## Trade-offs

- **Custo por compute-time** — pode escalar sem perceber; governe com auto-suspend, limites e
  monitoramento.
- Multi-cloud e abstração alta = ótima DX, mas *lock-in* (mitigável com Iceberg/formatos abertos).
- Menos "tuning de infra" que Redshift clássico (geralmente uma vantagem).

## Quando usar

Excelente para organizações que querem separação de cargas, elasticidade, multi-cloud, e recursos
como Time Travel/cloning/Streams&Tasks. Forte no [modern data stack](../../01-foundations/04-data-systems/README.md)
com dbt.

## Erros comuns

- Warehouse sem auto-suspend (queima créditos ocioso).
- Uma carga pesada competindo com BI no mesmo warehouse.
- Clusterizar tabelas pequenas sem necessidade.
- Ignorar *spilling* (warehouse subdimensionado).

## Relação com outros conceitos

- Implementa [arquitetura](../01-concepts-architecture/README.md),
  [columnar](../02-columnar-storage/README.md).
- Comparar com [BigQuery](../05-bigquery/README.md), [Redshift](../07-redshift/README.md).
- Time Travel ⇄ [DR](../../06-databases/09-backup-recovery-dr/README.md); Streams&Tasks ⇄
  [CDC/pipelines](../../09-etl-elt/06-cdc/README.md).

## Exercícios

1. Crie dois virtual warehouses (ETL e BI), configure auto-suspend e explique o isolamento.
2. Use Time Travel para recuperar uma tabela ao estado de 1 hora atrás.
3. Faça um zero-copy clone de um schema para um ambiente de teste.
4. Monte um pipeline incremental com Streams & Tasks (ou Dynamic Table).

## Referências

- Documentação oficial do Snowflake (docs.snowflake.com).
