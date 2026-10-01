# Sistemas de dados

> 🟢 Foundations · Parte de [01 — Fundamentos](../README.md)

## O que é

Um **sistema de dados** é a combinação de componentes que, juntos, armazenam e
processam dados para um propósito. Uma **plataforma de dados** é o arranjo desses
componentes em uma organização. Este tópico apresenta os *blocos de construção*
recorrentes e as *arquiteturas de referência* — o vocabulário que você vai
reencontrar em cada módulo.

## Por que existe

Nenhum sistema único resolve tudo: bancos operacionais são ruins para analytics;
warehouses são caros para dados brutos; filas não guardam histórico longo. Por
isso, plataformas de dados são **compostas** por vários sistemas especializados,
conectados por pipelines. Entender os blocos evita "usar um martelo para tudo".

## Blocos de construção

| Bloco | Papel | Exemplos |
| --- | --- | --- |
| **Fontes** | Onde o dado nasce | Postgres, APIs, Kafka, arquivos |
| **Ingestão** | Trazer dados para a plataforma | Airbyte, Kafka Connect, scripts |
| **Message brokers / logs** | Transporte e desacoplamento | [Kafka](../../18-message-brokers/02-apache-kafka/README.md), RabbitMQ |
| **Object storage** | Armazenamento barato em escala | S3, GCS, [MinIO](../../19-cloud/02-object-storage/README.md) |
| **Data lake** | Dados brutos/semiestruturados | lake sobre object storage |
| **Data warehouse** | Dados modelados p/ analytics | BigQuery, Snowflake |
| **Lakehouse** | Lake + ACID + warehouse | Delta, [Iceberg](../../15-lakehouse/05-apache-iceberg/README.md) |
| **Engines de processamento** | Transformar em escala | [Spark](../../16-distributed-processing/05-apache-spark/README.md), Flink |
| **Orquestrador** | Coordenar pipelines | [Airflow](../../11-orchestration/02-airflow/README.md), Dagster |
| **Transformação analítica** | Modelar no warehouse | [dbt](../../28-dbt/README.md) |
| **Serving** | Entregar ao consumidor | BI, APIs, feature store |
| **Transversais** | Governança, catálogo, observabilidade, segurança | ver módulos 24–27 |

## Arquiteturas de referência

### Pipeline analítico clássico (batch)

```text
Fontes ─► Ingestão ─► Data Lake (raw) ─► Processamento/dbt ─► Warehouse ─► BI
                                   └──────────► Features ─► ML
```

### Lambda architecture

Combina um **caminho batch** (preciso, com latência) e um **caminho speed/
streaming** (rápido, aproximado), unificados na camada de serving.

```text
Fontes ─┬─► Batch layer  ─► views batch ─┐
        └─► Speed layer  ─► views tempo-real ─┴─► Serving layer ─► consumo
```

*Trade-off:* lógica duplicada (batch + stream). Complexo de manter.

### Kappa architecture

Tudo é tratado como **stream**; batch vira "reprocessar o log do começo".
Simplifica ao remover a duplicação da Lambda, ao custo de exigir um log
retentivo e um motor de stream robusto. Ver
[streaming](../../17-streaming/README.md) e
[message brokers](../../18-message-brokers/README.md).

### Medallion (bronze/silver/gold)

Organização do lake/lakehouse em camadas de refino. Ver
[medallion](../../14-data-lake/03-medallion-architecture/README.md).

### Modern Data Stack

Conjunto de SaaS integrados: ingestão gerenciada (Fivetran/Airbyte) → warehouse
cloud (BigQuery/Snowflake) → transformação com [dbt](../../28-dbt/README.md) → BI.
Prioriza ELT e baixo esforço operacional. *Trade-off:* custo e *lock-in*.

### Data mesh

Abordagem organizacional (não só técnica): domínios donos de seus "dados como
produto", com governança federada. Ver [advanced](../../30-advanced/03-data-mesh/README.md).

## Como escolher uma arquitetura

Não existe "a melhor"; escolha pelo contexto:

- **Volume e latência** — precisa de tempo real? Streaming/Kappa. Relatórios
  diários? Batch simples.
- **Maturidade do time** — Modern Data Stack reduz operação; Spark/Kafka exigem
  mais engenharia.
- **Custo** — SaaS troca esforço por fatura; soluções self-hosted, o contrário.
- **Escala** — a maioria dos casos cabe em warehouse + dbt; só grandes volumes/
  variedade justificam lake/lakehouse + Spark.

> Princípio: **comece simples** (um warehouse bem modelado resolve muita coisa),
> adicione complexidade quando um problema real exigir.

## Trade-offs recorrentes

| Decisão | Opção A | Opção B |
| --- | --- | --- |
| Transformação | ETL (antes de carregar) | ELT (depois de carregar) |
| Latência | Batch (barato, atrasado) | Streaming (caro, fresco) |
| Validação | Schema-on-write | Schema-on-read |
| Build vs buy | Self-hosted (controle) | SaaS (velocidade) |
| Acoplamento | Direto | Desacoplado via broker |

## Erros comuns

- Adotar Lambda/streaming "porque é moderno" sem necessidade de tempo real.
- Montar um lake sem governança → *data swamp* (pântano de dados).
- Copiar a arquitetura de uma big tech para um volume mil vezes menor.

## Relação com outros conceitos

- Concretiza o [ciclo de vida dos dados](../03-data-lifecycle/README.md).
- Cada bloco é um módulo do repositório (storage → 13/14/15; processing → 16/17;
  orquestração → 11).
- Depende de [sistemas distribuídos](../05-distributed-systems-fundamentals/README.md).

## Exercícios

1. **Arquitetura.** Desenhe uma plataforma de dados para uma fintech que precisa
   de (a) relatórios regulatórios diários e (b) detecção de fraude em tempo real.
   Justifique cada bloco.
2. **Trade-off.** Quando a Lambda architecture se justifica apesar da duplicação
   de lógica? Quando Kappa é melhor?
3. **Simplificação.** Dado um projeto que usa Kafka + Spark + lake para gerar um
   relatório semanal de 10 MB, proponha uma arquitetura mais simples.

## Referências

- Kleppmann, M. *Designing Data-Intensive Applications*. O'Reilly, 2017 — cap. 1
  e parte III.
- Reis, J.; Housley, M. *Fundamentals of Data Engineering*. O'Reilly, 2022 —
  cap. 3 (arquitetura de dados).
- Marz, N.; Warren, J. *Big Data*. Manning, 2015 (Lambda architecture).
