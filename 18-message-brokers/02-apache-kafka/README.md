# Apache Kafka

> 🟣 Distributed Systems · Parte de [18 — Message Brokers](../README.md)

## O que é

**Apache Kafka** é uma plataforma distribuída de **event streaming** baseada num **log particionado e
replicado**. Criado no LinkedIn, é o padrão de fato para transporte de eventos em escala: alta vazão,
baixa latência, durabilidade e replay. É o coração de pipelines de [streaming](../../17-streaming/README.md),
[CDC](../../09-etl-elt/06-cdc/README.md) e integração de dados.

## Por que existe / o que resolve

Integrar N sistemas ponto a ponto vira um emaranhado (N×M). Kafka oferece um **barramento central
durável**: produtores escrevem eventos uma vez; qualquer número de consumidores lê no seu ritmo, com
histórico retido ([log vs fila](../01-queue-vs-log/README.md)).

## Arquitetura

```text
Producers ─► [ Cluster Kafka: Brokers ] ─► Consumers (consumer groups)
              Tópico "pedidos" = N partições, cada uma replicada
              ├─ partição 0: líder em broker1, réplicas em broker2,3
              ├─ partição 1: líder em broker2, réplicas ...
              └─ ...
```

| Conceito | Papel |
| --- | --- |
| **Broker** | servidor que armazena partições e serve produtores/consumidores |
| **Topic** | categoria/feed de eventos (ex.: `pedidos`) |
| **Partition** | unidade de paralelismo e ordem: um log ordenado e imutável |
| **Offset** | posição sequencial de um registro numa partição |
| **Replication** | cada partição tem líder + réplicas (ISR) para tolerância a falhas |
| **Controller** | gerencia metadados/eleição de líder — **KRaft** (Raft embutido) substituiu o ZooKeeper nas versões atuais |

## Registro (record)

`chave` (opcional, define a partição) + `valor` (payload, ex.: [Avro](../../08-data-formats/05-avro/README.md)/JSON/Protobuf) + `timestamp` + `headers`.

## Durabilidade e replicação

- Dados gravados em disco (log segmentado, escrita sequencial) e **replicados**: `replication.factor=3`.
- **ISR (in-sync replicas)** — réplicas em dia; `min.insync.replicas` + `acks=all` garantem que o
  commit só ocorre quando réplicas suficientes confirmaram (durabilidade vs latência).
- Falha do líder → eleição de uma réplica ISR (ver [replicação](../../06-databases/07-replication/README.md),
  [CAP](../../01-foundations/05-distributed-systems-fundamentals/README.md)).

## Por que é rápido

Escrita **sequencial** no disco, *page cache* do SO, *zero-copy* no envio, batching e compressão de
mensagens, particionamento para paralelismo horizontal.

## Ecossistema

- **[Kafka Connect](../07-kafka-connect/README.md)** — ingestão/exportação (incl. Debezium CDC).
- **[Kafka Streams](../../17-streaming/06-kafka-streams/README.md)** / ksqlDB — processamento.
- **Schema Registry** — contratos/compatibilidade ([schema evolution](../../08-data-formats/10-schema-evolution/README.md)).
- Integração com [Flink](../../17-streaming/07-flink/README.md), [Spark](../../17-streaming/08-spark-structured-streaming/README.md).

## Exemplo rápido (CLI)

```bash
kafka-topics.sh --create --topic pedidos --partitions 6 --replication-factor 3 --bootstrap-server b:9092
kafka-console-producer.sh --topic pedidos --bootstrap-server b:9092
kafka-console-consumer.sh --topic pedidos --from-beginning --bootstrap-server b:9092
```

## Trade-offs

- **Operação complexa** (cluster, partições, rebalanceamento, monitoramento) — há serviços gerenciados
  (Confluent Cloud, MSK, Redpanda).
- **Não é banco nem fila de tarefas**: sem consulta ad-hoc; sem roteamento sofisticado.
- Escolher nº de partições é decisão difícil de reverter (aumentar quebra a ordem por chave).
- Consistência: ordem **só por partição**.

## Quando usar / não usar

- **Use** para ingestão/streaming em escala, CDC, integração, log de eventos com replay.
- **Evite** para poucas mensagens/baixo volume onde RabbitMQ/SQS bastam, ou como banco de consulta.

## Erros comuns

- Poucas partições (limita paralelismo) ou demais (overhead).
- `acks=1`/`min.insync.replicas` baixos em dados críticos.
- Chave mal escolhida (hot partition/skew).
- Retenção insuficiente para o replay desejado.
- Mensagens gigantes (use referência ao objeto no storage).

## Boas práticas

- `replication.factor=3`, `acks=all`, `min.insync.replicas=2` para dados críticos.
- Schema Registry + compatibilidade; chave pensada para ordem/distribuição.
- Monitorar consumer lag, ISR, under-replicated partitions.
- Preferir serviço gerenciado se o time é pequeno.

## Relação com outros conceitos

- [Queue vs log](../01-queue-vs-log/README.md), [producers/consumers](../03-producers-consumers/README.md),
  [partitions/offsets](../04-partitions-offsets-consumer-groups/README.md),
  [ordering/retention](../05-ordering-retention-replay/README.md).
- [Streaming](../../17-streaming/README.md), [CDC](../../09-etl-elt/06-cdc/README.md);
  [Projeto 07](../../projects/07-kafka/README.md).

## Exercícios

1. Suba Kafka (Docker/KRaft), crie um tópico com 3 partições e produza/consuma via CLI.
2. Explique líder, réplicas e ISR numa falha de broker.
3. Que configs garantem durabilidade máxima e o custo disso?
4. Por que a ordem é garantida só por partição?

## Referências

- Documentação oficial do Apache Kafka (kafka.apache.org/documentation).
- Narkhede, N. et al. *Kafka: The Definitive Guide*.
