# 14 — Data Lake

> 🔵 Nível 4 — Analytics Platforms · Pré: [08 — Formats](../08-data-formats/README.md),
> [13 — Warehouse](../13-data-warehouse/README.md) · Próximo:
> [15 — Lakehouse](../15-lakehouse/README.md)

Um **data lake** é um repositório central que armazena **qualquer tipo de dado** (estruturado,
semiestruturado, não-estruturado) em **formato bruto**, sobre
[object storage](../19-cloud/02-object-storage/README.md) barato e escalável. É a resposta para
"guardar tudo, barato, e decidir o esquema depois" — complementando o
[warehouse](../13-data-warehouse/README.md).

## Por que importa

Nem todo dado cabe (ou vale a pena) num warehouse: logs, eventos, imagens, JSON variável, dados
brutos para ML. O lake armazena tudo isso por uma fração do custo, preserva o bruto para
reprocessar e serve de fundação para [lakehouse](../15-lakehouse/README.md),
[Spark](../16-distributed-processing/README.md) e [ML](../31-data-engineering-and-ml/README.md).

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Conceitos](01-concepts/README.md) | O que é, lake vs warehouse, data swamp |
| 02 | [Object storage](02-object-storage/README.md) | O armazenamento por trás do lake |
| 03 | [Medallion architecture](03-medallion-architecture/README.md) | Bronze/silver/gold |
| 04 | [Schema-on-read vs on-write](04-schema-on-read-write/README.md) | Quando aplicar o schema |
| 05 | [Partitioning](05-partitioning/README.md) | Organizar arquivos para performance |
| 06 | [Small files e compaction](06-small-files-compaction/README.md) | O problema dos arquivos pequenos |
| 07 | [Metadata](07-metadata/README.md) | Catálogo técnico, Hive Metastore |

## Dependências internas

```text
Conceitos ─► Object storage ─► Medallion architecture
                                      │
Schema-on-read/write ─────────────────┤
Partitioning ─► Small files/compaction │
Metadata ──────────────────────────────┘
```

## Checkpoint

- [ ] Explicar o que é um data lake e como difere de um warehouse.
- [ ] Descrever object storage e por que ele sustenta o lake.
- [ ] Organizar um lake em camadas medallion (bronze/silver/gold).
- [ ] Diferenciar schema-on-read de schema-on-write e seus trade-offs.
- [ ] Particionar arquivos (Hive-style) e explicar o partition pruning.
- [ ] Explicar o small files problem e como compactar.
- [ ] Explicar o papel de um metastore/catálogo no lake.

## Referências do módulo

- Reis & Housley, *Fundamentals of Data Engineering* — storage.
- Documentação de S3/GCS, Hive Metastore, Apache Iceberg (metadados).
