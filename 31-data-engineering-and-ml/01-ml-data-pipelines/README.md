# ML data pipelines e datasets de treino

> 🟣 ML Integration · Parte de [31 — DE + ML](../README.md)

## O que é

Um **ML data pipeline** transforma dados brutos da plataforma ([lake/warehouse](../../14-data-lake/README.md))
em **datasets de treino/validação/teste** (e dados de inferência) **corretos, versionados e reprodutíveis**.
É onde a engenharia de dados determina o **teto de qualidade** de um modelo: "garbage in, garbage out".

## Por que difere de um pipeline analítico comum

Pipelines analíticos respondem perguntas **sobre o passado**; pipelines de ML precisam simular, para cada
exemplo, **o que se sabia no momento da predição** — e reproduzir isso **igual** no treino e no serviço. Isso
introduz preocupações novas:

| Preocupação | Por quê |
| --- | --- |
| **Point-in-time correctness** | evitar usar informação do futuro (vazamento) |
| **Rótulos (labels)** | derivar o alvo corretamente, com atraso de observação |
| **Reprodutibilidade** | mesmo código + mesmos dados ⇒ mesmo dataset (auditoria, debug, comparar modelos) |
| **Consistência treino↔serving** | features calculadas **do mesmo jeito** ([feature stores](../03-feature-stores-online-offline/README.md)) |
| **Volume/amostragem** | balanceamento, particionamento por tempo/entidade |

## Etapas típicas

```text
Fontes (OLTP/eventos/CDC) ─► lake (bronze/silver) ─► seleção de entidades + labels ─► JOIN de features point-in-time
   ─► split (treino/val/teste) ─► validação ─► dataset versionado ─► treino
```

