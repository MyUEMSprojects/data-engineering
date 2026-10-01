# Integração com MLOps

> 🟣 ML Integration · Parte de [31 — DE + ML](../README.md)

## O que é

**MLOps** é a prática de **operacionalizar o ciclo de vida de ML** — combinando **DevOps**
([CI/CD](../../23-cicd-dataops/README.md)), **DataOps** ([DataOps](../../23-cicd-dataops/05-dataops/README.md))
e **gestão de modelos** — para construir, implantar, monitorar e **retreinar** modelos de forma
**confiável, reprodutível e contínua**. É o último elo da cadeia **Data Engineering → ML Engineering → MLOps**.

> Insight clássico (Sculley et al., 2015): em sistemas de ML reais, o **código do modelo é uma pequena fração**;
> o resto é **dados, features, configuração, infraestrutura, serving e monitoramento** — onde mais há
> **dívida técnica**.

## O ciclo de vida completo

```text
  ┌──────────────────────────────────────────────────────────────────────────────┐
  ▼                                                                              │
Dados ─► Features ─► Treino ─► Avaliação ─► Registro ─► Deploy ─► Serving ─► Monitoramento ─┘
(DE)      (DE/MLE)   (MLE/DS)   (gates)     (registry)   (CD)     (MLE)     (drift/perf) → retreino
```

Cada seta é **automatizada, versionada e observada**.

## Os três "CI/CD" do ML (CI / CD / CT)

Diferente de software, ML tem **dados e modelos mutáveis**, então além de CI/CD há **CT**:

| | O que automatiza | Gatilho | Gates |
| --- | --- | --- | --- |
| **CI** (Continuous Integration) | testar **código, dados e modelo**: unidade, validação de dados/schema, testes de features, treino "fumaça" | commit/PR | testes passam; sem vazamento; lint |
| **CD** (Continuous Delivery/Deployment) | **entregar** o pipeline/serviço/modelo ao ambiente alvo | merge/aprovação | validação do modelo, testes de integração, canary |
| **CT** (**Continuous Training**) | **retreinar** automaticamente o modelo com novos dados | agenda · novo dado · **drift** · degradação | validação de dados + de modelo (champion/challenger) |

(Google: níveis de maturidade MLOps — 0: manual; 1: **pipeline de treino automatizado + CT**; 2: **CI/CD do
pipeline** completo.)

## Componentes de uma plataforma MLOps

| Componente | Função | Exemplos |
| --- | --- | --- |
| **Versionamento de código** | Git, PRs, reviews | [Git](../../03-git-software-engineering/README.md) |
| **Versionamento de dados** | datasets/snapshots/lineage | DVC, lakeFS, Iceberg/Delta time travel |
| **Feature store** | features consistentes treino/serving | [Feast, Tecton…](../03-feature-stores-online-offline/README.md) |
| **Experiment tracking** | runs, params, métricas, artefatos | MLflow, W&B, Neptune |
| **Orquestração de pipelines** | treino/CT reprodutível | Airflow/Dagster, **Kubeflow, TFX, Vertex/SageMaker Pipelines, Metaflow, Flyte, ZenML** |
| **Model registry** | versões, estágios, metadados, aprovação | **MLflow Registry**, Vertex/SageMaker/Azure registries |
| **Serving** | batch/online/streaming | [KServe, Seldon, BentoML, Triton](../05-model-serving/README.md) |
| **Monitoramento** | infra + dados + modelo | [Evidently, NannyML, Arize…](../06-ml-observability-drift/README.md) |
| **Infra reprodutível** | containers, IaC, GPU, K8s | [Docker](../../20-containers/README.md), [Kubernetes](../../21-kubernetes/README.md), [IaC](../../22-infrastructure-as-code/README.md) |
| **Governança** | catálogo, lineage, acesso, auditoria, model cards | [governança](../../25-data-governance/README.md) |

> Você **não** precisa de todos desde o início. Comece com **Git + pipeline reprodutível + tracking +
> registry + monitoramento básico**; adicione feature store/CT/plataforma conforme a dor e a escala.

## Model registry e promoção

O **registry** é a "fonte da verdade" dos modelos: cada versão com **metadados** (dataset/snapshot, código,
features/transformadores, métricas, ambiente, aprovações) e **estágio** (`None → Staging → Production →
Archived`).

```text
Treino ─► registra modelo v13 (Staging) ─► testes de integração/shadow/canary ─► aprovação ─► Production ─► v12 → Archived
                                                  └─ falhou? permanece/rollback para v12
```

Promoção com **gates automáticos + aprovação humana** quando o risco justificar
([estratégias de deploy](../../23-cicd-dataops/06-deployment-strategies/README.md)).

## CI/CD para ML (esboço de workflow)

