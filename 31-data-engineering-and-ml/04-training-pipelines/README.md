# Training pipelines e validação de dados

> 🟣 ML Integration · Parte de [31 — DE + ML](../README.md)

## O que é

Um **training pipeline** é o fluxo **automatizado e reprodutível** que, a partir de dados versionados,
**treina, avalia e registra** um modelo — substituindo o "notebook que alguém rodou". É a ponte entre
[ML data pipelines/features](../02-feature-engineering-pipelines/README.md) e [serving](../05-model-serving/README.md),
e peça central do [MLOps](../07-mlops-integration/README.md).

```text
Dataset versionado ─► validação de dados ─► (pré-processamento) ─► treino ─► avaliação ─► validação do modelo ─► registro (model registry)
        ▲                                                                                       │
        └────────────── gatilhos: agenda · novo dado · drift · degradação ◄──────────────────────┘ (retraining)
```

## Por que pipeline (e não notebook)

| Notebook ad hoc | Pipeline de treino |
| --- | --- |
| Manual, não repetível | **Automatizado**, parametrizado, agendável/acionável |
| "Funciona na minha máquina" | **Ambiente reprodutível** (container, lockfile) |
| Dataset/código/params não rastreados | **Versionamento** de dados, código, params, modelo |
| Sem testes/validação | **Validação de dados e de modelo** como gates |
| Difícil de re-treinar | **Retraining** contínuo e seguro |

## Etapas e responsabilidades

1. **Ingestão do dataset** (versão/snapshot específica — [reprodutibilidade](../01-ml-data-pipelines/README.md)).
2. **Validação de dados** (abaixo) — gate: bloqueia treino com dados ruins.
3. **Pré-processamento/feature transforms** — ajustados no treino, **artefatos persistidos**
   (scaler/encoders/vocabulário) para o serving.
4. **Treino** — algoritmo, hiperparâmetros (busca: grid/random/Bayesiana/Optuna), distribuído se preciso.
5. **Avaliação** em conjunto de validação/teste (métricas de negócio e de modelo; fatias/segmentos).
6. **Validação do modelo** (gate): melhor que o **baseline/modelo atual**? atende limites de qualidade,
   latência, justiça/viés?
7. **Registro** no **model registry** com metadados (dataset, código, métricas, ambiente) e estágio
   (staging/production).
8. **Notificação/aprovação** e disparo do deploy ([MLOps](../07-mlops-integration/README.md)).

## Validação de dados (a parte "DE" do treino)

Dados de treino com problemas silenciosos produzem modelos ruins que passam despercebidos. Valide **antes**
de treinar, com testes sobre o dataset (e **contra o dataset anterior/de referência**):

| Categoria | Verificações |
| --- | --- |
| **Schema** | colunas/tipos esperados; sem colunas novas/ausentes ([schema validation](../../12-data-quality/03-schema-validation/README.md)) |
| **Qualidade** | nulos, duplicatas, faixas, domínios, integridade ([dimensões](../../12-data-quality/01-dimensions-of-quality/README.md)) |
| **Volume/frescor** | nº de linhas esperado; dados recentes presentes ([freshness](../../24-observability/06-data-freshness/README.md)) |
| **Distribuição** | média/percentis/cardinalidade dentro do esperado vs referência (**data drift** — [06](../06-ml-observability-drift/README.md)) |
| **Rótulos** | proporção de classes, vazamento do label, atraso de observação |
| **Vazamento** | features com informação futura; sobreposição treino/teste |
| **Viés/fairness** (quando aplicável) | métricas por grupo; proxies de atributos sensíveis |

Ferramentas: **Great Expectations / Pandera / Soda**, **TFX Data Validation (TFDV)** (estatísticas e
detecção de skew/drift contra schema), **Evidently**, **deepchecks**, testes dbt
([expectation testing](../../12-data-quality/04-expectation-testing/README.md)). Falha ⇒ **abortar e
alertar** (hard) ou quarentenar.

## Reprodutibilidade (o que registrar por execução)

```text
código (commit SHA) · dataset (snapshot/hash/versão) · features (versões) · hiperparâmetros · sementes · ambiente (imagem/lockfile) · métricas · artefatos (modelo + transformadores)
```

- **Experiment tracking**: **MLflow**, Weights & Biases, Neptune, Comet — runs, params, métricas, artefatos.
- **Dados**: DVC/lakeFS/snapshots Iceberg-Delta; **lineage** modelo→dataset→fontes
  ([lineage](../../10-data-pipelines/06-data-lineage/README.md)).
