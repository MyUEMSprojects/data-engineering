# 21 — Kubernetes (orientado a Data Engineering)

> 🟣 Nível 6 — Cloud & Infra · Pré: [20 — Containers](../20-containers/README.md) ·
> Próximo: [22 — IaC](../22-infrastructure-as-code/README.md)

**Kubernetes (K8s)** orquestra containers em cluster: agenda, escala, recupera e conecta cargas de
trabalho. Em dados, é onde rodam cada vez mais **Airflow, Spark, Flink, Kafka operators e serviços de
serving**. Este módulo é uma **introdução focada no que o Data Engineer usa** — não um curso completo de
K8s.

> Pragmatismo: Kubernetes é poderoso e **complexo**. Se serviços gerenciados/serverless resolvem, prefira-os.
> Aprenda K8s o suficiente para operar/diagnosticar pipelines e conversar com o time de plataforma.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Conceitos e arquitetura](01-concepts-architecture/README.md) | Cluster, control plane, nós |
| 02 | [Pods e Deployments](02-pods-deployments/README.md) | Unidade de execução e réplicas |
| 03 | [Services e networking](03-services-networking/README.md) | Descoberta e exposição |
| 04 | [Jobs e CronJobs](04-jobs-cronjobs/README.md) | Cargas batch |
| 05 | [ConfigMaps e Secrets](05-configmaps-secrets/README.md) | Configuração e segredos |
| 06 | [Volumes](06-volumes/README.md) | Persistência (PV/PVC) |
| 07 | [Scaling e recursos](07-scaling-resources/README.md) | Requests/limits, HPA, autoscaling |
| 08 | [Observabilidade](08-observability/README.md) | Logs, métricas, debug com kubectl |

## Dependências internas

```text
Conceitos ─► Pods/Deployments ─► Services ─► ConfigMaps/Secrets ─► Volumes
                   │
                   ├─► Jobs/CronJobs (batch)
                   └─► Scaling/recursos ─► Observabilidade
```

## Checkpoint

- [ ] Descrever a arquitetura do K8s (control plane, nós, kubelet, etcd).
- [ ] Escrever um Deployment e um Service; explicar réplicas e rolling update.
- [ ] Rodar um job batch (Job/CronJob) com retries e limites.
- [ ] Injetar config/segredos via ConfigMap/Secret.
- [ ] Persistir dados com PV/PVC e entender StatefulSets.
- [ ] Definir requests/limits e escalar (HPA/KEDA).
- [ ] Depurar com `kubectl logs/describe/get events`.

## Referências do módulo

- Documentação oficial do Kubernetes (kubernetes.io/docs).
- Burns, B. et al. *Kubernetes: Up & Running*, O'Reilly.
