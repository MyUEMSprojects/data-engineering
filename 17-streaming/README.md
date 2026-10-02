# 17 — Streaming

> 🟣 Nível 5 — Distributed Systems · Pré:
> [01/06 — Batch vs Streaming](../01-foundations/06-batch-vs-streaming/README.md),
> [16 — Distributed Processing](../16-distributed-processing/README.md) · Próximo:
> [18 — Message Brokers](../18-message-brokers/README.md)

**Streaming** é processar dados **contínuos e ilimitados** (*unbounded*), evento a evento, com baixa
latência — em contraste com o [batch](../01-foundations/06-batch-vs-streaming/README.md). É o que
permite fraude em tempo real, dashboards ao vivo, alertas e personalização instantânea. Também é
**mais difícil** que batch: lida com tempo, ordem, eventos atrasados, estado e garantias de entrega.

## Por que importa (e o aviso)

Streaming abre casos de uso que batch não alcança. Mas é **mais complexo e caro de operar** —
só vá para streaming quando a **latência for um requisito real** (não um desejo). Comece batch; migre o
que precisar.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Batch vs Streaming (processamento)](01-batch-vs-streaming/README.md) | O paradigma de stream processing |
| 02 | [Event-driven architecture](02-event-driven-architecture/README.md) | Sistemas orientados a eventos |
| 03 | [Tempo e janelas](03-time-and-windows/README.md) | Event/processing time, windows, watermarks |
| 04 | [Delivery semantics](04-delivery-semantics/README.md) | at-most/at-least/exactly-once |
| 05 | [Stateful processing](05-stateful-processing/README.md) | Estado em streaming |
| 06 | [Kafka Streams](06-kafka-streams/README.md) | Processamento sobre Kafka |
| 07 | [Apache Flink](07-flink/README.md) | True streaming de baixa latência |
| 08 | [Spark Structured Streaming](08-spark-structured-streaming/README.md) | Streaming no Spark (micro-batch) |

## Dependências internas

```text
Batch vs Streaming ─► Event-driven architecture
         │
         ▼
Tempo e janelas ─► Delivery semantics ─► Stateful processing
         │
         ▼
Kafka Streams / Flink / Spark Structured Streaming (engines)
```

## Checkpoint

- [ ] Explicar stream processing (unbounded) e quando usá-lo vs batch.
- [ ] Descrever arquitetura orientada a eventos e seus trade-offs.
- [ ] Diferenciar event time de processing time; explicar windows e watermarks.
- [ ] Explicar at-most/at-least/exactly-once e como exactly-once é alcançado na prática.
- [ ] Explicar processamento com estado e checkpoints de estado.
- [ ] Comparar Kafka Streams, Flink e Spark Structured Streaming.

## Referências do módulo

- Akidau, T. et al. *Streaming Systems*. O'Reilly, 2018 (a referência).
- Kleppmann, M. *DDIA* — cap. 11 (stream processing).
- Documentação de Apache Flink, Kafka Streams, Spark Structured Streaming.
