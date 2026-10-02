# 18 — Message Brokers

> 🟣 Nível 5 — Distributed Systems · Pré: [17 — Streaming](../17-streaming/README.md),
> [01/05 — Sistemas distribuídos](../01-foundations/05-distributed-systems-fundamentals/README.md) ·
> Próximo: [19 — Cloud](../19-cloud/README.md)

**Message brokers** são o sistema nervoso de arquiteturas orientadas a eventos: recebem mensagens de
**produtores**, armazenam-nas e as entregam a **consumidores**, desacoplando-os no tempo e na escala. O
**Apache Kafka** domina o mundo de dados, mas entender a diferença **fila vs log** e as alternativas
(RabbitMQ, etc.) é o que permite escolher bem.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Queue vs Log](01-queue-vs-log/README.md) | Dois modelos fundamentais de broker |
| 02 | [Apache Kafka](02-apache-kafka/README.md) | Arquitetura e conceitos |
| 03 | [Producers e consumers](03-producers-consumers/README.md) | Como produzir e consumir bem |
| 04 | [Partitions, offsets e consumer groups](04-partitions-offsets-consumer-groups/README.md) | Paralelismo e ordem |
| 05 | [Ordering, retention e replay](05-ordering-retention-replay/README.md) | Garantias de ordem e retenção |
| 06 | [Backpressure](06-backpressure/README.md) | Quando o consumidor não acompanha |
| 07 | [Kafka Connect](07-kafka-connect/README.md) | Integração com sistemas externos |
| 08 | [RabbitMQ e outros](08-rabbitmq-and-others/README.md) | Filas tradicionais e alternativas |

## Dependências internas

```text
Queue vs Log ─► Kafka ─► Producers/consumers ─► Partitions/offsets/groups
                                   │                      │
                       Ordering/retention/replay ◄────────┘
                                   │
                    Backpressure · Kafka Connect · RabbitMQ & outros
```

## Checkpoint

- [ ] Diferenciar fila (queue) de log e escolher entre eles.
- [ ] Descrever a arquitetura do Kafka (brokers, tópicos, partições, réplicas).
- [ ] Configurar producers (acks, idempotência) e consumers (commit de offset) com segurança.
- [ ] Explicar partições, offsets e consumer groups e como definem paralelismo/ordem.
- [ ] Explicar garantias de ordem, retenção e replay.
- [ ] Tratar backpressure.
- [ ] Usar Kafka Connect para integração; comparar Kafka e RabbitMQ.

## Referências do módulo

- Documentação oficial do Apache Kafka; *Kafka: The Definitive Guide* (Narkhede et al., O'Reilly).
- Kleppmann, M. *DDIA* — cap. 11 (message brokers vs logs).
- Documentação do RabbitMQ.
