# ML observability e drift

> 🟣 ML Integration · Parte de [31 — DE + ML](../README.md)

## O que é

**Observabilidade de ML** é monitorar **modelos em produção** — não só a infraestrutura de serving
([observability](../../24-observability/README.md)), mas a **qualidade dos dados de entrada, o
comportamento do modelo e o seu desempenho real**. Modelos **degradam silenciosamente** porque o mundo muda:
um modelo pode estar "no ar, rápido e sem erros" e **estar errado**.

> Software tradicional falha **explicitamente** (exceção). ML falha **silenciosamente** (predições piores
> sem nenhum erro). Por isso é essencial monitorar **dados e predições**.

## O que monitorar (camadas)

| Camada | Perguntas | Exemplos |
| --- | --- | --- |
| **Infra/serving** | está de pé, rápido, escalando? | latência p95/p99, erro, QPS, CPU/GPU, custo ([métricas](../../24-observability/02-metrics/README.md)) |
| **Dados/features** | os **inputs** são válidos e parecidos com o treino? | schema, nulos, faixas, **drift de features**, frescor ([freshness](../../24-observability/06-data-freshness/README.md)) |
| **Predições/saídas** | a distribuição das predições mudou? | média/distribuição do score, taxa de classes, confiança |
| **Performance do modelo** | **acerta**? | accuracy/AUC/RMSE/etc. com **ground truth** (quando chega) |
| **Negócio** | o modelo gera valor? | conversão, fraude evitada, receita, KPIs |
| **Justiça/segurança** | vieses, abusos, ataques? | métricas por grupo; detecção de entradas adversariais |

## Tipos de drift (o conceito central)

**Drift** = mudança ao longo do tempo que **degrada** a adequação do modelo.

### 1. Data drift / covariate shift — P(X) muda

A **distribuição das features de entrada** muda em relação ao treino (ex.: novo perfil de clientes, mudança de
canal, sazonalidade, mudança de sensor/unidade). A relação X→Y pode ainda valer, mas o modelo vê regiões do
espaço que não conhecia.

### 2. Concept drift — P(Y|X) muda

A **relação entre features e alvo** muda (ex.: o que indica fraude evolui; comportamento pós-pandemia).
O modelo **fica errado mesmo com inputs "normais"**. Variantes: **súbito**, **gradual**, **incremental**,
**recorrente/sazonal**.

### 3. Label/prior drift — P(Y) muda

A proporção das classes muda (ex.: taxa de fraude aumenta).

### 4. Feature/schema drift (operacional)

Mudanças **upstream** quebram/alteram features: coluna renomeada, unidade trocada, valores nulos, atraso de
dados, bug de pipeline — **não é "o mundo mudou", é dado quebrado** (resolver com
[qualidade](../../12-data-quality/README.md) e [contratos](../../29-data-contracts/README.md)).

### 5. Training-serving skew

Diferença **sistemática** entre as features no treino e no serving (lógica diferente, dados faltando online)
— ver [feature stores](../03-feature-stores-online-offline/README.md).

## Como detectar

### Sem ground truth (imediato) — monitorar **distribuições**

Compare a distribuição **atual (janela recente)** com a **referência** (dados de treino ou janela estável):

| Técnica | Para |
| --- | --- |
| **PSI** (Population Stability Index) | features numéricas/categóricas binadas; regra prática: <0,1 estável, 0,1–0,25 atenção, >0,25 mudança grande |
| **KS test / Kolmogorov–Smirnov** | numéricas contínuas |
| **Chi-quadrado** | categóricas |
| **Jensen–Shannon / KL / Wasserstein (EMD)** | distância entre distribuições |
| **Estatísticas simples** | média, desvio, % nulos, cardinalidade, min/max |
| **Classificador de domínio** | treina um modelo para distinguir treino vs produção; AUC alta ⇒ drift |
| **Drift multivariado** | PCA/embeddings/autoencoders; detecção em espaço de embeddings |

Aplique a **features**, **predições** e (quando possível) **embeddings**. Cuidado com **falsos positivos**
(drift estatisticamente significativo mas irrelevante) — considere **tamanho do efeito** e **importância da
feature**.

### Com ground truth (atrasado) — monitorar **performance**

Quando os rótulos reais chegam (às vezes dias/meses depois — churn, inadimplência), calcule as métricas e
acompanhe a **degradação**. Requer **pipeline de feedback**: juntar predição (com `request_id`/`model_version`)
ao desfecho real ([serving: logging](../05-model-serving/README.md)).

- Enquanto o rótulo não vem, use **proxies** (distribuição de scores, métricas de negócio rápidas) e
  **performance estimada** (métodos como CBPE/NannyML).
- **Avaliar por fatias** (segmentos) — a média pode esconder falhas locais.

## Arquitetura de monitoramento

```text
Serving ─► logs de (entradas, features, predição, versão, request_id) ─► lake/streaming
                                                                           │
Ground truth (tardio) ─► join por request_id ──────────────────────────────┤
                                                                           ▼
              Jobs de monitoramento (batch/streaming): drift, qualidade, performance ─► métricas/dashboards ─► ALERTAS ─► ação
```