- **Ambiente**: containers ([Docker](../../20-containers/README.md)), lockfiles
  ([ambientes Python](../../04-python-for-data-engineering/02-environments-and-packaging/README.md)).
- **Determinismo**: sementes, ordenação estável, versões fixas de libs.

## Orquestração de treino

- **Orquestradores de dados** ([Airflow](../../11-orchestration/02-airflow/README.md)/[Dagster](../../11-orchestration/03-dagster/README.md)/
  Prefect) coordenando passos (dataset → treino → avaliação), disparando jobs em K8s/Spark/GPU.
- **Plataformas ML-nativas**: **Kubeflow Pipelines**, **TFX**, **Vertex AI Pipelines**, **SageMaker Pipelines**,
  **Azure ML Pipelines**, **Metaflow**, **ZenML**, **Flyte** — passos containerizados, cache de artefatos,
  linhagem ML.
- Cada passo **idempotente** e parametrizado ([idempotência](../../09-etl-elt/07-idempotency-retries/README.md));
  cache de resultados intermediários para economizar.

## Computação de treino

- **CPU/GPU/TPU**, **spot/preemptible** com **checkpoints** do modelo para retomar
  ([checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md), [spot](../../19-cloud/03-compute/README.md)).
- **Treino distribuído** (Spark MLlib, Horovod, PyTorch DDP, Ray Train) para dados/modelos grandes.
- **Dados para treino**: leitura eficiente (Parquet/TFRecord/WebDataset, *sharding*, prefetch) — evitar que
  I/O seja o gargalo.
- **Custo**: tags, orçamento, parada de recursos ociosos ([cost](../../19-cloud/08-cost-management/README.md)).

## Avaliação e validação do modelo

- **Métricas** adequadas ao problema (AUC/PR-AUC, F1, RMSE, NDCG...) e **métricas de negócio**.
- **Avaliação por fatias** (segmentos, regiões, coortes) — média esconde falhas locais.
- **Comparação com baseline** e com o **modelo em produção** (champion/challenger).
- **Testes de comportamento** (invariância, limites), robustez, **fairness**, explicabilidade.
- **Gates automáticos**: só registra/promove se atender limiares ([CI para ML](../07-mlops-integration/README.md)).

## Gatilhos de (re)treino

- **Agendado** (diário/semanal) — simples.
- **Por novo dado** (volume/tempo).
- **Por drift/degradação** detectados em produção ([observabilidade](../06-ml-observability-drift/README.md)).
- **Por mudança de código/features** (CI).

Equilibre custo e frescor; retreino contínuo exige **validação robusta** para não promover modelos piores.

## Erros comuns

- Treinar sem validar os dados (modelo com lixo/vazamento).
- Dataset/código/params não versionados — impossível reproduzir/auditar.
- Transformadores (scaler/encoder) não persistidos → skew no serving.
- Promover modelo sem comparar com baseline/produção; avaliar só a média.
- Pipeline não idempotente/sem cache; recomeçar do zero em falha.
- Treino em dados de produção com PII sem governança.
- Retreino automático sem gates (degrada silenciosamente).

## Boas práticas

- Pipeline versionado e containerizado; passos idempotentes; dataset por snapshot.
- Validação de dados e de modelo como **gates**; métricas por fatia; comparação com champion.
- Rastrear tudo (tracking + registry + lineage); persistir transformadores com o modelo.
- Spot + checkpoints para custo; observabilidade do pipeline de treino.
- Tratar o pipeline de treino como código de produção (testes, CI, revisão).

## Relação com outros conceitos

- [ML data pipelines](../01-ml-data-pipelines/README.md), [feature stores](../03-feature-stores-online-offline/README.md),
  [serving](../05-model-serving/README.md), [MLOps](../07-mlops-integration/README.md),
  [data quality](../../12-data-quality/README.md), [orquestração](../../11-orchestration/README.md).

## Exercícios

1. Desenhe um training pipeline (passos, gates, artefatos) para um modelo de churn semanal.
2. Liste 8 validações de dados que bloqueariam o treino e a ferramenta para cada.
3. Defina o que registrar para que o "modelo v12" seja 100% reproduzível.
4. Explique champion/challenger e como o gate de validação evita promover um modelo pior.

## Referências

- Google, "MLOps: Continuous delivery and automation pipelines in ML"; Breck et al., "The ML Test Score" (2017);
  docs de MLflow, TFX/TFDV, Kubeflow, Great Expectations, Evidently; Huyen, C. *Designing ML Systems*.
