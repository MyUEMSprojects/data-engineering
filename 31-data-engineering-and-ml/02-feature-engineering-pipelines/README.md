# Feature engineering pipelines

> 🟣 ML Integration · Parte de [31 — DE + ML](../README.md)

## O que é

**Feature engineering** é transformar dados brutos em **variáveis (features)** informativas para um modelo.
Um **feature pipeline** é o processo **automatizado, versionado e reprodutível** que calcula essas features
a partir dos dados da plataforma — o equivalente, no mundo ML, das transformações
[ETL/ELT](../../09-etl-elt/03-transformation/README.md) (e frequentemente construído com as mesmas
ferramentas: SQL/[dbt](../../28-dbt/README.md), [Spark](../../16-distributed-processing/README.md),
[Flink](../../17-streaming/07-flink/README.md)).

## Por que é um problema de engenharia (não só de DS)

Em notebooks, features viram código ad hoc; em produção, isso gera **inconsistência, duplicação e dívida
técnica**. Os desafios clássicos:

- **Training-serving skew**: a feature é calculada de **um jeito no treino** (SQL/pandas) e **de outro no
  serviço** (código reimplementado) → o modelo recebe entradas diferentes das que treinou
  ([feature stores](../03-feature-stores-online-offline/README.md)).
- **Reuso**: cada projeto recalcula "total de compras 30d" de formas ligeiramente diferentes.
- **Correção temporal** ([point-in-time](../01-ml-data-pipelines/README.md)).
- **Frescor** (features em tempo real vs batch) e **custo de cálculo**.

## Tipos de features (por origem/janela)

| Tipo | Exemplo | Computação |
| --- | --- | --- |
| **Atributos estáticos/derivados** | idade da conta, UF, segmento | batch (tabela/dimensão) |
| **Agregações em janela** | nº de compras últimos 7/30 dias, soma gasta, média móvel | batch ou streaming (janelas — [tempo e janelas](../../17-streaming/03-time-and-windows/README.md)) |
| **Contagens/frequências/recência** | dias desde última compra, nº de logins | batch/streaming |
| **Razões e interações** | compras/visitas, valor/ticket médio | em cima de outras features |
| **Embeddings** | vetor de usuário/produto/texto | modelo pré-treinado/treinado ([vector DBs](../../30-advanced/06-vector-databases/README.md)) |
| **Features de contexto da requisição** | hora, dispositivo, valor da transação | calculadas **on-demand** no momento da inferência |
| **Features de grafo/sequência** | centralidade, últimos N eventos | jobs especializados |

## Transformações comuns

- **Numéricas**: normalização/padronização, log, binning, tratamento de outliers, imputação.
- **Categóricas**: one-hot, **target/frequency encoding**, hashing (alta cardinalidade), embeddings.
- **Temporais**: componentes (hora/dia/semana), sazonalidade, **lags/rolling windows**, tempo desde evento.
- **Texto**: tokenização, TF-IDF, embeddings; **imagem**: resize/normalização/augmentations.
- **Agregações por entidade e por janela** (o maior volume de trabalho em DE).

> **Cuidados**: estatísticas para normalização/encoding (média, desvio, mapeamentos) **ajustadas só no
> treino** e **persistidas/versionadas** para reaplicar idênticas no serviço (evita skew e vazamento).

## Arquitetura de pipelines de features

### Batch
```text
Warehouse/lake (silver) ─► job agendado (SQL/dbt/Spark) ─► tabela de features (versionada, particionada por data)
```
Simples, barato, ideal para features que mudam devagar. Atualizadas por [orquestração](../../11-orchestration/README.md)
(diária/horária), **idempotentes** e **parametrizadas por data**
([idempotência](../../09-etl-elt/07-idempotency-retries/README.md), [backfill](../../09-etl-elt/08-backfill/README.md)).

### Streaming
```text
Eventos (Kafka) ─► Flink/Spark SS/Kafka Streams (janelas/estado) ─► feature store online (+ lake p/ offline)
```
Para **frescor de segundos** (fraude, recomendação em sessão): agregações em janela mantidas em tempo real
([stateful](../../17-streaming/05-stateful-processing/README.md)).

### On-demand (request-time)
Features que dependem do **contexto da requisição** (valor da transação atual, geolocalização) são
calculadas **na hora da inferência** — com a **mesma função** usada no treino (código compartilhado).

### A "regra de ouro": **uma definição, duas execuções**

```text
        ┌─ definição ÚNICA da feature (código/SQL/DSL) ─┐
        ▼                                               ▼
  execução BATCH (treino, backfill)           execução ONLINE (serving, baixa latência)
```
Evita skew: **o mesmo código/lógica** (ou uma DSL/feature store que gera ambos) alimenta treino e serviço.

