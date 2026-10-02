# Batch vs Streaming

> 🟢 Foundations · Parte de [01 — Fundamentos](../README.md)

## O que é

São os dois paradigmas fundamentais de processamento de dados:

- **Batch** — processa um **conjunto delimitado** de dados (um "lote"), em
  intervalos. Ex.: "toda madrugada, processar as vendas do dia anterior".
- **Streaming** — processa dados **contínuos e ilimitados** (um "fluxo"), evento
  a evento, logo após chegarem. Ex.: "para cada clique, atualizar a contagem em
  tempo real".

A diferença essencial é a **fronteira dos dados**: batch opera sobre dados
*bounded* (com início e fim); streaming, sobre dados *unbounded* (que nunca
"terminam").

## Por que os dois existem

Batch é mais **simples, barato e fácil de garantir correção** — você tem todos os
dados, pode reprocessar à vontade. Streaming entrega **frescor** (baixa
latência), essencial quando decisões não podem esperar horas. Cada um resolve uma
necessidade diferente de **latência vs custo/complexidade**.

## Como funciona cada um

### Batch

```text
coleta dados por um período ─► dispara job agendado ─► processa o lote inteiro
─► grava resultado ─► espera o próximo ciclo
```

- Disparado por [scheduling](../../10-data-pipelines/03-scheduling/README.md)
  (cron, Airflow) ou por chegada de arquivo.
- Latência = tamanho do intervalo (minutos a horas).
- Fácil de tornar [idempotente](../../09-etl-elt/07-idempotency-retries/README.md)
  e de fazer [backfill](../../09-etl-elt/08-backfill/README.md).
- Motores típicos: [Spark](../../16-distributed-processing/README.md),
  SQL em [warehouse](../../13-data-warehouse/README.md),
  [dbt](../../28-dbt/README.md).

### Streaming

```text
eventos chegam continuamente ─► motor processa cada evento/janela ─► atualiza
estado/saída em (quase) tempo real
```

- Alimentado por um log/broker ([Kafka](../../18-message-brokers/README.md)).
- Latência de milissegundos a segundos.
- Exige lidar com [tempo, janelas e watermarks](../../17-streaming/03-time-and-windows/README.md),
  [estado](../../17-streaming/05-stateful-processing/README.md) e
  [delivery semantics](../../17-streaming/04-delivery-semantics/README.md).
- Motores típicos: [Flink](../../17-streaming/07-flink/README.md),
  [Kafka Streams](../../17-streaming/06-kafka-streams/README.md),
  [Spark Structured Streaming](../../17-streaming/08-spark-structured-streaming/README.md).

## Comparação

| Aspecto | Batch | Streaming |
| --- | --- | --- |
| Dados | *Bounded* (lotes) | *Unbounded* (fluxo) |
| Latência | Minutos a horas | ms a segundos |
| Complexidade | Menor | Maior (estado, tempo, ordem) |
| Custo operacional | Menor | Maior (roda 24/7) |
| Correção/reprocesso | Fácil (rerodar o lote) | Difícil (replay do log) |
| Throughput | Altíssimo por lote | Alto e contínuo |
| Casos | Relatórios, ETL diário, ML training | Fraude, alertas, dashboards ao vivo |

## Micro-batch: o meio-termo

Alguns motores (Spark Structured Streaming no modo padrão) processam o fluxo em
**micro-lotes** muito pequenos (ex.: a cada segundo). Fica entre os dois: quase a
simplicidade do batch com latência baixa (mas não mínima). Flink, por contraste,
é *true streaming* (evento a evento), com latência menor.

## Quando usar cada um

**Use batch quando:**

- A decisão tolera atraso (relatórios, faturamento, ML training).
- Você precisa de correção exata e reprocessamento simples.
- Custo e simplicidade importam (a maioria dos casos!).

**Use streaming quando:**

- A latência é parte do requisito (fraude, trading, alertas, personalização ao
  vivo, monitoramento).
- O valor do dado decai rápido com o tempo.

> Regra prática: **comece batch.** Só vá para streaming quando a latência for um
> requisito real, não um desejo. Streaming mal justificado é custo e bug a mais.

## Relação com arquiteturas

- **Lambda** combina um caminho batch e um streaming (ver
  [sistemas de dados](../04-data-systems/README.md)).
- **Kappa** trata tudo como stream e faz batch via *replay* do log.

## Erros comuns

- Adotar streaming por "modernidade" sem requisito de latência.
- Esquecer que streaming exige lidar com **eventos atrasados e fora de ordem**
  ([watermarks](../../17-streaming/03-time-and-windows/README.md)).
- Achar que batch é "legado" — é o paradigma dominante e correto para a maioria
  dos pipelines analíticos.

## Relação com outros conceitos

- Aprofundado no nível 5: [streaming](../../17-streaming/README.md) e
  [brokers](../../18-message-brokers/README.md).
- Interage com [OLTP vs OLAP](../07-oltp-vs-olap/README.md) e com o
  [ciclo de vida dos dados](../03-data-lifecycle/README.md) (ingestão).

## Exercícios

1. **Classificação.** Para cada caso, escolha batch ou streaming e justifique:
   (a) relatório fiscal mensal; (b) bloqueio de cartão por fraude; (c) treino
   diário de modelo; (d) contador de usuários online.
2. **Trade-off.** Uma empresa quer "dashboards em tempo real" para dados que
   mudam uma vez por dia. O que você recomenda e por quê?
3. **Arquitetura.** Esboce como o mesmo pipeline de "vendas" poderia existir em
   batch e em streaming, e o que muda em complexidade.

## Referências

- Akidau, T. et al. *Streaming Systems*. O'Reilly, 2018 — caps. 1–2.
- Kleppmann, M. *Designing Data-Intensive Applications*. O'Reilly, 2017 — cap. 11
  (stream processing) e cap. 10 (batch).
- Documentação do Apache Flink — conceitos de *bounded vs unbounded streams*.
