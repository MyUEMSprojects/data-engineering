# Real-time analytics (OLAP de baixa latência)

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: especialização*

## O que é

**Real-time analytics** é executar **consultas analíticas (agregações/filtros/group by) sobre dados
muito recentes**, com **latência de milissegundos a poucos segundos** e **alta concorrência** — frequentemente
para **usuários finais/aplicações** (dashboards embutidos em produto, métricas ao vivo, personalização,
detecção de fraude, observabilidade). Combina **ingestão de streaming** com **OLAP rápido**.

## Por que um warehouse tradicional não basta

[Warehouses](../../13-data-warehouse/README.md) são ótimos para análise **exploratória/BI interno**, mas:

- **Latência**: consultas em segundos–minutos e carga em lote/micro-lote (frescor de minutos–horas).
- **Concorrência**: dezenas/centenas de consultas simultâneas são custosas; milhares de usuários de um
  produto externo inviabilizam.
- **Custo por consulta** alto em uso user-facing.

OLTP ([Postgres](../../06-databases/02-postgresql/README.md)) não agrega bem em escala. Daí uma categoria:
**bancos OLAP em tempo real**.

## O trio de requisitos

```text
FRESCOR:      dados disponíveis para consulta em segundos após o evento (ingestão streaming)
LATÊNCIA:     consultas p95 em ms–poucos s (agregações sobre bilhões de linhas)
CONCORRÊNCIA: milhares de consultas/s (analytics user-facing)
```

## Arquitetura típica

```text
Eventos/CDC ─► Kafka ─► [Stream processing opcional: enriquecer/filtrar (Flink/Kafka Streams)] ─► OLAP em tempo real ─► APIs/dashboards/apps
                                  │                                                  ▲
                                  └─────────► lake/lakehouse (histórico completo) ───┘ (batch/backfill, tabelas offline)
```