## Implementação com ferramentas que você já conhece

- **dbt/SQL** para features batch no warehouse (testadas, documentadas, com lineage)
  ([dbt](../../28-dbt/README.md)).
- **Spark/polars** para volumes grandes/lógica complexa.
- **Flink/Spark SS** para features em streaming.
- **Feature stores** (Feast, Tecton, Databricks/Vertex/SageMaker Feature Store) para registro, point-in-time
  join, materialização offline→online e servir ([03](../03-feature-stores-online-offline/README.md)).

```python
# Exemplo conceitual (Feast): definição única de uma feature view
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64
cliente = Entity(name="cliente", join_keys=["cliente_id"])
compras_30d = FeatureView(
    name="compras_30d", entities=[cliente], ttl=timedelta(days=2),
    schema=[Field(name="total_30d", dtype=Float32), Field(name="n_compras_30d", dtype=Int64)],
    source=FileSource(path="s3://lake/gold/compras_30d/", timestamp_field="event_ts"),
)
```
(APIs mudam entre versões — consulte a documentação do Feast/ferramenta usada.)

## Qualidade, testes e observabilidade das features

- **Testes**: unitários da lógica (casos de borda), **idempotência**, ausência de vazamento, schema/tipos
  ([pipeline testing](../../10-data-pipelines/07-pipeline-testing/README.md)).
- **Validação de dados**: distribuição, nulos, faixas, cardinalidade; comparar **treino vs serving** (skew)
  ([data quality](../../12-data-quality/README.md)).
- **Monitoramento**: frescor, volume, **drift de features** ([drift](../06-ml-observability-drift/README.md)),
  latência de cálculo/serving.
- **Documentação/catálogo**: definição de negócio, dono, SLA, PII, quem usa
  ([catálogo](../../27-data-catalog-metadata/README.md), [contratos](../../29-data-contracts/README.md)).
- **Versionamento de features**: mudar a lógica = **nova versão** (modelos treinados na antiga seguem
  consistentes); registrar qual versão cada modelo usa.

## Governança e privacidade

Features podem derivar de **PII** ou proxies de atributos sensíveis (viés/discriminação). Classifique,
minimize, controle acesso e documente finalidade ([LGPD](../../26-security/08-lgpd/README.md),
[classificação](../../25-data-governance/05-access-control-classification/README.md)).

## Custo e desempenho

- Pré-calcular em **batch** o que não precisa de frescor extremo; streaming só onde o valor justifica
  ([batch vs streaming](../../01-foundations/06-batch-vs-streaming/README.md)).
- **Reuso** entre modelos (uma feature, vários consumidores) reduz custo.
- Janelas grandes/agregações por entidade em escala → particionar por entidade/tempo, evitar skew
  ([skew](../../16-distributed-processing/04-distributed-joins-skew/README.md)).

## Erros comuns

- Reimplementar a feature no serviço (skew) em vez de compartilhar definição.
- Vazamento temporal por agregações que incluem o futuro.
- Estatísticas de normalização/encoding calculadas no dataset inteiro e não persistidas.
- Features sem dono/versão/documentação; duplicação entre times.
- Streaming desnecessário (custo/complexidade) para features que mudam lentamente.
- Mudar a lógica de uma feature "no lugar" (quebra modelos em produção).

## Boas práticas

- **Uma definição, duas execuções**; versionar features; point-in-time correctness.
- Persistir artefatos de transformação (scalers/encoders/vocabulários) junto do modelo.
- Testar, validar e monitorar features como dados de produção; catalogar com dono/SLA.
- Batch por padrão; streaming/on-demand onde necessário; idempotência e backfill seguros.

## Relação com outros conceitos

- [ML data pipelines](../01-ml-data-pipelines/README.md), [feature stores](../03-feature-stores-online-offline/README.md),
  [ETL/transformação](../../09-etl-elt/03-transformation/README.md), [dbt](../../28-dbt/README.md),
  [streaming](../../17-streaming/README.md), [SQL analítico](../../05-sql/13-analytical-sql/README.md).

## Exercícios

1. Defina 6 features de churn (estáticas, janela, recência, razão) e a computação de cada (batch/stream).
2. Explique training-serving skew com um exemplo e como "uma definição, duas execuções" o evita.
3. Escreva o SQL de `compras_30d` correto point-in-time (sem usar eventos futuros).
4. Planeje o versionamento de uma feature cuja lógica vai mudar sem quebrar modelos existentes.

## Referências

- Zheng & Casari, *Feature Engineering for Machine Learning*; Huyen, C. *Designing ML Systems* (features);
  documentação de Feast/Tecton; Uber Michelangelo "Palette" (artigo sobre feature store).
