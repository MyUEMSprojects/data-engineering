# Producers e consumers

> 🟣 Distributed Systems · Parte de [18 — Message Brokers](../README.md)

## Producers

Um **producer** publica registros em tópicos. Decisões que importam:

### Particionamento (qual partição recebe)

- Com **chave**: `hash(chave) % nº_partições` → mesma chave, mesma partição → **ordem por chave**.
- Sem chave: distribuição round-robin/sticky (balanceia, sem ordem por entidade).
- Chave ruim = *hot partition* ([skew](../../16-distributed-processing/04-distributed-joins-skew/README.md)).

### Garantias de escrita (`acks`)

| `acks` | Significado | Risco |
| --- | --- | --- |
| `0` | não espera confirmação | perde dados |
| `1` | líder confirma | perde se líder cair antes de replicar |
| `all` | todas as réplicas ISR confirmam | mais latência, **mais seguro** |

### Idempotência e retries

`enable.idempotence=true` evita duplicatas causadas por retries do producer (dedupe por sequência na
partição). Combine com `acks=all`. Transações Kafka permitem escrever em vários tópicos/partições
atomicamente (base do [exactly-once](../../17-streaming/04-delivery-semantics/README.md)).

### Performance

*Batching* (`linger.ms`, `batch.size`), compressão (`lz4`/`zstd`), buffer — trocam latência por
throughput.

```python
from confluent_kafka import Producer
p = Producer({"bootstrap.servers": "b:9092", "acks": "all", "enable.idempotence": True,
              "compression.type": "zstd", "linger.ms": 20})
p.produce("pedidos", key=str(order_id), value=payload, callback=on_delivery)
p.flush()
```

## Consumers

Um **consumer** lê registros de partições, normalmente dentro de um
[consumer group](../04-partitions-offsets-consumer-groups/README.md).

### Commit de offset (define a semântica)

- **Auto-commit** — simples, mas pode perder ou duplicar em falhas.
- **Commit manual após processar** — **at-least-once** (recomendado) + processamento idempotente.
- Commit antes de processar → at-most-once. Ver [delivery semantics](../../17-streaming/04-delivery-semantics/README.md).

```python
from confluent_kafka import Consumer
c = Consumer({"bootstrap.servers": "b:9092", "group.id": "lake-writer",
              "enable.auto.commit": False, "auto.offset.reset": "earliest"})
c.subscribe(["pedidos"])
while True:
    msg = c.poll(1.0)
    if msg is None or msg.error(): continue
    process(msg)               # idempotente (upsert/dedupe)
    c.commit(msg)              # só após a saída estar durável
```

### Pontos de atenção

- **`auto.offset.reset`** — onde começar sem offset salvo (`earliest` vs `latest`).
- **Rebalanceamento** — ao entrar/sair consumidores, partições são reatribuídas (pausa breve; use
  *cooperative* rebalancing).
- **`max.poll.interval.ms`** — processar demais entre `poll`s causa expulsão do grupo.
- **Lag** — distância entre o último offset e o consumido: métrica-chave de saúde.
- **Deserialização** com schema registry; trate mensagens inválidas (dead letter topic).

## Erros comuns

- Auto-commit + processamento falho → perda silenciosa.
- Consumidor não-idempotente com at-least-once → duplicatas.
- Processamento lento estourando `max.poll.interval.ms` (rebalanço em loop).
- `acks=1` para dados críticos; sem idempotência no producer.
- Ignorar *poison pills* (mensagem que sempre falha trava a partição) — use DLQ.

## Boas práticas

- Producer: `acks=all`, idempotência, compressão, chave intencional.
- Consumer: commit manual pós-processamento, idempotência, DLQ, monitorar lag.
- Fechar clientes graciosamente (flush/close) para evitar perdas.

## Relação com outros conceitos

- [Kafka](../02-apache-kafka/README.md), [partitions/offsets](../04-partitions-offsets-consumer-groups/README.md),
  [backpressure](../06-backpressure/README.md), [idempotência](../../09-etl-elt/07-idempotency-retries/README.md).
- [Projeto 07](../../projects/07-kafka/README.md).

## Exercícios

1. Escreva um producer idempotente com `acks=all`, chave por `order_id`.
2. Escreva um consumer com commit manual que grava em arquivo de forma idempotente.
3. Explique por que processar lento causa rebalanços e como evitar.
4. Projete uma DLQ para mensagens que falham a validação.

## Referências

- Documentação do Kafka (Producer/Consumer configs); confluent-kafka-python.
- Narkhede et al., *Kafka: The Definitive Guide* — caps. 3–4.
