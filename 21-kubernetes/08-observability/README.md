# Observabilidade no Kubernetes

> 🟣 Cloud & Infra · Parte de [21 — Kubernetes](../README.md)
>
> Fundamentos em [24 — Observability](../../24-observability/README.md). Aqui: **como observar e
> depurar** cargas de dados em K8s.

## Os três sinais no cluster

### Logs

Containers escrevem em **stdout/stderr**; o runtime os coleta por Pod. Como Pods são efêmeros, os logs
somem com eles — **centralize** (Fluent Bit/Vector → Loki/Elasticsearch/CloudWatch/Cloud Logging).

```bash
kubectl logs <pod>                      # logs do container
kubectl logs -f <pod> -c <container>    # seguir; container específico
kubectl logs <pod> --previous           # do container ANTERIOR (após crash/restart!)
kubectl logs -l app=etl --tail=100      # por label
```

Logue **estruturado (JSON)** com `run_id`/partição ([logging](../../04-python-for-data-engineering/04-errors-and-logging/README.md)).

### Métricas

Padrão de fato: **Prometheus** (coleta) + **Grafana** (dashboards) + **Alertmanager**. Fontes:

- **metrics-server** — CPU/memória de Pods/nós (`kubectl top`; alimenta HPA).
- **kube-state-metrics** — estado dos objetos (réplicas, Pods pending, restarts).
- **Métricas da aplicação** (endpoint `/metrics`): contagens de linhas, duração, lag.
- Exporters: Kafka, Postgres, Spark, Airflow.

Métricas-chave: restarts, `OOMKilled`, CPU throttling, memória vs limit, Pods `Pending`, **consumer lag**,
duração/falhas de Jobs, frescor dos dados ([observability de pipelines](../../10-data-pipelines/08-pipeline-observability/README.md)).

### Traces

OpenTelemetry para rastrear requisições entre serviços (serving, APIs) — menos central em batch.

## Debug com kubectl (roteiro)

```text
1. kubectl get pods -n <ns>                  → status (Pending/CrashLoopBackOff/OOMKilled/Error/Completed)
2. kubectl describe pod <pod>                → Events: por que não agenda/ falhou (recursos, imagem, probe, volume)
3. kubectl logs <pod> [--previous]           → erro da aplicação
4. kubectl get events --sort-by=.lastTimestamp
5. kubectl exec -it <pod> -- sh              → investigar por dentro
6. kubectl top pod/node                      → consumo de recursos
```

### Status comuns e causas

| Status | Causa provável |
| --- | --- |
| **Pending** | sem recurso no nó (requests altos), PVC não ligado, taint/afinidade |
| **ImagePullBackOff** | tag/registry errado, sem credencial ([registries](../../20-containers/05-registries/README.md)) |
| **CrashLoopBackOff** | app falha ao iniciar; veja `logs --previous` |
| **OOMKilled** (137) | memória acima do limit ([recursos](../07-scaling-resources/README.md)) |
| **Error / BackoffLimitExceeded** (Job) | falha do job após retries |
| **Evicted** | pressão de recursos no nó |
| **Service sem tráfego** | selector/labels, readiness ([services](../03-services-networking/README.md)) — `get endpoints` |

## Alertas úteis para plataformas de dados

- Job/CronJob **falhou** ou **não rodou** no horário esperado (dead man's switch).
- Pod em `CrashLoopBackOff`/`OOMKilled` repetidamente.
- **Consumer lag** acima do SLO ([backpressure](../../18-message-brokers/06-backpressure/README.md)).
- Pods Pending por muito tempo; nós sem espaço; PVC quase cheio.
- Frescor/volume de dados fora do esperado.

## Ferramentas de produtividade

- **k9s** (TUI), **Lens**, `stern` (logs multi-Pod), `kubectl-debug`/ephemeral containers
  (`kubectl debug`) para Pods sem shell.
- **Dashboards** prontos (kube-prometheus-stack) para cluster/namespace/Pod.

## Auditoria e segurança

Habilite **audit logs** do API server e monitore acessos a Secrets/RBAC ([security](../../26-security/README.md)).

## Erros comuns

- Logs só no Pod (somem com ele) — sem agregação central.
- Esquecer `--previous` ao depurar crash.
- Alertar só em infra e não em **dados**/jobs.
- Sem `run_id`/contexto nos logs (impossível correlacionar).
- Ignorar `OOMKilled`/throttling (lentidão "misteriosa").

## Boas práticas

- Stack Prometheus+Grafana+logs centralizados; logs JSON com contexto.
- Alertas acionáveis ligados a SLOs; dono definido; runbooks.
- Combine observabilidade de **infra** e de **dados**.
- Use `describe`+`logs --previous`+`events` como primeiro passo.

## Relação com outros conceitos

- [Observability](../../24-observability/README.md), [pipeline observability](../../10-data-pipelines/08-pipeline-observability/README.md),
  [monitoring cloud](../../19-cloud/07-monitoring-autoscaling/README.md),
  [troubleshooting](../../02-linux-shell-environment/08-logs-and-troubleshooting/README.md).

## Exercícios

1. Um Job vira `BackoffLimitExceeded`; descreva os comandos e a ordem para achar a causa.
2. Explique por que `logs --previous` é essencial em `CrashLoopBackOff`.
3. Liste 5 alertas para um pipeline Kafka→lake rodando em K8s.
4. Diferencie Pending, ImagePullBackOff e OOMKilled com causas e correções.

## Referências

- Kubernetes Docs — Logging, Monitoring, Debug Running Pods; Prometheus/Grafana; OpenTelemetry.
