# 13 — Data Warehouse

> 🔵 Nível 4 — Analytics Platforms · Pré: [07 — Modeling](../07-data-modeling/README.md),
> [08 — Formats](../08-data-formats/README.md) · Próximo:
> [14 — Data Lake](../14-data-lake/README.md)

Um **data warehouse** é um sistema de armazenamento otimizado para **analytics**
([OLAP](../01-foundations/07-oltp-vs-olap/README.md)): consultas agregadas sobre grandes
volumes de dados históricos e modelados. É o destino clássico dos pipelines analíticos e o
lar da [modelagem dimensional](../07-data-modeling/04-dimensional-modeling/README.md) e do
[dbt](../28-dbt/README.md).

## Por que importa

O warehouse é onde os dados de toda a organização se encontram, limpos e modelados, para BI e
análise. Entender sua arquitetura (colunar, MPP, particionamento) é o que permite consultas
rápidas e **custo controlado** — nos warehouses na nuvem, cada decisão de design vira dinheiro.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Conceitos e arquitetura](01-concepts-architecture/README.md) | O que é, MPP, separação storage/compute |
| 02 | [Columnar storage](02-columnar-storage/README.md) | Por que warehouses são colunares |
| 03 | [Partitioning e clustering](03-partitioning-clustering/README.md) | Data skipping e organização física |
| 04 | [Query optimization](04-query-optimization/README.md) | Consultas rápidas e baratas |
| 05 | [BigQuery](05-bigquery/README.md) | Warehouse serverless do GCP |
| 06 | [Snowflake](06-snowflake/README.md) | Warehouse multi-cloud |
| 07 | [Redshift](07-redshift/README.md) | Warehouse da AWS |

## Dependências internas

```text
Conceitos/arquitetura ─► Columnar storage ─► Partitioning/clustering ─► Query optimization
                                                        │
                        BigQuery / Snowflake / Redshift ┘ (implementações)
```

## Checkpoint

- [ ] Explicar o que é um data warehouse e por que não se usa um banco OLTP para isso.
- [ ] Descrever arquitetura MPP e a separação storage/compute dos warehouses na nuvem.
- [ ] Explicar por que armazenamento colunar acelera analytics.
- [ ] Usar particionamento e clustering para reduzir custo/tempo (data skipping).
- [ ] Otimizar uma query de warehouse (reduzir bytes lidos/shuffle).
- [ ] Comparar BigQuery, Snowflake e Redshift em modelo e cobrança.

## Referências do módulo

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed.
- Documentação oficial de BigQuery, Snowflake e Redshift.
- Reis & Housley, *Fundamentals of Data Engineering* — storage e serving.
