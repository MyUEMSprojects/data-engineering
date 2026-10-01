# Kafka Connect

> 🟣 Distributed Systems · Parte de [18 — Message Brokers](../README.md)

## O que é

**Kafka Connect** é um framework (parte do Apache Kafka) para **mover dados entre o Kafka e sistemas
externos** de forma escalável e configurável, **sem escrever código**. Você declara *connectors* (JSON/
REST) e o Connect cuida de paralelismo, offsets, retries e tolerância a falhas.

## Por que existe

Ingerir/exportar dados com producers/consumers feitos à mão é repetitivo e frágil (offsets, esquemas,
falhas, escala). O Connect padroniza isso com um ecossistema de **conectores prontos** (centenas).

## Arquitetura

```text
Fonte (DB, S3, API) ─► [Source Connector] ─► Kafka ─► [Sink Connector] ─► Destino (lake, warehouse, DB)
                       (Connect Workers: cluster distribuído, tasks paralelas)
```

- **Source connector** — lê de um sistema externo e **produz** em tópicos.
- **Sink connector** — **consome** de tópicos e grava num sistema externo.
- **Workers** — processos que rodam *connectors* e *tasks*; modo **distribuído** (cluster, HA) ou
  standalone (dev).
- **Converters** — serialização (Avro/JSON/Protobuf, com [Schema Registry](../../08-data-formats/05-avro/README.md)).
- **SMT (Single Message Transforms)** — transformações leves por mensagem (renomear campo, mascarar,
  rotear, extrair chave) — não substituem processamento de stream.

## Exemplo (sink JDBC / registrar via REST)

```json
{
  "name": "sink-pedidos-postgres",
  "config": {
    "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
    "topics": "pedidos",
    "connection.url": "jdbc:postgresql://db:5432/dw",
    "insert.mode": "upsert",
    "pk.mode": "record_key",
    "auto.create": "true",
    "tasks.max": "4"
  }
}
```

`insert.mode=upsert` + chave = escrita [idempotente](../../09-etl-elt/07-idempotency-retries/README.md).

## Debezium (CDC via Connect)

**[Debezium](../../09-etl-elt/06-cdc/README.md)** é um conjunto de *source connectors* de CDC (Postgres,
MySQL, SQL Server, MongoDB...) que leem o log de transações (WAL/binlog) e publicam eventos de
mudança no Kafka — o caminho padrão para replicar OLTP → lake/warehouse em tempo quase real.

## Conectores comuns

- **Sources**: Debezium (CDC), JDBC (polling), S3, arquivos, APIs.
- **Sinks**: S3/GCS (Parquet/Avro), JDBC, Elasticsearch, BigQuery, Snowflake, Iceberg, Redis.

## Vantagens

- Sem código; escalável (tasks paralelas); gerenciamento de offsets e falhas embutido.
- Ecossistema amplo; integra Schema Registry e SMTs.
- Padroniza integrações (operação e monitoramento uniformes).

## Limitações / trade-offs

- **Transformações limitadas** (SMTs): lógica complexa → use [stream processing](../../17-streaming/README.md).
- Operar um cluster Connect (ou usar gerenciado).
- Qualidade/maturidade varia por conector; semântica de entrega depende do conector (muitos são
  at-least-once → use sinks idempotentes).
- Evolução de schema exige atenção ([schema evolution](../../08-data-formats/10-schema-evolution/README.md)).

## Quando usar / não usar

- **Use** para ingestão/exportação padrão entre Kafka e sistemas conhecidos, e CDC com Debezium.
- **Evite** para lógica de negócio/transformação complexa (use Flink/Kafka Streams/Spark) ou integrações
  muito customizadas sem conector.

## Erros comuns

- Colocar lógica complexa em SMTs.
- Sink não-idempotente com at-least-once (duplicatas).
- Não monitorar conectores/tasks falhas e lag.
- Ignorar mudanças de schema da origem (conector quebra).
- `tasks.max` maior que o paralelismo útil.

## Boas práticas

- Modo distribuído em produção; monitorar status de connectors/tasks e lag.
- Schema Registry + compatibilidade; DLQ (`errors.deadletterqueue.topic.name`) para registros ruins.
- Sinks em modo upsert/idempotente; segredos via config providers (não em texto claro).

## Relação com outros conceitos

- [Kafka](../02-apache-kafka/README.md), [CDC](../../09-etl-elt/06-cdc/README.md),
  [ingestão](../../09-etl-elt/02-ingestion-extraction/README.md),
  [schema evolution](../../08-data-formats/10-schema-evolution/README.md).
- Avançado: [Debezium](../../30-advanced/01-cdc-debezium/README.md); [Projeto 07](../../projects/07-kafka/README.md).

## Exercícios

1. Configure um sink connector que grava um tópico em Parquet num bucket (MinIO/S3).
2. Explique source vs sink e o papel dos workers/tasks.
3. Dê um caso adequado a SMT e outro que exige stream processing.
4. Como garantir que um sink at-least-once não duplique?

## Referências

- Documentação do Kafka Connect e do Debezium; Confluent Hub.
