# Delivery semantics

> 🟣 Distributed Systems · Parte de [17 — Streaming](../README.md)

## O que é

**Delivery semantics** (garantias de entrega) definem **quantas vezes** um evento é processado quando
há falhas e retries num sistema de streaming distribuído. As três garantias clássicas: **at-most-once**,
**at-least-once** e **exactly-once**. Escolher (e entender) a garantia certa é essencial para a
**correção** dos dados.

## As três garantias

```text
at-most-once:   cada evento é processado 0 ou 1 vez   → pode PERDER eventos, nunca duplica
at-least-once:  cada evento é processado 1+ vezes      → nunca perde, pode DUPLICAR
exactly-once:   cada evento tem efeito como 1 vez       → não perde nem duplica (o ideal, o difícil)
```

| Garantia | Perde? | Duplica? | Custo/complexidade |
| --- | --- | --- | --- |
| At-most-once | sim | não | mínimo (rápido, descartável) |
| At-least-once | não | sim | médio (padrão comum) |
| Exactly-once | não | não | maior (precisa de mecanismos extras) |

## Por que exactly-once é difícil

Em sistemas distribuídos, falhas são inevitáveis (ver
[sistemas distribuídos](../../01-foundations/05-distributed-systems-fundamentals/README.md)). Se um
consumidor processa um evento e **cai antes de confirmar** (commitar o offset), ao reiniciar ele
reprocessa aquele evento → **duplicata** (at-least-once). Garantir que o **efeito** aconteça
exatamente uma vez, apesar de reprocessamentos, exige coordenação.

```text
consumidor processa evento X ─► grava resultado ─► [CRASH antes de commitar offset]
   → reinicia, reprocessa X ─► grava de novo ─► DUPLICATA
```

## Como exactly-once é alcançado na prática

Exactly-once "puro" na entrega é quase impossível; o que se faz é garantir **efeito exactly-once**,
por duas estratégias:

### 1. At-least-once + idempotência (a mais comum)

Entregue pelo menos uma vez (sem perder) e torne o **processamento idempotente** — reprocessar o mesmo
evento não muda o resultado (ver [idempotência](../../09-etl-elt/07-idempotency-retries/README.md)):

- **Upsert por chave** no destino (reprocessar sobrescreve, não duplica).
- **Deduplicação** por ID do evento ([dedupe](../../09-etl-elt/09-deduplication/README.md)).
- Escrita em partição/chave determinística.

> Esta é a abordagem pragmática dominante: "exactly-once" = at-least-once + processamento idempotente.

### 2. Transações end-to-end

A engine coordena, numa **transação**, o *consumo + processamento + escrita + commit do offset* de
forma atômica (tudo ou nada). Exemplos:

- **Kafka transactions** — produzir no tópico de saída **e** commitar o offset de leitura atomicamente
  (base do exactly-once do [Kafka Streams](../06-kafka-streams/README.md)).
- **[Flink](../07-flink/README.md)** — *checkpointing* distribuído (algoritmo Chandy-Lamport) +
  *two-phase commit* para sinks → exactly-once state **e** output.
- **[Spark Structured Streaming](../08-spark-structured-streaming/README.md)** — exactly-once com
  checkpoint de offsets + sinks idempotentes/transacionais.

O elo comum: **checkpoint do offset só é confirmado junto/depois** de a saída estar durável — nunca
antes (senão perde dados). Ver [checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md).

## Offsets e commit (a raiz do problema)

O consumidor rastreia até onde leu via **offset** (ver
[offsets](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md)). **Quando** commitar
o offset decide a garantia:

```text
commit ANTES de processar  → at-most-once (se cair, pula o evento = perde)
commit DEPOIS de processar+gravar → at-least-once (se cair entre gravar e commitar, reprocessa = duplica)
commit atômico com a gravação → exactly-once (efeito)
```

## Escolhendo a garantia

- **At-most-once** — só quando perder dados é aceitável e latência/throughput máximos importam (ex.:
  métricas aproximadas, telemetria descartável).
- **At-least-once** — padrão seguro **se** o processamento for idempotente. A escolha mais comum.
- **Exactly-once (efeito)** — quando duplicatas são inaceitáveis (ex.: contadores financeiros) e você
  aceita o custo/complexidade; via transações ou at-least-once + idempotência.

## Fim-a-fim é o que importa

Uma garantia só vale **end-to-end**: fonte → processamento → sink. Um sink não-idempotente estraga o
exactly-once da engine. Garanta a garantia **em toda a cadeia** (fonte retentável, estado com
checkpoint, sink idempotente/transacional).

## Erros comuns

- Assumir exactly-once "de graça" sem configurar/entender (duplicatas silenciosas).
- Commitar offset **antes** de a saída estar durável (perde dados).
- At-least-once com processamento **não** idempotente → duplicatas.
- Engine exactly-once + sink não-idempotente (quebra a garantia no fim).
- Confundir "exactly-once de entrega" (quase impossível) com "efeito exactly-once" (viável).

## Boas práticas

- Default: **at-least-once + idempotência** (upsert/dedupe por chave/ID).
- Commit de offset **só após** a saída durável.
- Para exactly-once, use transações da engine **e** sinks idempotentes/transacionais (fim-a-fim).
- Monitore duplicatas/perdas; teste cenários de falha/reinício.

## Relação com outros conceitos

- [Idempotência](../../09-etl-elt/07-idempotency-retries/README.md),
  [dedupe](../../09-etl-elt/09-deduplication/README.md),
  [checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md),
  [offsets](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md).
- Engines: [Flink](../07-flink/README.md), [Kafka Streams](../06-kafka-streams/README.md),
  [Spark](../08-spark-structured-streaming/README.md).

## Exercícios

1. Explique, com o momento do commit do offset, como se obtém at-most/at-least/exactly-once.
2. Descreva a estratégia "at-least-once + idempotência" para um contador de eventos sem duplicar.
3. Explique por que um sink não-idempotente quebra o exactly-once da engine.
4. Dê um caso em que at-most-once é aceitável e outro em que exactly-once é obrigatório.

## Referências

- Kleppmann, M. *DDIA* — cap. 11 (exactly-once, dedup, transações).
- Akidau, T. et al. *Streaming Systems*.
- Documentação de exactly-once do Flink e do Kafka (transactions).
