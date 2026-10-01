# 30 — Advanced Data Engineering

> 🟣 Nível 8 — Advanced · Pré: módulos [09](../09-etl-elt/README.md), [15](../15-lakehouse/README.md),
> [16](../16-distributed-processing/README.md), [17](../17-streaming/README.md),
> [18](../18-message-brokers/README.md), [29](../29-data-contracts/README.md) · Próximo:
> [31 — DE + ML](../31-data-engineering-and-ml/README.md)

Tópicos **especializados e arquiteturais** que ampliam o repertório de um Data Engineer sênior. Aqui a
fronteira entre **fundamento**, **ferramenta**, **especialização** e **tendência** importa — para você não
tratar moda como obrigação.

## O que é fundamental vs especializado (leia primeiro)

| Tópico | Natureza | Quando estudar |
| --- | --- | --- |
| [CDC / Debezium](01-cdc-debezium/README.md) | **Especialização com forte valor prático** (padrão de ingestão incremental) | quando precisar replicar OLTP em tempo quase real |
| [Event sourcing / CQRS](02-event-sourcing-cqrs/README.md) | **Padrão arquitetural** (conceito durável; uso seletivo) | ao projetar sistemas orientados a eventos/auditáveis |
| [Data mesh](03-data-mesh/README.md) | **Paradigma organizacional** (não é tecnologia) | organizações grandes, muitos domínios |
| [Data fabric](04-data-fabric/README.md) | **Conceito/abordagem de integração** (parte marketing) | ao avaliar arquiteturas de metadados ativos |
| [Real-time analytics](05-real-time-analytics/README.md) | **Especialização** (OLAP de baixa latência) | produtos com analytics em segundos |
| [Vector databases](06-vector-databases/README.md) | **Tendência/tecnologia nova** (IA/RAG) | busca semântica, RAG, recomendação |
| [Distributed databases](07-distributed-databases/README.md) | **Fundamento avançado** (NewSQL, consenso) | escala/consistência global |
| [Query engines (Trino/Presto)](08-query-engines/README.md) | **Ferramenta/arquitetura** (federação/lakehouse SQL) | SQL interativo sobre lake/múltiplas fontes |
| [Spark avançado](09-advanced-spark/README.md) | **Aprofundamento** de ferramenta essencial | jobs grandes/custosos |
| [Kafka avançado](10-advanced-kafka/README.md) | **Aprofundamento** de ferramenta essencial | operação/garantias em escala |

> Regra: **fundamentos** (módulos 01–29) antes de **especializações**. Muitas "tendências" têm núcleo
> sólido, mas são cercadas de *hype*; avalie por **problema real**, não por moda.

## Dependências internas

```text
CDC/Debezium ─► Event sourcing/CQRS ─► Real-time analytics
        │                                      │
Data mesh ─► Data fabric            Distributed databases ─► Query engines
                                         │
                 Advanced Spark · Advanced Kafka · Vector databases
```

## Checkpoint

- [ ] Projetar CDC com Debezium (snapshot + streaming, deletes, schema evolution).
- [ ] Explicar event sourcing e CQRS, seus ganhos e custos.
- [ ] Descrever os 4 princípios do data mesh e criticar quando **não** usá-lo.
- [ ] Diferenciar data mesh e data fabric.
- [ ] Escolher entre warehouse, OLAP em tempo real (Pinot/Druid/ClickHouse) e streaming para um caso.
- [ ] Explicar embeddings, ANN e quando usar um vector database.
- [ ] Comparar bancos distribuídos (Spanner/CockroachDB/Cassandra) por consistência.
- [ ] Usar Trino/Presto para consultas federadas; aplicar técnicas avançadas de Spark/Kafka.

## Referências do módulo

- Kleppmann, M. *DDIA* (replicação, consenso, event sourcing); Dehghani, Z. *Data Mesh*.
- Documentação de Debezium, Trino, Apache Pinot/Druid, pgvector/Milvus, Spark e Kafka.
