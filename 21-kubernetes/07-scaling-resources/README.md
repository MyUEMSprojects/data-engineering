# Scaling e recursos

> 🟣 Cloud & Infra · Parte de [21 — Kubernetes](../README.md)

## Requests e limits (a base de tudo)

Cada container declara quanto de **CPU e memória** precisa e pode usar:

```yaml
resources:
  requests: {cpu: "500m", memory: "1Gi"}   # reservado; usado pelo scheduler p/ escolher o nó
  limits:   {memory: "2Gi"}                # teto; ultrapassar memória → OOMKilled
```

| | Significado | Efeito |
| --- | --- | --- |
| **requests** | quantidade garantida/reservada | o **scheduler** só coloca o Pod num nó com sobra |
| **limits** | máximo permitido | **CPU**: throttling; **memória**: processo é morto (`OOMKilled`) |

- CPU em *millicores* (`500m` = 0,5 core); memória em `Mi/Gi`.
- **Sem requests** → scheduling imprevisível e *noisy neighbors*; **sem limit de memória** → um Pod pode
  derrubar o nó.
- **OOMKilled** (exit 137) é a falha clássica de jobs de dados (pandas/Spark estourando memória) — ver
  [troubleshooting/OOM](../../02-linux-shell-environment/08-logs-and-troubleshooting/README.md),
  [Spark tuning](../../16-distributed-processing/11-performance-tuning/README.md).
- Dica prática: para memória, `request == limit` (previsibilidade); para CPU, muitas vezes definir
  `request` e **omitir** limit (evita throttling desnecessário).

### QoS classes

`Guaranteed` (request=limit), `Burstable`, `BestEffort` — sob pressão do nó, `BestEffort` é despejado
primeiro.

### ResourceQuota e LimitRange

Por **namespace**, limitam o total consumível e definem defaults — governança de custo/capacidade por time
([cost](../../19-cloud/08-cost-management/README.md)).

## Escalando cargas

### Horizontal Pod Autoscaler (HPA)

Ajusta o **nº de réplicas** de um Deployment conforme métricas:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: {name: feature-api}
spec:
  scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: feature-api}
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource: {name: cpu, target: {type: Utilization, averageUtilization: 70}}
```

Funciona bem para serviços (CPU/latência/requests). Exige `requests` definidos.

### KEDA (escala orientada a eventos)

**KEDA** escala por **métricas externas** e pode ir a **zero**: **consumer lag do Kafka**, tamanho de fila
(SQS/RabbitMQ), cron, etc. Ideal para **consumidores de streaming**: mais lag → mais réplicas (limitadas
pelo nº de [partições](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md)).

### VPA (Vertical Pod Autoscaler)

Recomenda/ajusta requests/limits de Pods conforme uso real (ajuda no *rightsizing*).

### Cluster Autoscaler / Karpenter (nós)

Adiciona/remove **nós** quando há Pods não agendáveis por falta de recursos (e remove nós ociosos).
**Karpenter** (AWS) provisiona nós sob medida, rápido, inclusive **spot**. Ligam o autoscaling de Pods ao de
infraestrutura ([compute/spot](../../19-cloud/03-compute/README.md)).

```text
carga ↑ → HPA/KEDA cria Pods → sem nó livre → Cluster Autoscaler/Karpenter adiciona nó
carga ↓ → Pods saem → nós ociosos são removidos (custo ↓)
```

## Em dados

- **Consumidores Kafka**: KEDA por lag, `maxReplicas ≤ partições`.
- **Spark on K8s**: executors são Pods; *dynamic allocation* + Cluster Autoscaler; scheduling em nós spot
  com tolerância a falhas ([idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Jobs batch**: requests dimensionados ao pico real; nós spot para custo.
- **Serving**: HPA por CPU/latência com `minReplicas` para disponibilidade.

## Spot / preemptible, taints e afinidade

- **Taints/tolerations** e **node selectors/affinity** direcionam Pods a pools específicos (GPU, spot,
  memória alta).
- **PodDisruptionBudget (PDB)** limita quantos Pods ficam indisponíveis em manutenções/downscale.
- Cargas em spot devem tolerar interrupção (checkpoints, retries).

## Erros comuns

- Sem requests/limits (HPA não funciona; nós sobrecarregados; OOM).
- Limite de memória abaixo do pico real → `OOMKilled` em loop.
- Escalar consumidores além das partições (sem ganho).
- HPA por CPU num consumidor limitado por lag/I/O.
- Autoscaler sem teto (`maxReplicas`) → conta explosiva.
- Spot sem tolerância a interrupção.

## Boas práticas

- Meça o uso real; defina requests/limits; revise com VPA/observabilidade.
- KEDA por lag para streaming; HPA para serviços; Cluster Autoscaler/Karpenter para nós.
- ResourceQuotas por namespace; PDBs; tetos de escala.
- Spot para batch tolerante, on-demand para serving crítico.

## Relação com outros conceitos

- [Monitoring/autoscaling cloud](../../19-cloud/07-monitoring-autoscaling/README.md),
  [cost](../../19-cloud/08-cost-management/README.md), [Kafka consumers](../../18-message-brokers/03-producers-consumers/README.md),
  [Spark tuning](../../16-distributed-processing/11-performance-tuning/README.md), [observabilidade](../08-observability/README.md).

## Exercícios

1. Defina requests/limits para um job pandas que usa até 3 GiB; explique o risco de limit menor.
2. Configure um HPA por CPU e explique por que requests são obrigatórios.
3. Descreva como KEDA escalaria um consumidor Kafka e o teto imposto pelas partições.
4. Explique a cadeia HPA → Cluster Autoscaler ao subir a carga.

## Referências

- Kubernetes Docs — Resource management, HPA, VPA, Cluster Autoscaler; KEDA; Karpenter.
