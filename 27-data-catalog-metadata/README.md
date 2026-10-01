# 27 — Data Catalog, Lineage e Metadata

> 🟣 Nível 7 — Production · Pré: [25 — Governance](../25-data-governance/README.md),
> [10 — Pipelines/lineage](../10-data-pipelines/06-data-lineage/README.md) · Próximo:
> [29 — Data Contracts](../29-data-contracts/README.md)

Este módulo aprofunda a **camada de metadados** da plataforma: os tipos de metadados, o **lineage
(inclusive por coluna)**, os **catálogos** para descoberta e as **ferramentas** (DataHub, OpenMetadata,
Atlas e nativas de cloud). É a base técnica que viabiliza a [governança](../25-data-governance/README.md)
em escala: descobrir, entender, confiar e analisar impacto.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Tipos de metadados](01-metadata-types/README.md) | Técnico, de negócio, operacional, social |
| 02 | [Lineage e column lineage](02-lineage-column-lineage/README.md) | Rastreio de origem e impacto |
| 03 | [Catálogos, discovery e impact analysis](03-catalogs-discovery/README.md) | Encontrar e usar dados |
| 04 | [Ferramentas](04-tools/README.md) | DataHub, OpenMetadata, Atlas e outras |

## Dependências internas

```text
Tipos de metadados ─► Lineage/column lineage ─► Catálogos/discovery/impact analysis ─► Ferramentas
```

## Checkpoint

- [ ] Classificar metadados (técnico, negócio, operacional, social) e dar exemplos.
- [ ] Explicar lineage em nível de tabela e de coluna e como é capturado (OpenLineage).
- [ ] Usar um catálogo para discovery e análise de impacto.
- [ ] Comparar DataHub, OpenMetadata e Atlas e quando usar cada um.
- [ ] Projetar a ingestão automatizada de metadados de dbt/warehouse/orquestrador.

## Referências do módulo

- Documentação de DataHub, OpenMetadata, Apache Atlas, OpenLineage/Marquez.
- DAMA-DMBOK (Metadata Management); Reis & Housley, *Fundamentals of Data Engineering*.