- Reutilize a **plataforma de dados**: logs no lake ([lakehouse](../../15-lakehouse/README.md)), jobs
  agendados ([orquestração](../../11-orchestration/README.md)), métricas no Prometheus/warehouse, alertas
  ([alertas](../../24-observability/04-alerting/README.md)).
- Amostragem de tráfego para reduzir custo; **retenção** e **privacidade** (minimizar/mascarar PII nos logs —
  [LGPD](../../26-security/08-lgpd/README.md)).

## Ferramentas

| Tipo | Exemplos |
| --- | --- |
| **Open source** | **Evidently**, **NannyML**, **whylogs/WhyLabs**, **Great Expectations** (qualidade), deepchecks, Alibi Detect |
| **Plataformas** | Arize, Fiddler, Superwise, Datadog/New Relic ML, **SageMaker Model Monitor**, **Vertex AI Model Monitoring**, Azure ML, Databricks Lakehouse Monitoring |
| **DIY** | SQL/Spark no lake + Grafana/alertas |

## Respondendo ao drift (ação)

```text
Detectou drift/degradação
   ├─ É quebra de dado/pipeline? ─► corrigir upstream (qualidade/contrato), reprocessar
   ├─ Drift real moderado? ────────► retreinar com dados recentes (ver gatilhos em training pipelines)
   ├─ Concept drift grave? ────────► redesenhar features/modelo; reavaliar o problema
   └─ Crítico? ────────────────────► fallback (modelo anterior/regra), degradar com segurança, escalar incidente
```

- **Retreino**: agendado, por gatilho de drift/performance, com **validação e gates**
  ([training pipelines](../04-training-pipelines/README.md)); cuidado com **feedback loops** (o modelo
  influencia os dados que depois treinam o próprio modelo).
- **Janela de treino**: usar dados recentes vs todo o histórico (trade-off estabilidade × adaptação).
- **Aprendizado online/incremental** em casos específicos (complexidade/risco).
- **Resposta a incidentes** com runbooks ([incident response](../../24-observability/07-incident-response/README.md)).

## SLOs e alertas para ML

Defina **SLOs** de modelo (ex.: AUC ≥ X semanal; PSI de features-chave < 0,2; atraso de ground truth ≤ D+3;
latência p99 ≤ Y) e alerte por **violação sustentada/burn rate**, não por ruído
([SLO](../../24-observability/05-sli-slo-sla/README.md), [alertas](../../24-observability/04-alerting/README.md)).
Priorize **features mais importantes** (por importância/SHAP) para reduzir ruído.

## Desafios

- **Ground truth tardio/ausente** (difícil medir performance) → proxies, amostragem, rotulagem.
- **Alta dimensionalidade** e muitas features → alertas em excesso; priorize.
- **Sazonalidade vs drift** (variação esperada ≠ problema) → baselines sazonais.
- **Falsos positivos/negativos** de testes estatísticos (amostras grandes tornam tudo "significativo").
- **Custo** de logar/processar tudo; **privacidade**.
- **Responsabilidade difusa** (DE, MLE, DS) → ownership claro ([ownership](../../25-data-governance/04-ownership-stewardship/README.md)).

## Erros comuns

- Monitorar só infraestrutura (modelo pode estar ruim com tudo "verde").
- Não registrar entradas/predições/versão (impossível investigar).
- Esperar o rótulo para detectar problemas (tarde demais) — falta monitoramento de distribuições.
- Alertas por qualquer diferença estatística (ruído) em vez de efeito relevante.
- Retreinar automaticamente sem gates (promove modelo pior; feedback loop).
- Confundir dado quebrado (bug/pipeline) com drift "natural".
- PII em logs de monitoramento.

## Boas práticas

- Monitore **dados, predições e performance** (com feedback de ground truth); infra também.
- Defina **referência** (treino/janela estável), métricas de drift por feature (priorizadas) e limiares
  calibrados; baselines sazonais.
- Pipeline de feedback e avaliação por fatias; SLOs e alertas acionáveis com dono e runbook.
- Integre a observabilidade ao **ciclo de retreino/MLOps** com gates e rollback.
- Separe **qualidade de dados/pipeline** de **drift** — corrija a causa certa.

## Relação com outros conceitos

- [Serving](../05-model-serving/README.md), [training pipelines](../04-training-pipelines/README.md),
  [MLOps](../07-mlops-integration/README.md), [observability](../../24-observability/README.md),
  [anomaly detection](../../12-data-quality/07-anomaly-detection/README.md),
  [data quality](../../12-data-quality/README.md), [incident response](../../24-observability/07-incident-response/README.md).

## Exercícios

1. Diferencie data drift, concept drift e training-serving skew com um exemplo de fraude.
2. Calcule/descreva o PSI de uma feature e interprete 0,05, 0,18 e 0,40.
3. Desenhe o pipeline de monitoramento (logs → ground truth tardio → métricas → alertas) para um modelo de churn.
4. Que ação você toma se a performance cai mas nenhuma feature apresenta drift (suspeita de concept drift)?

## Referências

- Huyen, C. *Designing ML Systems* (monitoramento/drift); Gama et al., "A Survey on Concept Drift Adaptation"
  (2014); Breck et al., "The ML Test Score"; docs de Evidently, NannyML, whylogs, SageMaker/Vertex Model Monitor.
