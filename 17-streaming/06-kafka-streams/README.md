# Kafka Streams

> 🟣 Distributed Systems · Parte de [17 — Streaming](../README.md)

## O que é

**Kafka Streams** é uma **biblioteca Java/Scala** (não um cluster) para processar streams de dados
**lidos e escritos em tópicos [Kafka](../../18-message-brokers/02-apache-kafka/README.md)**. Você a
embute na sua aplicação; ela herda do Kafka paralelismo, tolerância a falhas e
[exactly-once](../04-delivery-semantics/README.md). É *true streaming* (evento a evento).

## Por que existe

Frameworks como [Flink](../07-flink/README.md) e [Spark](../08-spark-structured-streaming/README.md)
exigem um cluster de processamento à parte. Se seus dados já vivem no Kafka e a lógica é de
transformação/agregação, uma biblioteca simples — apenas um app que você deploya como qualquer
microsserviço — reduz muito a complexidade operacional.

## Como funciona

```text
Tópico de entrada ──► [App Kafka Streams: N instâncias] ──► Tópico de saída
                         ├─ topologia (DAG de operadores)
                         └─ state stores locais (RocksDB) + changelog topics no Kafka
```

- **Topologia** — grafo de operadores (`map`, `filter`, `groupByKey`, `aggregate`, `join`, `windowedBy`).
- **Paralelismo** — uma *task* por partição do tópico de entrada; adicionar instâncias da app
  redistribui as partições (via [consumer group](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md)).
- **Estado** — *state stores* locais (RocksDB) respaldados por **changelog topics**: se uma instância
  cai, outra reconstrói o estado relendo o changelog (ver [stateful](../05-stateful-processing/README.md)).
- **Exactly-once** — `processing.guarantee=exactly_once_v2` usa transações Kafka (consumo + estado +
  produção atômicos).

## Abstrações

| Abstração | Significado |
| --- | --- |
| **KStream** | fluxo de eventos (cada registro é um fato independente) |
| **KTable** | tabela de "último valor por chave" (changelog materializado) |
| **GlobalKTable** | tabela replicada em todas as instâncias (lookup/enriquecimento) |

A dualidade **stream ↔ tabela** é conceito central: uma tabela é um stream de mudanças; um stream pode
ser agregado numa tabela (mesma ideia do [CDC](../../09-etl-elt/06-cdc/README.md)).

## Exemplo (Java, conceitual)

```java
StreamsBuilder b = new StreamsBuilder();
KStream<String, Order> orders = b.stream("orders");

orders.filter((k, o) -> o.status().equals("PAID"))
      .groupBy((k, o) -> o.uf())
      .windowedBy(TimeWindows.ofSizeAndGrace(Duration.ofMinutes(5), Duration.ofSeconds(30)))
      .aggregate(() -> 0.0, (uf, o, acc) -> acc + o.value(), Materialized.as("rev-by-uf"))
      .toStream()
      .to("revenue-by-uf");
```

Janelas por **event time** com *grace period* para atrasados (ver
[tempo e janelas](../03-time-and-windows/README.md)).

## Vantagens

- Sem cluster extra: é uma biblioteca; deploy como qualquer app (container/[Kubernetes](../../21-kubernetes/README.md)).
- Integração nativa com Kafka, exactly-once e escalabilidade elástica.
- Baixa latência e estado local rápido.

## Limitações / trade-offs

- **Acoplado ao Kafka** (fonte e destino são tópicos; para outros sinks use Kafka Connect).
- Principal suporte em **JVM** (Java/Scala); Python não tem equivalente oficial (use
  [Flink](../07-flink/README.md)/Faust-like/ksqlDB).
- Menos recursos de alto nível que Flink (CEP, SQL rico, batch unificado).
- Reconstruir estado grande após falha pode demorar (mitigado por *standby replicas*).

## Quando usar / não usar

- **Use** para transformações/agregações/joins sobre dados que já estão no Kafka, com time JVM e desejo
  de simplicidade operacional.
- **Evite** se precisa de múltiplas fontes/sinks heterogêneos, SQL/CEP avançado, ou stack Python → veja
  Flink/Spark. **ksqlDB** oferece SQL sobre Kafka Streams.

## Erros comuns

- Número de partições do tópico limitando o paralelismo (instâncias ociosas).
- Ignorar o tamanho do estado/tempo de restore.
- Janelas sem *grace period* (perde eventos atrasados).
- Mudar a topologia e reusar `application.id`/state incompatível.

## Boas práticas

- Defina chaves/partições pensando em ordem e paralelismo.
- `exactly_once_v2` quando duplicatas são inaceitáveis; *standby replicas* para failover rápido.
- Monitore *consumer lag* e tamanho do state store.
- Versione schemas (registry) — ver [Avro](../../08-data-formats/05-avro/README.md).

## Relação com outros conceitos

- [Kafka](../../18-message-brokers/02-apache-kafka/README.md), [stateful](../05-stateful-processing/README.md),
  [delivery semantics](../04-delivery-semantics/README.md), [janelas](../03-time-and-windows/README.md).
- Alternativas: [Flink](../07-flink/README.md), [Spark Structured Streaming](../08-spark-structured-streaming/README.md).

## Exercícios

1. Escreva uma topologia que conta eventos por usuário em janelas tumbling de 1 minuto.
2. Explique a dualidade stream↔tabela com um exemplo (KStream vs KTable).
3. Descreva como o estado é recuperado após a queda de uma instância.
4. Compare Kafka Streams e Flink para um time Python com múltiplos sinks.

## Referências

- Documentação oficial do Kafka Streams (kafka.apache.org/documentation/streams).
- Kleppmann, M. *DDIA* — cap. 11; Stopford, B. *Designing Event-Driven Systems*.
