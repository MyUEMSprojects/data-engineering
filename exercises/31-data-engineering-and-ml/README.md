# Exercícios — Módulo 31: Engenharia de dados e Machine Learning

Teoria em [31-data-engineering-and-ml](../../31-data-engineering-and-ml/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Training-serving skew

O que é *training-serving skew* e por que um *feature store* ajuda?

<details><summary>Gabarito</summary>

É a **diferença** entre como a feature é calculada no treino e na inferência (código/dados distintos) — o modelo vê distribuições diferentes em produção. O *feature store* centraliza a **definição única** da feature, servindo-a offline (treino) e online (inferência) de forma consistente. Ver [feature stores](../../31-data-engineering-and-ml/03-feature-stores-online-offline/README.md).
</details>

## 2. 🟢 Conceitual — Vazamento de dados

Dê um exemplo de **data leakage** em previsão de churn e como evitá-lo.

<details><summary>Gabarito</summary>

Usar como feature "cancelou_ticket_de_cancelamento" (consequência do churn) ou estatísticas calculadas com dados **do futuro** em relação ao alvo. Evite com **pontos no tempo corretos** (*point-in-time joins*), separar treino/validação por tempo e revisar a causalidade das features. Ver [pipelines de ML](../../31-data-engineering-and-ml/01-ml-data-pipelines/README.md).
</details>

## 3. 🔵 SQL — Join point-in-time

Para cada evento de rótulo `(user_id, label_ts)`, traga a **última** feature conhecida **até** `label_ts` (sem olhar o futuro).

<details><summary>Gabarito</summary>

```sql
SELECT l.user_id, l.label_ts, f.value
FROM labels l
LEFT JOIN LATERAL (
  SELECT value FROM features f
  WHERE f.user_id = l.user_id AND f.feature_ts <= l.label_ts
  ORDER BY f.feature_ts DESC LIMIT 1
) f ON true;
-- DuckDB/Snowflake: ASOF JOIN features f ON l.user_id = f.user_id AND l.label_ts >= f.feature_ts
```
É a operação central de *feature stores* para montar conjuntos de treino sem vazamento.
</details>

## 4. 🔵 Implementação — Monitorar drift

Implemente o **PSI** (*Population Stability Index*) entre a distribuição de treino e a de produção para uma feature numérica, com 10 *bins* de treino.

<details><summary>Gabarito</summary>

```python
import numpy as np

def psi(train, prod, bins=10, eps=1e-6):
    edges = np.quantile(train, np.linspace(0, 1, bins + 1)); edges[0], edges[-1] = -np.inf, np.inf
    p = np.histogram(train, edges)[0] / len(train) + eps
    q = np.histogram(prod, edges)[0] / len(prod) + eps
    return float(np.sum((q - p) * np.log(q / p)))
```
Regra de bolso: PSI < 0,1 estável; 0,1–0,25 atenção; > 0,25 *drift* relevante. Ver [observabilidade de ML](../../31-data-engineering-and-ml/06-ml-observability-drift/README.md).
</details>

## 5. 🟣 Arquitetura — Servir um modelo

Compare servir **em batch**, **online (API)** e **streaming**. Escolha para: recomendações semanais; score de fraude em 50 ms; alertas de anomalia contínuos.

<details><summary>Gabarito</summary>

Semanal → **batch** (barato, pré-computado). Fraude 50 ms → **online** com features pré-computadas no *online store* e modelo leve. Anomalias contínuas → **streaming** (inferência no fluxo). Considere latência, custo, frescor das features e fallback. Ver [serviço de modelos](../../31-data-engineering-and-ml/05-model-serving/README.md).
</details>

## 6. 🟣 Arquitetura — Pipeline de retreino

Projete o retreino automático: gatilhos, validações antes de promover o modelo e *rollback*.

<details><summary>Gabarito</summary>

Gatilhos: agenda, **drift**, queda de métrica de negócio. Pipeline: dados validados (gate de qualidade) → treino reprodutível (versão de dados/código) → **avaliação contra o modelo atual** (métricas + fatias + testes de regressão) → registro no *model registry* → promoção gradual (*shadow/canary*). Rollback: manter a versão anterior servível e reverter por configuração. Ver [treinamento](../../31-data-engineering-and-ml/04-training-pipelines/README.md) e [MLOps](../../31-data-engineering-and-ml/07-mlops-integration/README.md).
</details>
