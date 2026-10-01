# Pods e Deployments

> 🟣 Cloud & Infra · Parte de [21 — Kubernetes](../README.md)

## Pod

O **Pod** é a menor unidade de execução: um ou mais containers que **compartilham rede (IP/porta) e
volumes** e são agendados juntos no mesmo nó. Normalmente **um container principal** por Pod; containers
auxiliares (*sidecars*, *init containers*) cooperam com ele.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: etl-once
  labels: {app: etl}
spec:
  containers:
    - name: etl
      image: ghcr.io/org/pipeline:1.4.2
      args: ["--date", "2024-01-15"]
      resources:
        requests: {cpu: "500m", memory: "1Gi"}
        limits:   {memory: "2Gi"}
```

Pods são **efêmeros**: podem ser recriados em outro nó, com **novo IP**. Por isso não se cria Pods "soltos"
em produção — usa-se controladores (Deployment, Job...).

### Init containers e sidecars

- **Init container** — roda **antes** do principal, até concluir (ex.: esperar o banco, baixar config,
  rodar migração).
- **Sidecar** — roda junto (ex.: agente de logs, proxy, sincronizador).

## Probes (saúde)

O kubelet usa probes para saber se o container está vivo/pronto:

- **liveness** — está travado? → reinicia o container.
- **readiness** — pronto para receber tráfego? → entra/sai do Service.
- **startup** — para aplicações de inicialização lenta.

```yaml
readinessProbe: {httpGet: {path: /health, port: 8080}, periodSeconds: 5}
livenessProbe:  {httpGet: {path: /health, port: 8080}, initialDelaySeconds: 15}
```

## Deployment (stateless com réplicas)

Um **Deployment** declara **N réplicas** de um Pod template e gerencia **rolling updates** e rollback
(via ReplicaSets). Ideal para serviços **stateless**: APIs, serving de modelos, workers consumidores.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: {name: feature-api}
spec:
  replicas: 3
  selector: {matchLabels: {app: feature-api}}
  strategy:
    type: RollingUpdate
    rollingUpdate: {maxUnavailable: 0, maxSurge: 1}
  template:
    metadata: {labels: {app: feature-api}}
    spec:
      containers:
        - name: api
          image: ghcr.io/org/feature-api:2.1.0
          ports: [{containerPort: 8080}]
          resources:
            requests: {cpu: "250m", memory: "512Mi"}
            limits: {memory: "1Gi"}
          readinessProbe: {httpGet: {path: /health, port: 8080}}
```

### Rolling update e rollback

Atualizar a imagem cria novos Pods gradualmente e remove os antigos (sem downtime se a readiness estiver
correta). Ver [deployment strategies](../../23-cicd-dataops/06-deployment-strategies/README.md).

```bash
kubectl set image deployment/feature-api api=ghcr.io/org/feature-api:2.2.0
kubectl rollout status deployment/feature-api
kubectl rollout undo deployment/feature-api        # rollback
```

## Outros controladores (quando usar)

| Controlador | Uso |
| --- | --- |
| **Deployment** | stateless, réplicas intercambiáveis |
| **StatefulSet** | estado/identidade estável (Kafka, bancos) — [volumes](../06-volumes/README.md) |
| **DaemonSet** | um Pod por nó (agentes de log/monitoramento) |
| **Job / CronJob** | batch / agendado — [04](../04-jobs-cronjobs/README.md) |

## Em dados

- **Consumidores de streaming** como Deployment (escala por [lag](../07-scaling-resources/README.md)).
- **APIs de serving/feature store online** como Deployment atrás de um Service.
- **Airflow**: scheduler/webserver como Deployments; tasks como Pods efêmeros (KubernetesExecutor).

## Erros comuns

- Pods soltos sem controlador (não se recuperam).
- Sem readiness probe → tráfego para Pod não pronto durante deploy.
- Liveness agressiva demais (reinícios em loop).
- Sem requests/limits (scheduling ruim, OOMKilled).
- `latest` na imagem (deploys não reprodutíveis).

## Boas práticas

- Deployment para stateless; probes de readiness/liveness; recursos definidos; tags fixas.
- `maxUnavailable: 0` para zero downtime quando possível.
- Consumidores idempotentes (Pods reiniciam — [idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).

## Relação com outros conceitos

- [Conceitos](../01-concepts-architecture/README.md), [Services](../03-services-networking/README.md),
  [scaling](../07-scaling-resources/README.md), [containers](../../20-containers/README.md).

## Exercícios

1. Crie um Deployment com 3 réplicas e uma readiness probe; faça um rolling update e um rollback.
2. Explique liveness vs readiness com um exemplo de falha de cada.
3. Escolha o controlador para: API de serving; agente de logs; consumidor Kafka; banco.

## Referências

- Kubernetes Docs — Pods, Deployments, Probes, Workloads.