1. **Definir o problema e a unidade de predição** (ex.: "prever churn de **cliente** em **t**, horizonte 30d").
2. **Construir a tabela de entidades/labels**: cada linha = (entidade, **timestamp de referência**, label).
3. **Anexar features como estavam em `t`** (point-in-time join — abaixo).
4. **Dividir** em treino/validação/teste (por **tempo**, não aleatório, quando há dependência temporal).
5. **Validar** distribuição, nulos, vazamento, balanceamento ([validação de dados](../04-training-pipelines/README.md)).
6. **Versionar** o dataset e registrar sua **lineage** ([versionamento](#versionamento-e-reprodutibilidade)).

## O pecado capital: vazamento de dados (data leakage)

**Vazamento** = o modelo vê, no treino, informação que **não estaria disponível** na hora real da
predição → métricas offline **infladas** e desempenho **ruim** em produção. Tipos:

- **Vazamento temporal (target leakage)**: usar features calculadas com dados **posteriores** ao instante
  de predição (ex.: "total de compras do mês" quando se prediz no dia 5).
- **Vazamento de rótulo**: feature que **codifica o alvo** (ex.: `status_cancelamento` para prever churn).
- **Vazamento de split**: o mesmo cliente/documento em treino **e** teste; **normalização/imputação**
  ajustada com todo o dataset antes do split (*train-test contamination*).
- **Duplicatas** entre splits; agrupamentos (mesma sessão/usuário) separados incorretamente.

### Point-in-time (as-of) joins

Para cada `(entidade, t)`, a feature deve ter o valor **vigente em `t` (≤ t)**, nunca posterior. Em SQL:

```sql
-- para cada exemplo, pega a última versão da feature ANTES do timestamp de referência
SELECT e.entity_id, e.ts AS event_ts, e.label,
       f.total_compras_30d, f.dias_desde_ultima_compra
FROM entidades e
LEFT JOIN LATERAL (
  SELECT * FROM features f
  WHERE f.entity_id = e.entity_id AND f.feature_ts <= e.ts      -- sem futuro
  ORDER BY f.feature_ts DESC LIMIT 1
) f ON true;
```
(Equivalente com `ASOF JOIN` em engines que o suportam, ou *window functions* — ver
[SQL analítico](../../05-sql/13-analytical-sql/README.md).) **Feature stores** automatizam isso
([feature stores](../03-feature-stores-online-offline/README.md)). Dimensões **SCD2**
([SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md)) e **tabelas históricas/snapshots**
são essenciais para reconstruir "o que era verdade em t".

## Labels

- **Atraso de observação**: o rótulo só é conhecido **depois** (churn em 30d ⇒ esperar 30d). O dataset deve
  conter só exemplos com **janela de observação completa**.
- **Definição precisa e estável** do alvo (documentada, versionada — [contratos](../../29-data-contracts/README.md)).
- **Rótulos ruidosos/ausentes**: trate viés de seleção (só vemos resultados de quem foi tratado/aprovado).
- **Rotulagem humana** (supervisão): ferramentas e qualidade (concordância entre anotadores).

## Splits corretos

| Cenário | Estratégia |
| --- | --- |
| Dados temporais (previsão, fraude, churn) | **split por tempo** (treino < validação < teste), simulando o futuro |
| Múltiplas linhas por entidade | **split por entidade/grupo** (sem a mesma entidade em dois conjuntos) |
| i.i.d. verdadeiro | split aleatório estratificado |
| Dados raros (fraude) | estratificação + cuidado com amostragem (reajustar métricas/probabilidades) |

**Ajuste de pré-processamento (scaler, imputação, encoders) apenas no treino** e aplique ao resto.

## Qualidade e volume

- **Qualidade**: aplique [testes de dados](../../12-data-quality/README.md) no dataset (nulos, faixas,
  duplicatas, distribuição vs referência).
- **Desbalanceamento**: reamostragem/pesos/métricas adequadas (PR-AUC, recall@k).
- **Amostragem**: estratificada/por entidade; documentar proporções.
- **Escala**: [Spark](../../16-distributed-processing/README.md)/[polars](../../04-python-for-data-engineering/12-polars/README.md)/
  SQL no warehouse; formatos colunares ([Parquet](../../08-data-formats/04-parquet/README.md)); partição por
  tempo.

## Versionamento e reprodutibilidade

Um modelo é reproduzível só se o **dataset exato** o for. Registre por treino: **versão do código**,
**versão/hash/snapshot do dataset**, **parâmetros** e **ambiente**.

- **Lakehouse time travel** (Delta/Iceberg): referenciar **snapshot/versão** da tabela
  ([lakehouse](../../15-lakehouse/README.md)).
- **Ferramentas**: **DVC**, **lakeFS** (branches/commits de dados), **MLflow** (artefatos/params), hash do
  dataset; **dataset cards/datasheets**.
- **Determinismo**: sementes, ordenação estável, evitar `now()` — parametrizar por **data de referência**
  ([idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Lineage**: de qual dado/feature/versão veio o modelo ([lineage](../../10-data-pipelines/06-data-lineage/README.md)).

## Dados não estruturados e outras modalidades

Texto/imagem/áudio: armazenar no [object storage](../../14-data-lake/02-object-storage/README.md), com
**manifestos/índices** (Parquet com URIs + metadados + labels), pré-processamento (tokenização, resize,
augmentations) reprodutível, e formatos de treino eficientes (TFRecord/WebDataset/Parquet). Embeddings →
[vector DBs](../../30-advanced/06-vector-databases/README.md).

## Privacidade e governança

Datasets de ML frequentemente contêm **PII**: minimize, pseudonimize, restrinja acesso, documente finalidade/
base legal; atenção a **viés/discriminação** (atributos sensíveis e proxies) e **explicabilidade**
([LGPD](../../26-security/08-lgpd/README.md), [mascaramento](../../26-security/07-data-masking-pii/README.md),
[compliance](../../25-data-governance/07-compliance-privacy/README.md)). Direito de exclusão pode exigir
**retreinar/remover** dados.

## Exemplo: pipeline de dataset (esboço PySpark/dbt)

```text
1. dbt/Spark: tabela `labels` (cliente, ref_date, churn_30d) só com janela completa
2. dbt/Spark/feature store: `features_asof` (point-in-time) → `training_set`
3. split por tempo: treino (jan–set), val (out), teste (nov)
4. validação: nulos, distribuição, ausência de vazamento (checagens)
5. grava Parquet versionado (snapshot Iceberg/Delta) + registra hash/lineage no MLflow
```

## Erros comuns

- **Vazamento temporal** (features com dados futuros) — métricas lindas, produção péssima.
- Split aleatório em dados temporais; mesma entidade em treino e teste.
- Ajustar scaler/imputer com todo o dataset antes do split.
- Labels com janela de observação incompleta.
- Dataset não versionado/irreproduzível ("qual dado treinou o modelo v7?").
- PII desnecessária; sem governança sobre dados de treino.
- Pipeline de treino diferente do de serving (skew).

## Boas práticas

- Defina unidade de predição, `t` de referência e janela de label **antes** de codar.
- **Point-in-time joins**; split por tempo/grupo; pré-processamento ajustado só no treino.
- Valide e versione o dataset (snapshot/hash) com lineage; reprodutibilidade por design.
- Use feature store para consistência; aplique governança/privacidade.
- Teste o pipeline (unidade/integração) como qualquer pipeline de dados
  ([pipeline testing](../../10-data-pipelines/07-pipeline-testing/README.md)).

## Relação com outros conceitos

- [Feature engineering](../02-feature-engineering-pipelines/README.md), [feature stores](../03-feature-stores-online-offline/README.md),
  [training pipelines](../04-training-pipelines/README.md), [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md),
  [lakehouse/time travel](../../15-lakehouse/README.md), [data quality](../../12-data-quality/README.md).

## Exercícios

1. Dê 3 exemplos de data leakage numa previsão de churn e como cada um seria evitado.
2. Escreva um point-in-time join (SQL) que anexa as features vigentes em `ref_date` a uma tabela de labels.
3. Defina o split correto para previsão de fraude com dados de 12 meses e justifique.
4. Descreva como garantir que o dataset do "modelo v7" possa ser reconstruído exatamente.

## Referências

- Huyen, C. *Designing ML Systems* (data leakage, splits); Kaufman et al., "Leakage in Data Mining" (2012);
  docs de Feast (point-in-time joins), DVC, lakeFS, MLflow.
