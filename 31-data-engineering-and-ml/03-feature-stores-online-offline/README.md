# Feature stores (online e offline)

> 🟣 ML Integration · Parte de [31 — DE + ML](../README.md)

## O que é

Uma **feature store** é a **camada de dados de ML** que **gerencia, armazena e serve features** de forma
**consistente entre treino e inferência**. Resolve: reuso de features, **point-in-time correctness**,
**training-serving skew**, descoberta/governança e latência de serving.

```text
                       ┌──────── Registry (definições, donos, versões, lineage) ────────┐
Fontes ─► pipelines ─► OFFLINE store (lake/warehouse)  ──materialização──► ONLINE store (Redis/DynamoDB/Cassandra)
(batch/stream)         └─ treino, backfill, point-in-time joins            └─ serving de baixa latência
```

> Uma feature store **não** é um banco mágico nem obrigatória: faz sentido quando há **múltiplos
> modelos/times**, necessidade de **serving online**, e dor real com skew/duplicação. Para um único modelo
> batch, tabelas de features bem versionadas podem bastar.

## Os dois "lados" da feature store

### Offline store

- Armazena **histórico** completo de features (por entidade e **timestamp**), em
  [lake/warehouse](../../14-data-lake/README.md)/[lakehouse](../../15-lakehouse/README.md) — Parquet/Iceberg/
  Delta/BigQuery/Snowflake.
- Usada para **treino**, **backfill** e **análise**; consultas **grandes** (muitas entidades × tempo),
  latência não crítica.
- Suporta **point-in-time (as-of) joins** para montar datasets sem vazamento
  ([point-in-time](../01-ml-data-pipelines/README.md)).

### Online store

- Armazena o **valor mais recente** de cada feature **por entidade**, num **key-value de baixa latência**
  (Redis, DynamoDB, Cassandra/ScyllaDB, Bigtable, Postgres): lookups em **milissegundos** por chave
  ([key-value](../../06-databases/04-nosql/01-key-value/README.md)).
- Usada no **serving**: dado `cliente_id`, retorna o vetor de features em tempo de requisição.
- **Materialização/sincronização** offline→online (batch agendado) e/ou **streaming** (features em tempo
  real direto no online).

| | Offline | Online |
| --- | --- | --- |
| Conteúdo | histórico (série temporal) | **valor atual** por entidade |
| Armazenamento | lake/warehouse (colunar) | key-value/cache (linha/chave) |
| Consulta | grandes varreduras, as-of joins | **lookup por chave**, ms |
| Uso | treino, backfill, batch inference | **inferência online** |
| Escala | TBs–PBs | milhões de entidades × poucas features recentes |

## O problema central: training-serving skew

```text
Treino:  features calculadas em SQL/Spark sobre o histórico
Serving: features reimplementadas no app (outra lógica, outra janela, outro bug) → distribuição diferente
Resultado: modelo bom offline, ruim em produção
```

A feature store impõe **uma definição única** executada para ambos os lados, e valida/monitora a
consistência (comparar distribuições treino vs serving — [drift](../06-ml-observability-drift/README.md)).

## Capacidades

1. **Registry/catálogo de features**: nome, entidade, tipo, descrição, **dono**, versão, fonte, SLA, tags/PII
   — **descoberta e reuso** ([catálogo](../../27-data-catalog-metadata/README.md)).
2. **Definição de features (código/DSL)** + **transformações** (batch, streaming, on-demand).
3. **Point-in-time correct joins** para construir datasets de treino (`get_historical_features`).
4. **Materialização** offline→online e/ou ingestão streaming.
5. **Serving online** (`get_online_features`) com baixa latência, TTL e consistência definida.
6. **Monitoramento**: frescor, volume, qualidade, drift de features.
7. **Governança**: controle de acesso, lineage, versionamento, auditoria.

## Exemplo (Feast, conceitual)

```python
from feast import FeatureStore
store = FeatureStore(repo_path=".")

# TREINO (offline): features vigentes em cada ts do entity_df, sem vazar o futuro
train_df = store.get_historical_features(
    entity_df=entidades_com_timestamp,                 # colunas: cliente_id, event_timestamp, label
    features=["compras_30d:total_30d", "compras_30d:n_compras_30d"],
).to_df()

# MATERIALIZAÇÃO: offline → online
store.materialize_incremental(end_date=datetime.utcnow())

# SERVING (online): lookup de baixa latência
vec = store.get_online_features(
    features=["compras_30d:total_30d", "compras_30d:n_compras_30d"],
    entity_rows=[{"cliente_id": "C-7"}],
).to_dict()
```

