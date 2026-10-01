# RabbitMQ e outros brokers

> 🟣 Distributed Systems · Parte de [18 — Message Brokers](../README.md)

## RabbitMQ

### O que é

**RabbitMQ** é um message broker **tradicional (fila)** baseado em AMQP, focado em **roteamento
flexível** e entrega confiável de mensagens a consumidores/workers. Segue o modelo de [fila](../01-queue-vs-log/README.md):
a mensagem é entregue, confirmada (*ack*) e removida.

### Conceitos

```text
Producer ─► Exchange ─(binding/routing key)─► Queue ─► Consumer (ack)
```

- **Exchange** — recebe do producer e **roteia** conforme o tipo: `direct` (chave exata), `topic`
  (padrões `a.*.b`), `fanout` (broadcast), `headers`.
- **Queue** — armazena mensagens até serem consumidas; pode ser durável.
- **Binding** — regra que liga exchange a fila.
- **Ack/nack/requeue**, **prefetch** (limita mensagens em voo por consumidor — controle de
  [backpressure](../06-backpressure/README.md)), **dead-letter exchanges**, TTL, prioridades.
- **Quorum queues / streams** — filas replicadas (Raft); *RabbitMQ Streams* adicionam semântica de log.

### Quando usar

- **Distribuição de tarefas** a workers (background jobs), RPC assíncrono, workflows.
- Roteamento sofisticado, prioridades, TTL, retries com DLX.
- Volume moderado; cada mensagem processada e descartada.

### Limitações para dados

- **Sem replay** (mensagem some após ack) e **sem múltiplos consumidores independentes** do mesmo dado
  sem fanout/filas separadas.
- Throughput e retenção menores que Kafka; não é feito para reter histórico.
- Menos adequado a ingestão massiva, CDC e streaming analítico.

## Outras opções

| Sistema | Modelo | Notas |
| --- | --- | --- |
| **Amazon SQS** | fila gerenciada | simples, escalável, sem servidor; FIFO opcional |
| **Amazon SNS** | pub/sub | fanout para filas/lambdas |
| **Amazon Kinesis** | log | similar ao Kafka, gerenciado AWS |
| **Google Pub/Sub** | pub/sub gerenciado | alto escalonamento; ack por assinatura, retenção/replay configurável |
| **Azure Event Hubs / Service Bus** | log (Event Hubs) / fila (Service Bus) | compatibilidade Kafka no Event Hubs |
| **Apache Pulsar** | log + fila unificados | multi-tenant, tiered storage, geo-replicação |
| **Redpanda** | log compatível com Kafka | binário único (C++), sem JVM/ZooKeeper |
| **Redis Streams / NATS** | log/mensageria leve | baixa latência, menor escala/durabilidade |

## Como escolher

```text
Dados/eventos em escala, replay, múltiplos consumidores, CDC  → Kafka (ou Kinesis/Pub/Sub/Event Hubs/Redpanda/Pulsar)
Tarefas/jobs com roteamento rico, prioridade, TTL              → RabbitMQ
Fila simples gerenciada na cloud, sem operar nada              → SQS / Pub/Sub / Service Bus
Mensageria leve de baixa latência                              → NATS / Redis Streams
```

Critérios: **replay**, **throughput**, **modelo (fila vs log)**, **operação (gerenciado vs self-hosted)**,
**ecossistema**, **semântica de ordem/entrega**, custo.

## Erros comuns

- Usar RabbitMQ como plataforma de event streaming/ingestão (sem replay).
- Usar Kafka como fila de tarefas com roteamento/prioridade complexos.
- Escolher pela moda em vez do padrão de acesso.
- Subestimar o custo operacional de self-hosted.

## Boas práticas

- Case o modelo (fila/log) com o caso de uso; prefira gerenciado se o time é pequeno.
- Em qualquer broker: consumidores idempotentes, DLQ, monitoramento de lag/profundidade.
- Evite lock-in com contratos de evento portáveis (Avro/Protobuf + registry).

## Relação com outros conceitos

- [Queue vs log](../01-queue-vs-log/README.md), [Kafka](../02-apache-kafka/README.md),
  [backpressure](../06-backpressure/README.md), [cloud services](../../19-cloud/README.md).
- [EDA](../../17-streaming/02-event-driven-architecture/README.md).

## Exercícios

1. Modele uma topologia RabbitMQ (exchange topic + filas) para logs por severidade/serviço.
2. Por que RabbitMQ não substitui Kafka em ingestão com replay?
3. Escolha broker para: jobs de envio de e-mail; CDC de 50 tabelas; telemetria IoT massiva.
4. Compare SQS e Kafka em modelo, replay e operação.

## Referências

- Documentação do RabbitMQ (rabbitmq.com), SQS/SNS, Pub/Sub, Kinesis, Pulsar, Redpanda.
- Kleppmann, M. *DDIA* — cap. 11 (message brokers).
