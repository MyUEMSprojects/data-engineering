# 15 — Lakehouse

> 🔵 Nível 4 — Analytics Platforms · Pré: [13 — Warehouse](../13-data-warehouse/README.md),
> [14 — Lake](../14-data-lake/README.md) · Próximo:
> [28 — dbt](../28-dbt/README.md)

Um **lakehouse** combina o melhor dos dois mundos: o **custo e a flexibilidade do
[data lake](../14-data-lake/README.md)** (object storage, formatos abertos, qualquer dado) com a
**confiabilidade e performance do [data warehouse](../13-data-warehouse/README.md)**
(ACID, schema, SQL rápido, time travel). Tecnicamente, é uma **camada de tabela transacional**
(table format) sobre arquivos [Parquet](../08-data-formats/04-parquet/README.md) no lake.

## Por que importa

Antes, você precisava de **dois** sistemas: lake (bruto/ML, barato) + warehouse (analytics,
confiável), com dados duplicados e pipelines entre eles. O lakehouse promete **um** sistema: ACID,
updates, time travel e SQL performático **direto sobre o lake** — menos cópias, menos complexidade,
formatos abertos (sem lock-in).

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Motivação e arquitetura](01-motivation-architecture/README.md) | Por que surgiu, como funciona |
| 02 | [Lake vs Warehouse vs Lakehouse](02-lake-vs-warehouse-vs-lakehouse/README.md) | Comparação dos três |
| 03 | [ACID sobre object storage](03-acid-on-object-storage/README.md) | Como se dá transações num lake |
| 04 | [Delta Lake](04-delta-lake/README.md) | O table format da Databricks |
| 05 | [Apache Iceberg](05-apache-iceberg/README.md) | O table format aberto da Netflix |
| 06 | [Apache Hudi](06-apache-hudi/README.md) | Table format com foco em upserts/CDC |

## Dependências internas

```text
Motivação/arquitetura ─► Lake vs Warehouse vs Lakehouse ─► ACID sobre object storage
                                                                  │
                                 Delta Lake / Iceberg / Hudi ─────┘ (implementações)
```

## Checkpoint

- [ ] Explicar o que um lakehouse resolve que lake e warehouse sozinhos não.
- [ ] Comparar lake, warehouse e lakehouse em ACID, custo, schema e performance.
- [ ] Explicar como ACID é alcançado sobre object storage (log/manifesto + commit atômico).
- [ ] Descrever time travel, schema evolution e upserts (`MERGE`) num lakehouse.
- [ ] Comparar Delta, Iceberg e Hudi (sem declarar um vencedor universal).

## Referências do módulo

- Armbrust et al. "Lakehouse: A New Generation of Open Platforms..." (CIDR 2021).
- Documentação de Delta Lake, Apache Iceberg e Apache Hudi.
