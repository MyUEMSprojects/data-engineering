# 08 — Data Formats

> 🔵 Nível 2 — Core · Pré: [04 — Python](../04-python-for-data-engineering/README.md),
> [06 — Databases](../06-databases/README.md) · Próximo:
> [09 — ETL/ELT](../09-etl-elt/README.md)

Dados precisam ser **serializados** para trafegar e serem armazenados. A escolha do
formato impacta diretamente **performance, custo, interoperabilidade e evolução** dos
pipelines. Este módulo cobre os formatos que o Data Engineer encontra, a diferença
fundamental entre **linha e coluna**, compressão e **schema evolution**.

## Por que importa

- O formato errado custa caro: CSV para analytics em escala desperdiça I/O e dinheiro;
  JSON sem schema vira dívida técnica.
- Entender **colunar (Parquet)** é entender por que o mundo analítico moderno é rápido.
- **Schema evolution** mal planejada quebra pipelines e consumidores silenciosamente.

## Tópicos

| # | Tópico | Tipo |
| --- | --- | --- |
| 01 | [CSV](01-csv/README.md) | texto, linha, sem schema |
| 02 | [JSON / JSONL](02-json-jsonl/README.md) | texto, semiestruturado |
| 03 | [XML](03-xml/README.md) | texto, hierárquico (legado) |
| 04 | [Parquet](04-parquet/README.md) | binário, **colunar** (analytics) |
| 05 | [Avro](05-avro/README.md) | binário, linha, schema (streaming) |
| 06 | [ORC](06-orc/README.md) | binário, colunar (Hive) |
| 07 | [Protocol Buffers](07-protobuf/README.md) | binário, linha (RPC/mensagens) |
| 08 | [Row vs Columnar](08-row-vs-columnar/README.md) | o conceito central |
| 09 | [Compressão](09-compression/README.md) | snappy, gzip, zstd... |
| 10 | [Schema evolution](10-schema-evolution/README.md) | evoluir sem quebrar |

## Como escolher (resumo)

```text
Analytics / data lake / warehouse        → Parquet (colunar) ✅
Streaming / mensagens Kafka com schema   → Avro (+ Schema Registry)
RPC / contratos de serviço               → Protobuf
Troca simples / humanos / planilhas      → CSV (pequeno) / JSON
Legado / integrações antigas             → XML
Ecossistema Hive/transações antigas      → ORC
```

## Dependências internas

```text
Row vs Columnar (conceito) ─┬─► CSV, JSON, XML, Avro, Protobuf (row/texto)
                            └─► Parquet, ORC (colunar)
                                      │
                 Compressão ─────────┤
                 Schema evolution ───┘ (atravessa Avro/Parquet/Protobuf)
```

## Checkpoint

- [ ] Explicar row-based vs columnar e por que Parquet acelera analytics.
- [ ] Escolher o formato certo para lake, streaming, RPC e troca simples.
- [ ] Ler/escrever Parquet e aproveitar *column pruning* + *predicate pushdown*.
- [ ] Diferenciar JSON de JSONL e tratar dados aninhados.
- [ ] Comparar codecs de compressão (snappy/gzip/zstd) por velocidade × razão.
- [ ] Planejar schema evolution compatível (adicionar campo opcional, etc.).

## Referências do módulo

- Documentação oficial do Apache Parquet, Avro, ORC e Protocol Buffers.
- Kleppmann, M. *DDIA* — cap. 4 (encoding e evolution).
- Apache Arrow (arrow.apache.org).
