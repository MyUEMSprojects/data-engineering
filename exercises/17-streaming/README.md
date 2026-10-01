# Exercícios — Módulo 17: Streaming

Teoria em [17-streaming](../../17-streaming/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Tempo de evento × tempo de processamento

Um evento do usuário é gerado às 12:00:05, fica 3 minutos offline e chega às 12:03:10. Qual é o tempo de evento e o de processamento? Em que janela de 1 min ele deve contar?

<details><summary>Gabarito</summary>

Evento = **12:00:05**; processamento = **12:03:10**. Deve contar na janela **[12:00, 12:01)** (tempo de evento) — janelas por tempo de processamento dariam resultados que mudam a cada reprocessamento. Ver [tempo e janelas](../../17-streaming/03-time-and-windows/README.md).
</details>

## 2. 🟢 Conceitual — Watermark

O que é um watermark e qual o trade-off ao escolher a tolerância (ex.: 30 s × 10 min)?

<details><summary>Gabarito</summary>

Watermark é a estimativa de "até que tempo de evento já recebi tudo" (≈ máximo tempo de evento visto − tolerância). Tolerância **maior**: resultado mais completo, mas mais **latência** e **estado**. **Menor**: respostas rápidas, mas **descarta** mais eventos tardios. Meça o atraso real da fonte. Ver [Projeto 08](../../projects/08-streaming/README.md).
</details>

## 3. 🔵 Implementação — Contagem em janelas

Escreva a agregação do Spark Structured Streaming: visualizações por página em janelas **tumbling** de 1 minuto com watermark de 2 minutos, deduplicando por `event_id`.

<details><summary>Gabarito</summary>

```python
from pyspark.sql import functions as F
out = (events.withWatermark("event_time", "2 minutes")
       .dropDuplicatesWithinWatermark(["event_id"])
       .groupBy(F.window("event_time", "1 minute"), "page")
       .agg(F.count("*").alias("views")))
```

A ordem importa: **watermark → dedup → agregação**. `dropDuplicates` sem watermark manteria estado para sempre. Implementado e verificado no [Projeto 08](../../projects/08-streaming/README.md).
</details>

## 4. 🔵 Debugging — Contagem que "muda sozinha"

O painel mostra 100 views para a janela 12:00 e, minutos depois, 112. É bug? Qual configuração controla até quando isso pode acontecer?

<details><summary>Gabarito</summary>

Não é bug: **eventos tardios** (dentro da tolerância do watermark) atualizam janelas já emitidas (*update mode*). Depois que o watermark passa do fim da janela, ela **fecha** e novos atrasados são descartados. Comunique "resultado provisório até X". Ver [processamento com estado](../../17-streaming/05-stateful-processing/README.md).
</details>

## 5. 🟣 Arquitetura — Semânticas de entrega

Um consumidor lê do Kafka e escreve num banco. Descreva como obter efeito **exactly-once** e o que acontece se o processo cair entre gravar e confirmar o offset.

<details><summary>Gabarito</summary>

*At-least-once* (commit **depois** de gravar) + **destino idempotente** (chave natural/upsert/livro-razão) ⇒ efeito *exactly-once*. Se cair entre gravar e commitar, o lote é **reentregue** e reaplicado sem duplicar. O inverso (commit antes) arrisca **perder** dados. Alternativa: transações Kafka (só dentro do ecossistema). Demonstrado no [Projeto 07](../../projects/07-kafka/README.md). Ver [semânticas](../../17-streaming/04-delivery-semantics/README.md).
</details>

## 6. 🟣 Arquitetura — Lambda × Kappa

Compare as arquiteturas Lambda e Kappa. Quando manter uma camada batch separada ainda faz sentido?

<details><summary>Gabarito</summary>

**Lambda:** batch (preciso) + speed (rápido) + merge na consulta — duas bases de código. **Kappa:** tudo como stream, reprocessamento relendo o log. Kappa simplifica, mas exige log com retenção longa e engine capaz de reprocessar em escala. Batch separado ainda faz sentido para **reprocessamento histórico massivo barato**, correções complexas e quando o custo de manter estado em streaming é proibitivo. Ver [batch vs streaming](../../17-streaming/01-batch-vs-streaming/README.md).
</details>