- **Ingestão** streaming nativa (Kafka/Kinesis/Pulsar) **+** batch (arquivos do lake).
- Pré-agregação/*rollups* e índices para consultas rápidas.
- Frequentemente uma arquitetura **híbrida** (**real-time + offline**), como Lambda/Kappa
  ([sistemas de dados](../../01-foundations/04-data-systems/README.md)).

## As engines (o que as torna rápidas)

Todas: **armazenamento colunar**, **compressão/encoding**, **índices especializados**, **segmentação por
tempo**, **processamento vetorizado/paralelo**, **pré-agregação**.

| Engine | Características | Bom para |
| --- | --- | --- |
| **Apache Pinot** (LinkedIn/Uber) | índices ricos (inverted, star-tree, range, sorted), ingestão realtime+offline, tabelas híbridas, **alta concorrência** | analytics user-facing, "Who viewed my profile", dashboards embutidos |
| **Apache Druid** | segmentos por tempo, rollup na ingestão, índices bitmap, ingestão streaming/batch | séries temporais, eventos, observabilidade/ad-tech |
| **ClickHouse** | colunar muito rápido, engines MergeTree, SQL rico, ótimo custo/desempenho; self-hosted ou cloud | analytics de logs/eventos em alta escala; BI rápido |
| **StarRocks / Apache Doris** | MPP vetorizado, MySQL-compatível, joins melhores, MVs | analytics interativo, lakehouse acelerado |
| **Rockset (descontinuado/aquisição)**, **Materialize / RisingWave** | **SQL incremental** sobre streams (visões materializadas atualizadas continuamente) | views em tempo real com semântica SQL de streaming |
| **Elasticsearch/OpenSearch** | busca + agregações | logs/observabilidade/busca (menos ideal p/ analytics pesado) |
| **TimescaleDB/QuestDB/InfluxDB** | séries temporais | métricas/IoT |
| **Warehouses com ingestão rápida** (BigQuery streaming, Snowflake Snowpipe Streaming/Dynamic Tables) | frescor de segundos–minutos; concorrência limitada | casos de frescor moderado sem nova engine |

> O panorama muda rápido (ex.: aquisições/descontinuações). Confirme o estado atual de cada projeto/produto.

## Streaming SQL vs OLAP em tempo real

Duas abordagens complementares:

- **Streaming SQL / visões materializadas incrementais** ([Flink SQL](../../17-streaming/07-flink/README.md),
  Materialize, RisingWave, ksqlDB): a **consulta é fixa** e roda **continuamente**, mantendo o resultado
  atualizado (push). Ótimo para **métricas conhecidas** e alertas.
- **OLAP em tempo real** (Pinot/Druid/ClickHouse): **consultas ad hoc/parametrizadas** sobre dados recentes
  (pull) com latência baixa. Ótimo para **exploração/filtros dinâmicos** de usuários.

Muitas vezes combinam-se: Flink pré-processa → Pinot/ClickHouse serve.

## Modelagem para real-time analytics

- **Desnormalize** (tabela larga/"flattened"): joins são caros; **enriqueça no stream** antes de gravar
  ([denormalização](../../07-data-modeling/02-normalization-denormalization/README.md)).
- **Pré-agregue** (rollups, star-tree, MVs) para consultas previsíveis.
- **Particione/segmente por tempo** e escolha **chaves de ordenação/índices** conforme os filtros.
- **Dimensões de baixa cardinalidade** como dicionários; cuidado com **alta cardinalidade** (custo/índices).
- **Upserts/CDC**: algumas engines suportam atualização (Pinot upsert, ClickHouse ReplacingMergeTree) —
  entenda o custo e a semântica.
- **Retenção**: hot (recente, rápido) vs histórico no lake.

## Trade-offs

- **Mais um sistema** para operar (consistência com o lake/warehouse, duplicação de dados).
- **Joins/consultas complexas** limitadas (varia por engine); modelagem mais rígida.
- **Custo**: indexar/manter dados quentes em memória/SSD.
- **Consistência eventual** entre real-time e batch; reconciliação.
- **Exatidão vs latência** (dados tardios, correções — [watermarks](../../17-streaming/03-time-and-windows/README.md)).

## Quando usar / não usar

- **Use** quando o **produto/negócio exige** frescor de segundos + latência baixa + alta concorrência
  (analytics user-facing, fraude, observabilidade, personalização).
- **Não use** se BI interno com atraso de minutos/horas basta — o [warehouse/lakehouse](../../13-data-warehouse/README.md)
  é mais simples e barato. Muitos "preciso de tempo real" são "preciso de batch frequente".

## Erros comuns

- Adotar OLAP em tempo real sem requisito real de latência/concorrência (custo e complexidade).
- Modelar normalizado e esperar joins rápidos.
- Ignorar dados tardios/correções (números que "mudam").
- Não prever a história/offline (apenas hot) ou reconciliação com o lake.
- Alta cardinalidade sem planejamento (índices/memória explodem).
- Tratar como substituto do warehouse.

## Boas práticas

- Defina SLOs de frescor/latência/concorrência primeiro; escolha a engine pelo padrão de consulta.
- Desnormalize/enriqueça no stream; pré-agregue; segmente por tempo.
- Arquitetura híbrida (hot + lake) com reconciliação; trate eventos tardios.
- Monitore lag de ingestão, latência de consulta (p95/p99), custo.

## Relação com outros conceitos

- [Streaming](../../17-streaming/README.md), [Kafka](../../18-message-brokers/README.md),
  [warehouse](../../13-data-warehouse/README.md), [lakehouse](../../15-lakehouse/README.md),
  [Flink](../../17-streaming/07-flink/README.md), [freshness](../../24-observability/06-data-freshness/README.md).

## Exercícios

1. Para um dashboard embutido num app com 5.000 usuários simultâneos e dados de 5 s de idade, escolha a
   arquitetura e justifique (vs warehouse).
2. Modele a tabela larga de eventos de clique para Pinot/ClickHouse (chaves, tempo, pré-agregações).
3. Diferencie streaming SQL (Materialize/Flink) e OLAP em tempo real (Pinot/Druid) com um caso para cada.
4. Descreva como reconciliar dados real-time com o histórico do lakehouse.

## Referências

- Documentação de Apache Pinot, Druid, ClickHouse, StarRocks/Doris, Materialize/RisingWave.
- Kleppmann, M. *DDIA* (cap. 11); artigos de engenharia de LinkedIn/Uber sobre Pinot.