(Nomes/APIs variam por versão — consulte a documentação do Feast/ferramenta.)

## Ferramentas (panorama, não endosso)

| Tipo | Exemplos |
| --- | --- |
| **Open source** | **Feast**, Hopsworks (open core), Featureform |
| **Gerenciadas/plataformas** | **Tecton**, Databricks Feature Store (Unity Catalog), **Vertex AI Feature Store**, **SageMaker Feature Store**, Snowflake Feature Store, Azure ML/Fabric |
| **DIY** | tabelas de features no warehouse/lakehouse + Redis/DynamoDB + pipelines próprios |

Critérios: stack (cloud/warehouse), necessidade de **online/streaming**, point-in-time, governança,
operação (gerenciado vs self-hosted), custo/lock-in. **DIY** é viável para casos simples e dá controle, ao
custo de reconstruir point-in-time/registry/monitoramento.

## Padrões de computação de features (relembrando)

- **Batch** (agendado → offline → materializa p/ online): maioria das features.
- **Streaming** (Flink/Spark SS → online + offline): frescor de segundos
  ([stateful](../../17-streaming/05-stateful-processing/README.md)).
- **On-demand** (calculadas na requisição): dependem do contexto; mesma função no treino.

## Consistência e frescor no online store

- **TTL**: expirar valores velhos (feature "recente" vs "stale").
- **Atualização incremental** e idempotência da materialização ([idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Atraso offline→online** (staleness): defina SLO de frescor por feature
  ([SLO](../../24-observability/05-sli-slo-sla/README.md), [freshness](../../24-observability/06-data-freshness/README.md)).
- **Valores ausentes** (entidade nova/sem histórico): defaults/imputação consistentes com o treino.
- Atenção a **hot keys**, **limites de throughput** do KV e **custos** (RAM/IO).

## Trade-offs e limites

- **Complexidade operacional** (registry, dois stores, materialização, streaming) — só vale com escala/
  reuso/online.
- **Acoplamento à ferramenta** (lock-in de DSL/APIs).
- **Latência/custo do online** (Redis em RAM) vs frescor.
- Feature store resolve **dados de features**, não substitui validação, versionamento de modelos nem
  [MLOps](../07-mlops-integration/README.md).
- Cuidado com **proliferação de features** pouco usadas (custo/ruído) — governança de ciclo de vida.

## Quando usar / quando NÃO usar

- **Use** com **vários modelos/times**, **serving online** de baixa latência, **skew** recorrente, necessidade de
  **reuso/governança** de features.
- **Evite/adie** com um modelo batch simples, time pequeno, sem online — comece com **tabelas de features
  versionadas** (dbt/Spark) e adote a store quando a dor aparecer.

## Erros comuns

- Adotar feature store prematuramente (overhead sem ganho).
- Duas lógicas diferentes de cálculo (offline vs online) — a razão de ser da store, violada.
- Ignorar TTL/frescor no online; servir features velhas sem perceber.
- Vazamento por não usar point-in-time joins ao montar o treino.
- Features sem dono/versão; mudar definição "no lugar".
- Online store sem monitoramento (lag de materialização, latência, erros).

## Boas práticas

- Uma definição de feature, executada para treino e serving; versionar e registrar donos.
- SLOs de frescor/latência por feature; monitorar materialização, skew e drift.
- Começar simples; escolher a ferramenta pelo stack e requisitos reais.
- Governança: PII/classificação, acesso, lineage ([governança](../../25-data-governance/README.md)).

## Relação com outros conceitos

- [Feature engineering](../02-feature-engineering-pipelines/README.md), [ML data pipelines](../01-ml-data-pipelines/README.md),
  [serving](../05-model-serving/README.md), [drift](../06-ml-observability-drift/README.md),
  [key-value stores](../../06-databases/04-nosql/01-key-value/README.md), [lakehouse](../../15-lakehouse/README.md).

## Exercícios

1. Explique offline vs online store e o que cada um responde, com um exemplo de fraude.
2. Descreva como a feature store evita training-serving skew e vazamento.
3. Desenhe o fluxo de materialização offline→online e os SLOs de frescor.
4. Decida se um time com 1 modelo batch diário deveria adotar uma feature store e justifique.

## Referências

- Documentação de Feast, Tecton, Hopsworks; Uber "Michelangelo Palette"; Huyen, C. *Designing ML Systems*;
  feast.dev/blog (feature store concepts); featurestore.org.
