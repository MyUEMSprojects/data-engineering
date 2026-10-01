# Apache Flink

> 🟣 Distributed Systems · Parte de [17 — Streaming](../README.md)

## O que é

**Apache Flink** é um framework/engine distribuído de processamento de **streams com estado**, com
*true streaming* (evento a evento), baixa latência, suporte de primeira classe a **event time** e
**exactly-once**. Trata batch como caso especial de stream (*bounded stream*), unificando os dois
modelos.

## Por que é a referência em streaming

- **Event time e watermarks nativos** — o modelo mais completo (ver
  [tempo e janelas](../03-time-and-windows/README.md)).
- **Estado robusto** — *keyed state*, state backends (heap/RocksDB), estado de TBs.
- **Exactly-once** via checkpoints distribuídos + two-phase commit em sinks.
- **Baixa latência** (ms) e alto throughput.
- **Múltiplas fontes/sinks** (Kafka, arquivos, bancos, lakehouse) — não preso ao Kafka.

## Arquitetura

```text
Client ─► JobManager (coordena, agenda, checkpoints)
              └─► TaskManagers (executam tasks em slots, mantêm estado)
```

- **JobManager** — planeja o job (dataflow graph), coordena checkpoints/recuperação.
- **TaskManagers** — workers com *slots*; cada operador roda em paralelo (subtasks) particionado por
  chave.
- Roda em Kubernetes, YARN, standalone ou serviços gerenciados.

## Checkpoints e savepoints

- **Checkpoint** — snapshot periódico e consistente do estado + posição das fontes (algoritmo
  Chandy-Lamport com *barriers*). Em falha, restaura do último checkpoint → [exactly-once](../04-delivery-semantics/README.md)
  no estado (ver [stateful](../05-stateful-processing/README.md)).
- **Savepoint** — snapshot **manual** para upgrades/mudanças de lógica/migração sem perder estado.

## APIs

| API | Nível | Uso |
| --- | --- | --- |
| **DataStream** | baixo | controle total (estado, timers, event time) |
| **Table API / Flink SQL** | alto | SQL contínuo sobre streams e batch |
| **PyFlink** | — | Python sobre as APIs acima |

```sql
-- Flink SQL: agregação em janela tumbling por event time
SELECT window_start, uf, SUM(valor) AS receita
FROM TABLE(TUMBLE(TABLE pedidos, DESCRIPTOR(event_ts), INTERVAL '5' MINUTES))
GROUP BY window_start, window_end, uf;
```

Define-se o watermark na DDL da tabela (`WATERMARK FOR event_ts AS event_ts - INTERVAL '10' SECOND`).

## Casos de uso fortes

- Detecção de fraude/anomalia em tempo real, alertas, CEP (padrões de eventos).
- Agregações/enriquecimento contínuos com estado grande.
- Ingestão streaming para [lakehouse](../../15-lakehouse/README.md) (Iceberg/Hudi sinks).
- Real-time analytics (ver [advanced](../../30-advanced/README.md)).

## Trade-offs

- **Curva de aprendizado** alta (tempo, estado, checkpoints, tuning).
- **Operação pesada** self-hosted (cluster, state backends, backpressure) — há opções gerenciadas.
- Overkill para transformações simples sobre Kafka (use [Kafka Streams](../06-kafka-streams/README.md)).
- PyFlink é menos maduro/performante que JVM em alguns casos.

## Flink vs Kafka Streams vs Spark SS

| | Flink | [Kafka Streams](../06-kafka-streams/README.md) | [Spark SS](../08-spark-structured-streaming/README.md) |
| --- | --- | --- | --- |
| Modelo | true streaming | true streaming | micro-batch (padrão) |
| Latência | ms | ms | ~segundos |
| Deploy | cluster | biblioteca | cluster Spark |
| Fontes/sinks | muitas | Kafka | muitas |
| Event time/estado | **melhor** | bom | bom |

## Erros comuns

- Checkpoint intervalar mal ajustado (muito curto = overhead; longo = restore lento).
- Estado sem TTL → crescimento ilimitado.
- Watermark mal configurado (atrasados perdidos ou latência alta).
- Sink não-idempotente/transacional quebrando exactly-once fim-a-fim.
- Ignorar *backpressure* (gargalo a jusante).

## Boas práticas

- RocksDB para estado grande; TTL; incremental checkpoints.
- Savepoints antes de upgrades; UIDs estáveis nos operadores.
- Monitore checkpoint duration, backpressure, watermark lag.
- Use Flink SQL quando possível; DataStream para lógica custom.

## Relação com outros conceitos

- [Janelas/watermarks](../03-time-and-windows/README.md), [stateful](../05-stateful-processing/README.md),
  [delivery semantics](../04-delivery-semantics/README.md), [Kafka](../../18-message-brokers/README.md).
- Lakehouse sinks: [Iceberg](../../15-lakehouse/05-apache-iceberg/README.md); avançado:
  [real-time analytics](../../30-advanced/README.md).

## Exercícios

1. Escreva Flink SQL com watermark e agregação em janela tumbling.
2. Explique checkpoint vs savepoint e quando usar cada.
3. Descreva como Flink alcança exactly-once fim-a-fim com Kafka source e sink.
4. Escolha entre Flink, Kafka Streams e Spark SS para 3 cenários.

## Referências

- Documentação oficial do Apache Flink (flink.apache.org).
- Akidau, T. et al. *Streaming Systems*; Hueske, F.; Kalavri, V. *Stream Processing with Apache Flink*.
