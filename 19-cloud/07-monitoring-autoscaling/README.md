# Monitoring e autoscaling

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)

> Fundamentos de observabilidade em [24 — Observability](../../24-observability/README.md); aqui, a
> visão de **serviços cloud** para monitorar infraestrutura e **escalar** automaticamente.

## Monitoring em cloud

Serviços nativos coletam **métricas, logs e traces** da infraestrutura e dos serviços gerenciados:

| Função | AWS | GCP | Azure |
| --- | --- | --- | --- |
| Métricas/alertas | CloudWatch | Cloud Monitoring | Azure Monitor |
| Logs | CloudWatch Logs | Cloud Logging | Log Analytics |
| Tracing | X-Ray | Cloud Trace | Application Insights |
| Auditoria de API | CloudTrail | Cloud Audit Logs | Activity Log |

### O que monitorar em plataformas de dados

- **Infra**: CPU, memória, disco, rede dos nós/clusters.
- **Serviços gerenciados**: conexões/IOPS/lag de réplica (DB), slots/bytes (warehouse), lag do consumer
  (Kafka — ver [backpressure](../../18-message-brokers/06-backpressure/README.md)).
- **Pipelines**: sucesso/falha, duração, volume, frescor ([observability de pipelines](../../10-data-pipelines/08-pipeline-observability/README.md)).
- **Custo**: gasto por serviço/tag/projeto ([cost](../08-cost-management/README.md)).

### Alertas

Acionáveis, com severidade e dono; evite *alert fatigue*. Defina limiares por **SLOs**
([SLI/SLO/SLA](../../24-observability/05-sli-slo-sla/README.md)). Notifique via PagerDuty/Slack/e-mail.
Alertas de **orçamento** também (surpresas de custo).

## Autoscaling

Ajustar capacidade **automaticamente** à demanda, evitando superprovisionar (custo) e subprovisionar
(lentidão/falha).

### Tipos

- **Horizontal** — adicionar/remover instâncias/réplicas/pods (mais comum e elástico).
- **Vertical** — aumentar tamanho do recurso (CPU/RAM) — geralmente exige reinício.

### Onde aparece em dados

- **Grupos de VMs** (Auto Scaling Groups / Managed Instance Groups / VMSS) — escala por métrica
  (CPU, fila).
- **Kubernetes** — HPA (pods por CPU/métrica customizada), Cluster Autoscaler/Karpenter (nós);
  **KEDA** escala por **lag de Kafka/tamanho de fila** ([K8s](../../21-kubernetes/README.md)).
- **Spark/EMR/Dataproc/Databricks** — autoscaling de executors/workers conforme carga do job.
- **Warehouses** — Snowflake multi-cluster/auto-suspend, BigQuery slots autoscaling, Redshift
  concurrency scaling/Serverless ([warehouse](../../13-data-warehouse/README.md)).
- **Serverless** — escala a zero e para cima automaticamente.

### Métrica certa para escalar

| Carga | Métrica de escala |
| --- | --- |
| API/serviço | CPU, latência, requests/s |
| Consumidor de streaming | **consumer lag** / profundidade da fila |
| Batch Spark | tarefas pendentes / memória |
| Warehouse | concorrência/fila de queries |

### Cuidados

- **Cooldown/estabilização** para evitar *flapping* (escala sobe e desce em loop).
- **Limites mín/máx** (teto de custo, piso de disponibilidade).
- Escala **não resolve** gargalos não-paralelizáveis ([skew](../../16-distributed-processing/04-distributed-joins-skew/README.md),
  partições limitando consumidores, lock no banco).
- **Tempo de provisionamento** (nós novos demoram) — antecipe picos previsíveis (escala agendada).

## Erros comuns

- Sem alertas de custo/orçamento.
- Autoscaling sem limite máximo → conta explosiva.
- Escalar por CPU um consumidor limitado por lag/partições.
- Alertas ruidosos ignorados.
- Monitorar infra e esquecer a saúde dos **dados**.

## Boas práticas

- Dashboards + alertas por SLO; logs centralizados e retenção definida.
- Autoscaling com métricas adequadas, cooldown e limites; escala agendada p/ picos conhecidos.
- Tags de custo + alertas de orçamento; revisão periódica.

## Relação com outros conceitos

- [Observability](../../24-observability/README.md), [cost](../08-cost-management/README.md),
  [Kubernetes](../../21-kubernetes/README.md), [compute](../03-compute/README.md).

## Exercícios

1. Defina métricas e alertas para um pipeline Kafka→lake (infra + dados).
2. Escolha a métrica de autoscaling para um consumidor Kafka e explique o limite imposto pelas partições.
3. Configure (conceitualmente) um alerta de orçamento mensal com 3 limiares.

## Referências

- Documentação de CloudWatch/Cloud Monitoring/Azure Monitor; Kubernetes HPA, KEDA.
- Google SRE Book — monitoring distributed systems.
