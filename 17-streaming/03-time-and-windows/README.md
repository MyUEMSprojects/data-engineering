# Tempo e janelas

> 🟣 Distributed Systems · Parte de [17 — Streaming](../README.md)

## O que é

Em streaming, como os dados são [unbounded](../01-batch-vs-streaming/README.md), você não agrega "tudo"
— agrega **janelas (windows)** de tempo. E "tempo" é ambíguo: o momento em que o evento **ocorreu**
(event time) raramente é o momento em que você o **processa** (processing time). Lidar com essa
diferença — e com eventos que chegam **atrasados** — é o conceito mais importante (e mais errado) do
streaming. Os **watermarks** são a ferramenta central para isso.

## Event time vs processing time

- **Event time** — quando o evento **realmente aconteceu** (timestamp no próprio evento: a hora do
  clique).
- **Processing time** — quando o sistema **processou** o evento (relógio do processador).
- **Ingestion time** — quando o evento entrou no sistema (meio-termo).

```text
clique às 12:00:00 (event time)
  → viaja pela rede, fica no Kafka, há atraso...
  → processado às 12:00:07 (processing time)   ← 7s depois!
```

Por que importa: se você agrega "vendas por minuto" por **processing time**, um evento das 11:59 que
chega às 12:01 vai para o minuto errado → **resultado incorreto**. Para correção, agregue por **event
time**. Mas event time traz o problema dos eventos atrasados (abaixo).

## Janelas (windows)

Formas de agrupar eventos em intervalos para agregar:

### Tumbling (fixas, sem sobreposição)

```text
[00:00–00:05) [00:05–00:10) [00:10–00:15) ...   cada evento em exatamente uma janela
```
Ex.: "total de vendas a cada 5 min".

### Sliding (deslizantes, com sobreposição)

```text
[00:00–00:05) [00:01–00:06) [00:02–00:07) ...   um evento pode cair em várias janelas
```
Ex.: "média móvel dos últimos 5 min, atualizada a cada 1 min".

### Session (sessão, por inatividade)

Agrupa eventos próximos no tempo, fechando a janela após um *gap* de inatividade (ex.: "sessão de
navegação do usuário: fecha após 30 min sem evento"). Tamanho variável.

### Global

Uma janela única para todo o stream (com *trigger* customizado).

## O problema dos eventos atrasados (late events)

Com event time, um evento pode chegar **depois** de sua janela "deveria" ter fechado (rede, buffer,
dispositivo offline). Pergunta central: **quanto tempo esperar** antes de emitir o resultado de uma
janela? Esperar pouco → perde atrasados (resultado incompleto). Esperar muito → latência alta. O
**watermark** responde isso.

## Watermarks

Um **watermark** é uma marca que afirma: *"acredito que já recebi todos os eventos com event time até
T"*. É uma **heurística** de progresso do event time. Quando o watermark passa do fim de uma janela, a
janela é considerada "completa" e seu resultado é emitido.

```text
watermark = max(event_time visto) - atraso_permitido (ex.: 10s)
→ "janelas que terminam antes do watermark podem fechar"
```

- **Atraso permitido (allowed lateness)** — você configura quanto tolerar; é o trade-off
  **latência vs completude**.
- Eventos que chegam **depois** do watermark/allowed lateness são **late** — descartados ou tratados à
  parte (ex.: emitidos como atualização, ou enviados a um [dead letter](../../09-etl-elt/11-handling-failures/README.md)).

```text
latência baixa  ←──── atraso permitido ────→  completude alta
(fecha rápido, pode perder atrasados)    (espera mais, pega atrasados)
```

## Triggers

Quando emitir o resultado de uma janela: no watermark (padrão), antecipadamente (resultados parciais
que se atualizam), ou após (atualizações com atrasados). Permite entregar um resultado rápido e
refiná-lo quando chegam atrasados.

## Por que event time + watermark é "o jeito certo"

Processar por event time com watermarks dá resultados **corretos e determinísticos** (independentes de
quando o processamento rodou) — você pode reprocessar o log e obter o mesmo resultado. Processar por
processing time é mais simples mas dá resultados que dependem do timing do sistema (não reproduzíveis,
errados sob atraso).

## Suporte nas engines

- **[Flink](../07-flink/README.md)** — suporte de event time/watermarks de primeira classe (o modelo de
  referência).
- **[Spark Structured Streaming](../08-spark-structured-streaming/README.md)** — `withWatermark` +
  windows por event time.
- **[Kafka Streams](../06-kafka-streams/README.md)** — windows e *grace period* para atrasados.

## Erros comuns

- Agregar por **processing time** quando a correção exige **event time** (resultados errados sob
  atraso).
- Não configurar watermark/allowed lateness (perde atrasados silenciosamente ou espera para sempre).
- Allowed lateness curto demais (descarta atrasados legítimos) ou longo demais (latência/estado
  crescente).
- Ignorar eventos late (sem tratá-los nem monitorá-los).

## Boas práticas

- Use **event time** para correção; defina **watermark** com allowed lateness pelo trade-off real.
- Escolha o tipo de janela pelo caso (tumbling/sliding/session).
- Trate eventos late explicitamente (atualizar resultado, dead letter, ou descartar com métrica).
- Monitore o watermark lag (quão atrás o event time está).

## Relação com outros conceitos

- [Stateful processing](../05-stateful-processing/README.md) (janelas guardam estado),
  [delivery semantics](../04-delivery-semantics/README.md).
- Engines: [Flink](../07-flink/README.md), [Spark](../08-spark-structured-streaming/README.md),
  [Kafka Streams](../06-kafka-streams/README.md).

## Exercícios

1. Dê um exemplo concreto em que agregar por processing time dá o resultado errado e event time
   corrige.
2. Diferencie tumbling, sliding e session windows com um caso de uso de cada.
3. Explique o que é um watermark e o trade-off do allowed lateness.
4. Descreva como tratar um evento que chega depois do watermark.

## Referências

- Akidau, T. et al. *Streaming Systems* — caps. 2–4 (tempo, janelas, watermarks).
- Akidau, T. "The world beyond batch: Streaming 101/102" (artigos).
- Documentação de event time/watermarks do Flink e Spark.
