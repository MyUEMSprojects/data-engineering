# 31 — Data Engineering + Machine Learning

> 🟣 Nível 9 — ML Integration · Pré: [09 — ETL/ELT](../09-etl-elt/README.md),
> [12 — Data Quality](../12-data-quality/README.md), [15 — Lakehouse](../15-lakehouse/README.md),
> [23 — CI/CD & DataOps](../23-cicd-dataops/README.md)

A interseção entre **Engenharia de Dados** e **Machine Learning**: levar dados confiáveis até modelos e
modelos confiáveis até produção. Para quem estuda ML, este módulo mostra **onde os dados encontram os
modelos** — e por que a maior parte do esforço de ML em produção é **engenharia de dados e de sistemas**,
não "treinar o modelo".

> "ML em produção" é, em boa parte, um problema de **dados**: construir datasets corretos, features
> consistentes entre treino e serviço, e monitorar mudanças nos dados.

## A cadeia: Data Engineering → ML Engineering → MLOps

```text
Data Engineering ─► ML Data Pipeline ─► Feature Engineering ─► Training Pipeline ─► Serving ─► MLOps (monitorar/retreinar)
 (dados confiáveis)   (datasets p/ ML)     (features)           (treino reprodutível) (inferência) (ciclo de vida contínuo)
```

| Disciplina | Foco | Entregas típicas |
| --- | --- | --- |
| **Data Engineering** | dados confiáveis, acessíveis, em escala | pipelines, lake/warehouse, qualidade, lineage, **datasets/features base** |
| **ML Engineering** | levar modelos a produção de forma robusta | pipelines de treino, **serving**, integração com apps, avaliação |
| **MLOps** | **operacionalizar o ciclo de vida** de ML (DevOps + dados + modelos) | CI/CD de modelos, registry, monitoramento, retraining automatizado |
| **Data Science** | modelagem e experimentação | modelos, experimentos, análises |

(Detalhes das fronteiras: [DE vs outros papéis](../01-foundations/02-data-engineer-vs-other-roles/README.md).)

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [ML data pipelines e datasets de treino](01-ml-data-pipelines/README.md) | De dados brutos a datasets corretos (sem vazamento) |
| 02 | [Feature engineering pipelines](02-feature-engineering-pipelines/README.md) | Construir features reprodutíveis |
| 03 | [Feature stores (online/offline)](03-feature-stores-online-offline/README.md) | Consistência treino↔serving |
| 04 | [Training pipelines e validação de dados](04-training-pipelines/README.md) | Treino reprodutível e dados validados |
| 05 | [Model serving](05-model-serving/README.md) | Batch, online e streaming |
| 06 | [ML observability e drift](06-ml-observability-drift/README.md) | Data/feature/concept drift, monitoramento |
| 07 | [Integração com MLOps](07-mlops-integration/README.md) | CI/CD/CT, registry, ciclo completo |

## Dependências internas

```text
Data Engineering ─► ML data pipelines ─► Feature engineering ─► Feature stores
                                                │                    │
                       Training pipelines ◄─────┘                    ▼
                              │                                Model serving
                              ▼                                     │
                         MLOps integration ◄── ML observability/drift ◄┘
```

## Checkpoint

- [ ] Explicar a cadeia DE → ML Engineering → MLOps e as fronteiras de cada papel.
- [ ] Construir datasets de treino evitando **vazamento de dados** (point-in-time correctness).
- [ ] Projetar pipelines de features reprodutíveis (batch e streaming).
- [ ] Explicar **feature store**, offline vs online e **training-serving skew**.
- [ ] Desenhar um pipeline de treino reprodutível, com validação de dados e versionamento.
- [ ] Comparar serving batch, online e streaming; escolher conforme o caso.
- [ ] Detectar e responder a **data drift / concept drift**; descrever o ciclo de MLOps.

## Referências do módulo

- Huyen, C. *Designing Machine Learning Systems*. O'Reilly, 2022.
- Sculley et al. "Hidden Technical Debt in Machine Learning Systems" (NeurIPS 2015).
- Google "MLOps: Continuous delivery and automation pipelines in ML"; Breck et al. "The ML Test Score".
- Documentação de Feast, MLflow, TFX, Kubeflow, Evidently.
