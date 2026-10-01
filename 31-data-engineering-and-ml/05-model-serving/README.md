# Model serving

> 🟣 ML Integration · Parte de [31 — DE + ML](../README.md)

## O que é

**Model serving** é disponibilizar um modelo treinado para gerar **predições** (inferência) para
aplicações/usuários/pipelines, com os requisitos certos de **latência, throughput, escala, custo e
confiabilidade**. É onde o modelo vira **produto**; e onde os dados de **features** precisam chegar
**consistentes** com o treino ([feature stores](../03-feature-stores-online-offline/README.md)).

## Os padrões de serving

Escolha pelo **requisito de latência e frescor** — não pela moda:

| Padrão | Latência | Como funciona | Quando |
| --- | --- | --- | --- |
| **Batch inference** | minutos–horas | job agendado prediz para **todas/muitas entidades** e grava o resultado (tabela/cache) | recomendações diárias, scores de risco, segmentação, forecasting |
| **Online (request-response)** | ms–centenas de ms | API recebe requisição, busca features, prediz, responde | fraude em checkout, personalização de página, busca/ranking |
| **Streaming inference** | segundos | consome eventos, prediz continuamente, emite resultados | monitoramento em tempo real, detecção de anomalias em fluxo |
| **Edge/embarcado** | local | modelo roda no dispositivo | mobile/IoT, privacidade, offline |

### Batch inference (o mais simples e subestimado)

```text
Tabela de entidades ─► job (Spark/SQL/Python, agendado) ─► features offline ─► modelo ─► predições gravadas (warehouse/KV)
Aplicação consulta as predições PRÉ-CALCULADAS
```
- **Pré-computa** predições; latência de leitura ≈ lookup. Barato, escalável, fácil de testar/auditar.
- Desvantagem: **defasagem** (predição tão velha quanto o último job) e desperdício se poucas entidades são
  consultadas.
- Em dados: é basicamente um **pipeline ETL** que aplica o modelo
  ([ETL](../../09-etl-elt/README.md), [orquestração](../../11-orchestration/README.md), idempotente e
  parametrizado por data — [backfill](../../09-etl-elt/08-backfill/README.md)).
- Muitos casos de "tempo real" aceitam **batch frequente** — **comece por aqui**.

### Online serving

```text
App ─► API de inferência ─► [busca features no ONLINE store] ─► modelo ─► predição ─► app
                              (+ features on-demand do contexto da requisição)
```
- Requisitos: **p95/p99 de latência**, alta disponibilidade, autoscaling, versionamento/rollout seguro.
- A **latência total** = rede + busca de features + pré-processamento + inferência + pós-processamento. A
  busca de features no online store costuma ser parte relevante — daí a importância do KV rápido
  ([key-value](../../06-databases/04-nosql/01-key-value/README.md)).
- **Contrato da API** (schema de entrada/saída, versão) — [contratos](../../29-data-contracts/README.md);
  protocolos: REST/**gRPC** ([Protobuf](../../08-data-formats/07-protobuf/README.md)).

### Streaming inference

Modelo aplicado **dentro** de um job de stream ([Flink](../../17-streaming/07-flink/README.md)/Spark SS/
Kafka Streams) ou por serviço chamado pelo stream; features por janelas/estado
([stateful](../../17-streaming/05-stateful-processing/README.md)); saída em tópico/sink. Trade-off:
complexidade/estado vs frescor.

## Infraestrutura de serving

| Opção | Notas |
| --- | --- |
| **Servidores de modelo** | **KServe**, **Seldon Core**, **BentoML**, **Triton Inference Server** (NVIDIA; multi-framework, GPU, batching dinâmico), **TorchServe**, **TF Serving**, **Ray Serve**, **MLflow serving** |
| **Plataformas gerenciadas** | **SageMaker Endpoints**, **Vertex AI Endpoints**, **Azure ML Endpoints**, Databricks Model Serving |
| **Serverless** | Lambda/Cloud Run/Functions (modelos pequenos; cold start, limites) |
| **Em app** | modelo embutido na aplicação (biblioteca) — simples, acoplado |
| **LLMs** | **vLLM**, TGI, Triton/TensorRT-LLM, APIs de provedores (outro conjunto de preocupações: tokens, custo, latência) |

Empacotamento: **container** ([Docker](../../20-containers/README.md)) rodando em **[Kubernetes](../../21-kubernetes/README.md)**
(Deployment + Service + HPA/KEDA), com GPU quando necessário.

## Desempenho e custo

- **Latência**: modelos menores/**quantização**/distilação/ONNX/TensorRT; **batching dinâmico** (agrupar
  requisições para throughput GPU); cache de predições/embeddings; co-localizar serviço e online store.
- **Throughput/escala**: réplicas + [autoscaling](../../21-kubernetes/07-scaling-resources/README.md) por
  CPU/latência/QPS; **GPU** vs CPU (custo × ganho).
