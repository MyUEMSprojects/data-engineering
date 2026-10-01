# Batch vs Streaming (processamento)

> 🟣 Distributed Systems · Parte de [17 — Streaming](../README.md)

## O que é

Este tópico aprofunda o **stream processing** como paradigma de computação, a partir da distinção de
[batch vs streaming](../../01-foundations/06-batch-vs-streaming/README.md) vista nos fundamentos. Aqui o
foco é *como pensar* uma computação sobre dados **ilimitados (unbounded)** e o que isso muda em relação
a processar dados **delimitados (bounded)**.

## Bounded vs unbounded (a diferença essencial)

- **Batch** processa um dataset **bounded** — tem início e fim conhecidos. Você tem *todos* os dados;
  pode ordenar, reprocessar, calcular agregados exatos.
- **Streaming** processa um fluxo **unbounded** — nunca "termina". Você só viu *parte* dos dados a cada
  instante; precisa decidir **quando** emitir resultados (não dá para esperar "o fim").

```text
Batch:    [████████████] (dataset completo) ─► processa ─► resultado
Streaming: ──●──●──●──●──●──● ... (fluxo infinito) ─► processa contínuo ─► resultados parciais/janelas
```

Essa diferença gera **todos** os desafios únicos do streaming: tempo, janelas, eventos atrasados,
estado, garantias (os próximos tópicos).

## Micro-batch vs true streaming

Há duas formas de implementar stream processing:

- **Micro-batch** — processa o fluxo em **pequenos lotes** frequentes (ex.: a cada segundo). É o modelo
  do [Spark Structured Streaming](../08-spark-structured-streaming/README.md) (por padrão). Mais
  simples (reusa a engine batch), latência de ~segundos.
- **True streaming (event-at-a-time)** — processa **cada evento** assim que chega. É o modelo do
  [Flink](../07-flink/README.md) e do [Kafka Streams](../06-kafka-streams/README.md). Latência mínima
  (ms), mais complexo.

```text
Micro-batch:  junta eventos por ~1s → processa o lote → repete   (latência ~segundos)
True stream:  processa cada evento ao chegar                       (latência ~ms)
```

Trade-off: micro-batch troca latência por simplicidade/throughput; true streaming entrega latência
mínima ao custo de complexidade.

## A unificação batch + streaming

Teoria moderna (Dataflow model / *Streaming Systems*): **batch é um caso especial de streaming** (um
stream bounded). Engines como Flink e Spark permitem o **mesmo código** rodar em batch ou streaming.
Isso leva a arquiteturas como **Kappa** (tudo é stream; batch = reprocessar o log) — ver
[sistemas de dados](../../01-foundations/04-data-systems/README.md).

## O que muda ao programar streaming

| Aspecto | Batch | Streaming |
| --- | --- | --- |
| Completude | tem todos os dados | só uma parte a cada instante |
| Quando emitir resultado | no fim | contínuo / por [janela](../03-time-and-windows/README.md) |
| Tempo | implícito (o lote) | explícito ([event vs processing time](../03-time-and-windows/README.md)) |
| Eventos atrasados | não existem (tudo já chegou) | precisam de [watermarks](../03-time-and-windows/README.md) |
| Estado | efêmero (um job) | **persistente** entre eventos ([stateful](../05-stateful-processing/README.md)) |
| Falhas/reprocesso | rerodar o lote | [checkpoints de offset/estado](../../10-data-pipelines/04-checkpoints-idempotency/README.md) |
| Garantias | fáceis | [delivery semantics](../04-delivery-semantics/README.md) explícitas |

## Fontes e destinos de stream

- **Fonte**: um log/broker ([Kafka](../../18-message-brokers/README.md)), filas, [CDC](../../09-etl-elt/06-cdc/README.md).
- **Processamento**: Flink / Kafka Streams / Spark Structured Streaming.
- **Destino (sink)**: lake/lakehouse, warehouse, outro tópico Kafka, banco, dashboard, cache.

## Quando usar streaming

- Latência é **requisito** (fraude, alertas, trading, monitoramento, personalização ao vivo).
- O valor do dado **decai rápido** com o tempo.
- Há um fluxo contínuo natural (eventos, logs, IoT).

**Senão, use batch** (mais simples, barato, correção fácil). Muitos "preciso de streaming" são, na
verdade, "preciso de batch mais frequente".

## Erros comuns

- Adotar streaming sem requisito real de latência (complexidade/custo à toa).
- Esquecer os problemas de tempo/eventos atrasados (resultados errados).
- Tratar estado como efêmero (perder o acumulado em reinícios).
- Confundir micro-batch (segundos) com true streaming (ms) ao escolher a ferramenta.

## Boas práticas

- Comece batch; vá para streaming quando a latência exigir.
- Escolha micro-batch vs true streaming pela latência necessária.
- Prepare-se para tempo/janelas/watermarks e estado desde o design.
- Reaproveite código batch/stream quando a engine permitir (unificação).

## Relação com outros conceitos

- [Batch vs streaming (fundamentos)](../../01-foundations/06-batch-vs-streaming/README.md),
  [tempo e janelas](../03-time-and-windows/README.md), [stateful](../05-stateful-processing/README.md).
- Engines: [Flink](../07-flink/README.md), [Kafka Streams](../06-kafka-streams/README.md),
  [Spark Structured Streaming](../08-spark-structured-streaming/README.md).

## Exercícios

1. Explique por que "não dá para esperar o fim" torna o streaming fundamentalmente diferente do batch.
2. Diferencie micro-batch de true streaming com latências e um exemplo de engine de cada.
3. Para 3 casos, decida batch ou streaming e justifique.
4. Explique a ideia "batch é um caso especial de streaming" e a arquitetura Kappa.

## Referências

- Akidau, T. et al. *Streaming Systems* — caps. 1–2.
- Kleppmann, M. *DDIA* — cap. 11.