```yaml
# PR: CI de ML
on: pull_request
jobs:
  ci:
    steps:
      - lint + testes unitários (transformações de features, lógica)
      - validação de dados/schema em amostra (Great Expectations/Pandera)
      - treino "fumaça" (dataset mínimo) + checagem de métricas mínimas e ausência de vazamento
      - build da imagem do pipeline/serviço (scan de segurança)
# main: CD
on: push main
jobs:
  cd:
    steps:
      - publica artefatos (imagem, pipeline) · atualiza definição do pipeline de treino
      - dispara treino no ambiente staging (ou CT agendado)
      - gate: modelo candidato vs champion ──► registra e promove (canary/shadow)
```

## Responsabilidades e fronteiras (quem faz o quê)

| Etapa | DE | ML Eng | DS | Plataforma/MLOps |
| --- | :-: | :-: | :-: | :-: |
| Pipelines de dados/qualidade/lineage | ● | ○ | | ○ |
| Feature pipelines/feature store | ● | ● | ○ | ○ |
| Experimentação/modelagem | | ○ | ● | |
| Pipeline de treino reprodutível | ○ | ● | ○ | ● |
| Serving e deploy | | ● | | ● |
| Monitoramento/drift/retreino | ○ | ● | ○ | ● |
| Infra/IaC/CI-CD/segurança | ○ | ○ | | ● |

(● principal · ○ colabora; varia por empresa.) O papel do **Data Engineer** é a **fundação de dados**
(qualidade, features, plataforma) que sustenta todo o ciclo; para evoluir a **ML Engineer/MLOps**, some
**serving, orquestração de treino, CI/CD de modelos e observabilidade de ML**.

## Governança, risco e responsabilidade em ML

- **Rastreabilidade ponta a ponta**: da predição → versão do modelo → dataset/features → fontes
  ([lineage](../../10-data-pipelines/06-data-lineage/README.md)). Essencial para **auditoria** e depuração.
- **Model cards / datasheets**: documentação de propósito, dados, métricas, limitações, vieses.
- **Privacidade**: PII em dados de treino/logs, finalidade, base legal, **decisões automatizadas** (LGPD art. 20),
  direito à exclusão (retreino/remoção) ([LGPD](../../26-security/08-lgpd/README.md)).
- **Justiça/viés** e **explicabilidade** monitorados; **segurança** (acesso ao modelo/dados, ataques).
- **Aprovação e responsabilidade**: dono do modelo, comitê/risco para casos de alto impacto.

## Padrões de maturidade (caminho prático)

```text
Nível 0: notebooks, deploy manual, sem monitoramento
Nível 1: pipeline de treino automatizado, tracking e registry, serving versionado, monitoramento básico
Nível 2: CI/CD do pipeline + CT acionado por dados/drift, feature store, validação automática de dados e modelo, canary/shadow
Nível 3: plataforma self-service, governança/fairness automatizada, otimização de custo, multi-modelo em escala
```

Evolua **incrementalmente**, guiado por incidentes e gargalos reais (não por ferramentas da moda).

## Anti-padrões

- "Notebook em produção"; modelo sem dataset/código versionados.
- Retreino automático **sem gates** (degradação silenciosa/feedback loops).
- Plataforma MLOps sofisticada para 1 modelo (over-engineering).
- Equipes em silos (DS "joga o modelo por cima do muro" ao engenheiro).
- Monitoramento só de infra; sem ground truth/drift.
- Falta de ownership do modelo em produção.

## Boas práticas

- Trate **dados, features, pipelines e modelos como código/artefatos versionados**; reprodutibilidade
  ponta a ponta.
- Automatize CI/CD/**CT** com **gates** de dados e de modelo; promova via registry; deploy gradual.
- Monitore infra + dados + modelo + negócio; feche o loop (feedback → retreino).
- Comece pequeno e evolua; padronize templates/ferramentas; ownership claro; governança e privacidade desde o
  desenho.

## Relação com outros conceitos

- [DataOps](../../23-cicd-dataops/05-dataops/README.md), [CI/CD](../../23-cicd-dataops/README.md),
  [IaC](../../22-infrastructure-as-code/README.md), [containers/K8s](../../20-containers/README.md),
  [training pipelines](../04-training-pipelines/README.md), [serving](../05-model-serving/README.md),
  [drift](../06-ml-observability-drift/README.md), [governança](../../25-data-governance/README.md).

## Exercícios

1. Desenhe o ciclo completo (dados→features→treino→registro→deploy→monitoramento→retreino) para um modelo de
   churn, marcando CI, CD e CT.
2. Defina os gates automáticos que um modelo candidato deve passar antes de ir a produção.
3. Descreva o papel de cada papel (DE, MLE, DS, MLOps) num incidente de degradação do modelo.
4. Avalie a maturidade MLOps de uma equipe fictícia e proponha os 3 próximos passos.

## Referências

- Sculley et al., "Hidden Technical Debt in ML Systems" (2015); Google, "MLOps: Continuous delivery and
  automation pipelines in ML"; Kreuzberger et al., "Machine Learning Operations (MLOps): Overview, Definition,
  and Architecture" (2022); Huyen, C. *Designing ML Systems*; docs de MLflow, Kubeflow, TFX, Vertex/SageMaker.