- **Custo**: dimensionar pela carga real; batch/offline quando possível; scale-to-zero p/ cargas esporádicas;
  spot para batch ([cost](../../19-cloud/08-cost-management/README.md)).
- **Cold start** (modelo grande/serverless): manter réplicas mínimas.

## Deploy seguro de modelos

Aplique [estratégias de deploy](../../23-cicd-dataops/06-deployment-strategies/README.md) ao ML:

- **Shadow**: novo modelo recebe cópia do tráfego, predições **comparadas, não usadas** — valida sem risco.
- **Canary**: pequena fração do tráfego → monitora métricas → expande.
- **A/B testing**: dividir tráfego entre modelos para medir **impacto de negócio** (estatisticamente).
- **Blue/green + rollback rápido**; **versionamento** de modelo e de transformadores; **model registry** como
  fonte de verdade ([MLOps](../07-mlops-integration/README.md)).
- **Fallback**: regra simples/modelo anterior se o novo falhar/timeout.

## Consistência com o treino (evitar skew)

- **Mesmas transformações** (artefatos persistidos: scaler/encoder/vocabulário) e **mesmas definições de
  feature** ([feature engineering](../02-feature-engineering-pipelines/README.md)).
- **Validação de entrada** no serviço (schema/faixas): rejeitar/alertar dados fora do domínio
  ([validação](../../09-etl-elt/10-data-validation/README.md)).
- **Logging de entradas, features e predições** (com `request_id`, `model_version`) para **monitoramento**,
  **depuração**, **retreino** e **auditoria** — respeitando **privacidade** (minimizar/mascarar PII —
  [LGPD](../../26-security/08-lgpd/README.md)).
- **Feedback/ground truth**: capturar resultados reais (rótulos tardios) para medir performance
  ([observabilidade](../06-ml-observability-drift/README.md)).

## Segurança e governança

- **AuthN/AuthZ** na API ([IAM](../../26-security/02-iam/README.md)), rede privada, rate limiting, TLS.
- **Proteção do modelo** (roubo/extração) e contra **ataques adversariais**/prompt injection (LLMs).
- **Explicabilidade/justiça** e **decisões automatizadas** (LGPD art. 20: direito de revisão)
  ([compliance](../../25-data-governance/07-compliance-privacy/README.md)).
- **Auditoria**: qual versão do modelo/feature produziu cada decisão.

## Como escolher (árvore de decisão)

```text
Predição pode ser pré-calculada e ficar levemente defasada?       → BATCH inference (+ servir da tabela/cache)
Precisa responder por requisição com baixa latência?              → ONLINE serving (feature store online + API)
Precisa reagir a um fluxo de eventos em segundos, com estado?     → STREAMING inference
Sem rede/privacidade extrema/latência local?                      → EDGE
```

## Erros comuns

- Construir serving online quando batch resolveria (custo/complexidade).
- Training-serving skew (transformações/features diferentes).
- Sem versionamento/rollback/canary — deploy "big bang" de modelo.
- Não registrar entradas/predições/versão (impossível depurar/monitorar).
- Ignorar latência da busca de features e do pré-processamento (só olhar a inferência).
- Sem fallback/timeouts; sem limites de recurso/autoscaling.
- Esquecer segurança, PII nos logs e requisitos legais de decisões automatizadas.

## Boas práticas

- Comece com **batch**; evolua para online/streaming conforme requisito real.
- Uma definição de features/transformações para treino e serving; validar entradas.
- Deploy gradual (shadow/canary/A-B) com rollback; model registry; versionar tudo.
- Observabilidade do serving (latência, erros, uso) **e** do modelo (drift, performance) — [06](../06-ml-observability-drift/README.md).
- Dimensionar/otimizar por custo; segurança e privacidade desde o desenho.

## Relação com outros conceitos

- [Feature stores](../03-feature-stores-online-offline/README.md), [training pipelines](../04-training-pipelines/README.md),
  [MLOps](../07-mlops-integration/README.md), [observabilidade/drift](../06-ml-observability-drift/README.md),
  [Kubernetes](../../21-kubernetes/README.md), [estratégias de deploy](../../23-cicd-dataops/06-deployment-strategies/README.md),
  [gRPC/Protobuf](../../08-data-formats/07-protobuf/README.md).

## Exercícios

1. Escolha batch/online/streaming para: recomendação diária por e-mail; score de fraude no checkout; alerta de
   anomalia em IoT. Justifique.
2. Desenhe o fluxo de uma requisição de inferência online incluindo busca de features e orçamento de latência.
3. Descreva um rollout canary + shadow de um novo modelo e as métricas de decisão.
4. O que registrar em cada predição para depuração/auditoria sem expor PII?

## Referências

- Huyen, C. *Designing ML Systems* (deployment/serving); docs de KServe, Seldon, BentoML, Triton, Ray Serve,
  SageMaker/Vertex endpoints; Google "Rules of ML".
