# Queue vs Log

> 🟣 Distributed Systems · Parte de [18 — Message Brokers](../README.md)

## O que é

Dois modelos fundamentais de broker de mensagens:

- **Fila (queue / message broker tradicional)** — a mensagem é **entregue a um consumidor e removida**
  após confirmação (*ack*). Exemplos: RabbitMQ, SQS, ActiveMQ.
- **Log (append-only log / event streaming)** — mensagens são **anexadas a um log durável e retidas**;
  consumidores lêem por **posição (offset)** sem removê-las. Exemplos: Kafka, Pulsar, Kinesis.

## Fila: como funciona

```text
Produtor ─► [ m1 m2 m3 m4 ] ─► Consumidor A (pega m1, ack → m1 removida)
                            └► Consumidor B (pega m2, ack → m2 removida)
```

- Mensagens são **consumidas e apagadas**; cada mensagem vai a **um** consumidor (*competing consumers*
  — distribui carga).
- Ótimo para **distribuir tarefas** (jobs/workers), com roteamento flexível, prioridades, TTL, dead-letter.
- Ordem global fraca com múltiplos consumidores; sem *replay* (a mensagem sumiu).

## Log: como funciona

```text
Produtor ─► [ m1 m2 m3 m4 m5 ... ] (log imutável, retido por tempo/tamanho)
              ▲        ▲
        Consumidor A  Consumidor B   (cada um com seu offset; leem independentemente)
```

- Mensagens **permanecem** (até a retenção expirar); consumidores controlam seu **offset**.
- **Múltiplos consumidores independentes** lêem o mesmo dado (pub/sub) sem interferir.
- **Replay** — reler o histórico (reprocessar, novo consumidor, corrigir bug) — ver
  [ordering/retention/replay](../05-ordering-retention-replay/README.md).
- **Ordem preservada por partição**; alto throughput por escrita sequencial em disco.

## Comparação

| Aspecto | Fila | Log |
| --- | --- | --- |
| Após consumir | mensagem removida | **retida** |
| Consumidores | competem (1 msg → 1 consumidor) | independentes (cada um lê tudo) |
| Replay | não | **sim** |
| Ordem | fraca com paralelismo | por partição |
| Roteamento complexo | **forte** (exchanges, filtros) | simples (tópico/partição) |
| Throughput | médio | **muito alto** |
| Caso típico | tarefas/RPC assíncrono | event streaming, CDC, analytics |

## Por que o log venceu em dados

Para Data Engineering, o log tem vantagens decisivas: **replay** (reprocessar/backfill), múltiplos
consumidores (lake + stream processing + serviços) a partir de **uma fonte**, retenção como buffer e
auditoria, e throughput. É a base das arquiteturas [Kappa](../../01-foundations/04-data-systems/README.md),
[event-driven](../../17-streaming/02-event-driven-architecture/README.md) e do
[CDC](../../09-etl-elt/06-cdc/README.md).

## Quando cada um

- **Log (Kafka)** — streams de eventos, ingestão de dados, múltiplos consumidores, replay, alto volume.
- **Fila (RabbitMQ/SQS)** — distribuição de tarefas, workers, roteamento sofisticado, mensagens que
  **devem ser processadas uma vez e descartadas**.

## Erros comuns

- Usar log (Kafka) como fila de tarefas com semântica de "remover ao concluir" (não é o modelo).
- Usar fila onde é preciso replay/múltiplos consumidores.
- Achar que "Kafka substitui tudo" ou o contrário.

## Boas práticas

- Escolha pelo padrão de acesso (replay/múltiplos consumidores → log; tarefas/roteamento → fila).
- Em ambos, projete consumidores [idempotentes](../../09-etl-elt/07-idempotency-retries/README.md).

## Relação com outros conceitos

- [Kafka](../02-apache-kafka/README.md), [RabbitMQ](../08-rabbitmq-and-others/README.md),
  [offsets](../04-partitions-offsets-consumer-groups/README.md), [replay](../05-ordering-retention-replay/README.md).
- [EDA](../../17-streaming/02-event-driven-architecture/README.md).

## Exercícios

1. Diferencie fila e log com um exemplo de cada.
2. Por que replay é valioso para Data Engineering?
3. Escolha fila ou log para: processar uploads de imagens; ingerir cliques; sincronizar bancos (CDC).

## Referências

- Kleppmann, M. *DDIA* — cap. 11 ("Messaging Systems", "Partitioned Logs").
