# Medallion architecture (Bronze/Silver/Gold)

> 🔵 Analytics Platforms · Parte de [14 — Data Lake](../README.md)

## O que é

A **arquitetura medallion** organiza um data lake/[lakehouse](../../15-lakehouse/README.md) em
**camadas de refino progressivo**, nomeadas por metais: **Bronze** (bruto), **Silver** (limpo) e
**Gold** (modelado/agregado para consumo). Cada camada tem uma responsabilidade clara, tornando o
lake compreensível e evitando o [data swamp](../01-concepts/README.md).

```text
Fontes ─► 🥉 Bronze (raw) ─► 🥈 Silver (clean) ─► 🥇 Gold (business) ─► BI / ML
           como chegou        limpo/tipado/dedup    modelado/agregado
```

## Por que existe

Jogar tudo bruto num lake sem organização gera caos. Jogar tudo já modelado perde o bruto (não dá
para reprocessar). A medallion resolve com **camadas e contratos** entre elas — *separation of
concerns* aplicado a dados, permitindo reprocessar, auditar e evoluir cada camada
independentemente.

## As camadas

### 🥉 Bronze (raw / landing)

- Dados **exatamente como chegaram** da fonte (sem transformação, ou mínima: adicionar metadados de
  ingestão como timestamp/fonte).
- **Imutável e append-only** — a fonte da verdade do que foi recebido.
- Permite **reprocessar** tudo a jusante sem re-extrair (ver
  [backfill](../../09-etl-elt/08-backfill/README.md), [ingestão](../../09-etl-elt/02-ingestion-extraction/README.md)).
- Formato: o original (JSON/CSV) e/ou [Parquet](../../08-data-formats/04-parquet/README.md);
  particionado por data de ingestão.

### 🥈 Silver (cleansed / conformed)

- Dados **limpos, tipados, deduplicados, validados** e padronizados (ver
  [transformação](../../09-etl-elt/03-transformation/README.md),
  [dedupe](../../09-etl-elt/09-deduplication/README.md),
  [validação](../../09-etl-elt/10-data-validation/README.md)).
- Schema aplicado; fontes integradas/conformadas; uma "versão confiável" dos dados.
- Ainda relativamente **granular** (nível de detalhe), não necessariamente agregado.
- É onde a maior parte do trabalho de qualidade acontece.

### 🥇 Gold (curated / business)

- Dados **modelados para consumo**: tabelas [dimensionais](../../07-data-modeling/04-dimensional-modeling/README.md)
  (fatos/dimensões), métricas de negócio, agregações.
- Otimizado para [BI](../../13-data-warehouse/README.md), relatórios e
  [features de ML](../../31-data-engineering-and-ml/README.md).
- O que os consumidores finais usam.

## Por que camadas ajudam

- **Reprocessamento** — bug no silver/gold? reprocessa a partir do bronze (sem re-extrair).
- **Separação de responsabilidades** — ingestão (bronze), qualidade (silver), negócio (gold).
- **Auditoria/lineage** — rastrear do gold até o bronze (ver
  [lineage](../../10-data-pipelines/06-data-lineage/README.md)).
- **Contratos entre camadas** — cada camada entrega um "produto" para a próxima.
- **Reuso** — várias tabelas gold podem derivar do mesmo silver.

## Relação com staging/marts (dbt)

As camadas mapeiam diretamente para a convenção de [dbt](../../28-dbt/README.md):

```text
Bronze  ≈  sources / raw
Silver  ≈  staging (stg_) + intermediate (int_)
Gold    ≈  marts (fct_/dim_)
```

É o mesmo conceito com nomes diferentes (ver [ETL vs ELT](../../09-etl-elt/01-etl-vs-elt/README.md)).

## Implementação

- Cada camada é um conjunto de tabelas/diretórios, construídos por
  [transformações](../../09-etl-elt/03-transformation/README.md) idempotentes
  ([Spark](../../16-distributed-processing/README.md)/[dbt](../../28-dbt/README.md)/SQL),
  orquestradas por um [DAG](../../10-data-pipelines/02-dags-dependencies/README.md) (bronze →
  silver → gold).
- Num [lakehouse](../../15-lakehouse/README.md), cada camada são tabelas Delta/Iceberg/Hudi (com
  ACID/time travel).
- Partição por data; controle de [small files](../06-small-files-compaction/README.md).

## Variações

- Nem todo projeto precisa das 3 camadas rígidas; o importante é o **princípio** (bruto preservado
  → refinado → consumo). Alguns adicionam camadas (ex.: "platinum" para agregações específicas) ou
  colapsam silver/gold em projetos simples. Use julgamento (KISS).

## Erros comuns

- Pular o bronze (transformar na ingestão) → não dá para reprocessar.
- Misturar responsabilidades (modelagem de negócio no silver, dados sujos no gold).
- Tratar como dogma 3-camadas quando 2 bastam (over-engineering) — ou nenhuma camada (swamp).
- Camadas sem contratos/qualidade entre si.

## Boas práticas

- **Bronze imutável** preservando o bruto; qualidade no **silver**; negócio no **gold**.
- Transformações idempotentes, por partição; orquestradas em DAG.
- Contratos e testes entre camadas; lineage rastreável.
- Ajuste o número de camadas ao projeto.

## Relação com outros conceitos

- [Transformação](../../09-etl-elt/03-transformation/README.md),
  [ETL/ELT](../../09-etl-elt/01-etl-vs-elt/README.md),
  [dbt](../../28-dbt/README.md), [lakehouse](../../15-lakehouse/README.md).
- [Data lake/swamp](../01-concepts/README.md),
  [lineage](../../10-data-pipelines/06-data-lineage/README.md).

## Exercícios

1. Desenhe as 3 camadas para um pipeline de e-commerce, dizendo o que vive em cada uma.
2. Explique por que preservar o bronze facilita corrigir um bug no gold.
3. Mapeie as camadas para as convenções de dbt (sources/staging/marts).
4. Dê um caso em que 2 camadas bastam e outro em que uma 4ª faria sentido.

## Referências

- Databricks — Medallion architecture (documentação).
- Kimball, R. *The Data Warehouse Toolkit* (modelagem na camada gold).
