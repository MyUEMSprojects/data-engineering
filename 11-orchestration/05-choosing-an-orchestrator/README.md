# Escolhendo um orquestrador

> 🔵 Pipelines · Parte de [11 — Orquestração](../README.md)

## O que é

Um guia de decisão entre os orquestradores — e, antes disso, se você **precisa** de um. A
escolha certa depende do contexto (time, escala, stack, filosofia), não de qual é "o melhor".

## Primeiro: você precisa de um orquestrador?

- **Não (ainda)** — se você tem **um ou dois** pipelines simples e isolados,
  [cron](../../02-linux-shell-environment/06-cron/README.md) +
  [scripts robustos](../../02-linux-shell-environment/05-shell-scripting/README.md) podem
  bastar. Não adicione um orquestrador pesado prematuramente (KISS).
- **Sim** — quando há **dependências entre pipelines**, necessidade de retries/backfill,
  observabilidade, SLAs e vários pipelines interligados. Aí o custo do orquestrador se paga.

## Os critérios de decisão

| Critério | Pergunta |
| --- | --- |
| **Filosofia** | task-centric ou asset/data-centric? |
| **Ecossistema/comunidade** | preciso de muitos conectores e profissionais no mercado? |
| **Dinamismo** | o pipeline muda de estrutura em runtime? |
| **Lineage/observabilidade de dados** | preciso disso nativo? |
| **Operação** | self-hosted (controle) ou gerenciado (menos esforço)? |
| **Maturidade do time** | já conhecem alguma ferramenta? |
| **Integração com dbt** | é central no meu stack? |
| **Streaming** | preciso de baixa latência? (orquestrador batch não serve) |

## Resumo das opções

| | [Airflow](../02-airflow/README.md) | [Dagster](../03-dagster/README.md) | [Prefect](../04-prefect/README.md) |
| --- | --- | --- | --- |
| Modelo | task-centric | asset/data-centric | flows pythônicos/dinâmicos |
| Lineage de dados | via extras | **nativo** | parcial |
| Dinamismo | limitado | moderado | **forte** |
| Curva de entrada | média | média | **baixa** |
| Ecossistema/mercado | **maior** | crescente | crescente |
| Testabilidade | ok | **forte** | boa |
| Melhor para | padrão de mercado, muitos conectores | plataformas analytics + dbt, observabilidade | simplicidade, fluxos dinâmicos |

## Recomendações por cenário

```text
"Padrão de mercado, muitos conectores, time já conhece"      → Airflow
"Stack analytics com dbt, quero lineage/observabilidade"      → Dagster
"Quero simplicidade e fluxos dinâmicos, time pequeno"         → Prefect
"Um pipeline simples só"                                      → cron (ainda não precisa)
"Baixa latência / tempo real"                                 → não é orquestrador: Flink/Kafka Streams
```

## Self-hosted vs gerenciado

Rodar um orquestrador em produção dá trabalho (scheduler, workers, DB, upgrades). Opções
gerenciadas reduzem esse esforço:

- **Airflow** — Astronomer, AWS MWAA, GCP Cloud Composer.
- **Dagster** — Dagster+.
- **Prefect** — Prefect Cloud.

Trade-off: gerenciado troca **esforço operacional** por **custo** e algum *lock-in*. Para
times pequenos, geralmente vale.

## O que NÃO é trabalho de orquestrador

- **Transformar** dados pesados (delegue a [dbt](../../28-dbt/README.md)/
  [Spark](../../16-distributed-processing/README.md)/SQL).
- **Streaming de baixa latência** (use [Flink/Kafka Streams](../../17-streaming/README.md)).
- Ser um [cron](../../02-linux-shell-environment/06-cron/README.md) glorificado (se é só
  isso, use cron).

## Migração e lock-in

Como os DAGs são código específico da ferramenta, trocar de orquestrador é custoso. Mitigue
mantendo a **lógica de transformação fora** do orquestrador (em dbt/Spark/funções puras), de
modo que só a "casca" de orquestração seja específica da ferramenta.

## Erros comuns

- Adotar um orquestrador pesado para um único script (over-engineering).
- Escolher pela moda em vez do contexto/time.
- Acoplar a lógica de transformação ao orquestrador (dificulta migração).
- Esperar streaming de um orquestrador batch.

## Boas práticas

- Comece simples; adote orquestrador quando a complexidade justificar.
- Escolha pela filosofia + ecossistema + time, não por hype.
- Mantenha transformação fora do orquestrador (reduz lock-in).
- Prefira gerenciado se o esforço operacional não compensa.

## Relação com outros conceitos

- Ferramentas: [Airflow](../02-airflow/README.md), [Dagster](../03-dagster/README.md),
  [Prefect](../04-prefect/README.md); conceitos: [01](../01-orchestration-concepts/README.md).
- Alternativa simples: [cron](../../02-linux-shell-environment/06-cron/README.md).
- Streaming (não-orquestrador): [17 — Streaming](../../17-streaming/README.md).

## Exercícios

1. Para 3 cenários (startup com 1 pipeline; plataforma analytics com dbt; time que precisa de
   fluxos dinâmicos), recomende um orquestrador e justifique.
2. Liste os critérios que você usaria para decidir self-hosted vs gerenciado.
3. Explique como manter a transformação fora do orquestrador reduz o lock-in.
4. Dê um caso em que a resposta certa é **não** usar orquestrador.

## Referências

- Documentação de Airflow, Dagster, Prefect.
- Reis & Housley, *Fundamentals of Data Engineering* — escolha de ferramentas.
