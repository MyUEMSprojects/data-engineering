# Conceitos e arquitetura

> 🟣 Cloud & Infra · Parte de [21 — Kubernetes](../README.md)

## O que é

**Kubernetes** é uma plataforma de orquestração de containers que gerencia um **cluster** de máquinas:
decide **onde** rodar cada container, **mantém** o estado desejado (réplicas, saúde), **escala**,
**atualiza** sem downtime e conecta serviços. Você declara **o que quer** (YAML); o K8s trabalha
continuamente para **convergir** o estado real a esse estado desejado.

## Por que importa para DE

- **Airflow** (KubernetesExecutor/Operator), **Spark on K8s**, **Flink** e **Kafka** (via operators) rodam
  em K8s.
- Serving de modelos/features, APIs e jobs de dados num mesmo plano de operação.
- Elasticidade: workers efêmeros que sobem para o job e somem (custo).

## Arquitetura

```text
┌────────────── Control Plane ───────────────┐
│ API Server  etcd  Scheduler  Controllers    │   ← cérebro: guarda estado, decide, reconcilia
└──────────────────────┬─────────────────────┘
                       │
   ┌───────────────────┼───────────────────┐
   ▼                   ▼                   ▼
 Node 1              Node 2              Node 3        ← workers (VMs)
 kubelet+runtime     kubelet+runtime     kubelet+runtime
 [Pod][Pod]          [Pod][Pod]          [Pod]
```

| Componente | Papel |
| --- | --- |
| **API Server** | porta de entrada (kubectl/CI falam com ele); tudo é recurso via API |
| **etcd** | banco chave-valor com o estado do cluster ([consenso/Raft](../../01-foundations/05-distributed-systems-fundamentals/README.md)) |
| **Scheduler** | decide em qual nó cada Pod roda (recursos, afinidade) |
| **Controller manager** | loops que reconciliam estado (Deployment→ReplicaSet→Pods) |
| **kubelet** | agente no nó; garante que os containers do Pod rodem |
| **Container runtime** | containerd/CRI-O executa containers |
| **kube-proxy / CNI** | rede de Pods e Services |

## O modelo declarativo (reconciliação)

```text
Você: "quero 3 réplicas da imagem X"  ──► grava no API Server (estado desejado)
Controller: "há 2 rodando" ──► cria mais 1 ──► converge
Um nó cai ──► controller percebe 2 réplicas ──► recria em outro nó (auto-recuperação)
```

É o mesmo princípio de [IaC declarativa](../../22-infrastructure-as-code/README.md): descreva o estado, não
os passos.

## Objetos fundamentais (mapa)

| Objeto | Função | Tópico |
| --- | --- | --- |
| **Pod** | menor unidade: 1+ containers com rede/volumes compartilhados | [02](../02-pods-deployments/README.md) |
| **Deployment** | réplicas + rolling update de Pods stateless | [02](../02-pods-deployments/README.md) |
| **Service** | endereço estável + balanceamento para Pods | [03](../03-services-networking/README.md) |
| **Job / CronJob** | execução batch / agendada | [04](../04-jobs-cronjobs/README.md) |
| **ConfigMap / Secret** | configuração / segredos | [05](../05-configmaps-secrets/README.md) |
| **PV / PVC / StatefulSet** | armazenamento / estado | [06](../06-volumes/README.md) |
| **Namespace** | isolamento lógico (times/ambientes) | abaixo |

## Namespaces, labels e selectors

- **Namespace** — particiona o cluster (`dados-dev`, `dados-prod`) com quotas e RBAC por namespace.
- **Labels** — pares chave/valor em objetos (`app=airflow`); **selectors** os selecionam (é como Service
  encontra Pods).

## kubectl essencial

```bash
kubectl get pods -n dados-prod
kubectl apply -f deployment.yaml          # declarativo (cria/atualiza)
kubectl describe pod <pod>                # eventos, motivo de falha
kubectl logs -f <pod> [-c container]
kubectl exec -it <pod> -- sh
kubectl delete -f deployment.yaml
```

## Clusters: onde rodar

- **Gerenciado**: EKS (AWS), GKE (GCP), AKS (Azure) — control plane operado pelo provedor (**recomendado**).
- **Local para estudo**: kind, minikube, k3d, Docker Desktop.
- Self-managed (kubeadm) só com time de plataforma dedicado.

## Trade-offs

- **Poder × complexidade**: curva de aprendizado alta, muitas peças (rede, storage, segurança).
- Custo operacional (upgrades, add-ons) — gerenciado reduz, não elimina.
- Para estado (bancos), prefira serviços gerenciados; K8s brilha em **cargas stateless/batch**.

## Erros comuns

- Adotar K8s sem necessidade (um serviço gerenciado/serverless bastaria).
- Tratar Pods como permanentes (são efêmeros; IP muda).
- Rodar bancos críticos em K8s sem experiência (operators/StatefulSets exigem cuidado).
- Sem requests/limits e sem namespaces/RBAC.

## Boas práticas

- Cluster gerenciado; namespaces por ambiente/time; tudo versionado como código (YAML/Helm/IaC).
- Imagens com tags fixas; recursos definidos; probes de saúde.
- Comece com o mínimo de objetos necessários.

## Relação com outros conceitos

- [Containers](../../20-containers/README.md), [Airflow](../../11-orchestration/02-airflow/README.md),
  [Spark](../../16-distributed-processing/README.md), [IaC](../../22-infrastructure-as-code/README.md),
  [cloud compute](../../19-cloud/03-compute/README.md).

## Exercícios

1. Suba um cluster local (kind/minikube) e liste os componentes do control plane.
2. Explique o loop de reconciliação com o exemplo de um nó que cai.
3. Dê 3 cargas de dados que fazem sentido em K8s e 1 que não.

## Referências

- Kubernetes Docs — Concepts, Cluster Architecture; Burns et al., *Kubernetes: Up & Running*.
