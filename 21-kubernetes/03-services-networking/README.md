# Services e networking

> 🟣 Cloud & Infra · Parte de [21 — Kubernetes](../README.md)

## O problema

Pods são efêmeros: o IP muda a cada recriação. Como outros componentes os encontram de forma estável? E
como expor um serviço para fora do cluster? **Services** e **Ingress** resolvem isso.

## Service

Um **Service** dá um **endereço estável (IP virtual + nome DNS)** e **balanceia carga** entre os Pods
selecionados por **labels**.

```yaml
apiVersion: v1
kind: Service
metadata: {name: feature-api}
spec:
  selector: {app: feature-api}      # Pods com este label recebem o tráfego
  ports: [{port: 80, targetPort: 8080}]
  type: ClusterIP
```

Dentro do cluster: `http://feature-api` (ou `feature-api.dados-prod.svc.cluster.local`). Apenas Pods
**prontos** (readiness) entram no balanceamento.

### Tipos

| Tipo | Alcance | Uso |
| --- | --- | --- |
| **ClusterIP** (padrão) | interno ao cluster | comunicação entre serviços |
| **NodePort** | porta em cada nó | debug/dev |
| **LoadBalancer** | LB do provedor cloud (IP externo) | expor serviço (TCP) |
| **ExternalName** | alias DNS para serviço externo | apontar para DB/API fora do cluster |
| **Headless** (`clusterIP: None`) | DNS retorna IPs dos Pods | StatefulSets (Kafka, bancos) |

## Ingress (HTTP/HTTPS)

**Ingress** roteia tráfego HTTP(S) externo para Services por **host/path**, com TLS — um ponto de entrada
para várias aplicações. Requer um **Ingress Controller** (NGINX, Traefik, ALB/GCE). A API sucessora é a
**Gateway API**.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata: {name: airflow}
spec:
  rules:
    - host: airflow.empresa.com
      http:
        paths: [{path: /, pathType: Prefix, backend: {service: {name: airflow-web, port: {number: 8080}}}}]
  tls: [{hosts: [airflow.empresa.com], secretName: airflow-tls}]
```

## Descoberta de serviços (DNS)

O DNS do cluster (CoreDNS) resolve nomes de Services. Componentes se encontram por **nome**, nunca por IP —
mesma ideia do [Compose](../../20-containers/04-docker-compose/README.md).

## Rede de Pods e segurança

- Todo Pod tem IP próprio e **pode falar com qualquer outro** por padrão (rede plana).
- **NetworkPolicies** restringem quem fala com quem (comece com *default-deny* e libere o necessário) —
  essencial para isolar bancos/Kafka ([segurança de rede](../../26-security/05-network-security/README.md),
  [container security](../../20-containers/07-container-security/README.md)).
- Tráfego para fora (egress) do cluster: NAT/endpoints privados ([cloud networking](../../19-cloud/05-networking/README.md)).

## Em dados

- **Serving**: Deployment + Service (+ Ingress/LB) para APIs de modelo/feature.
- **Kafka/Spark/Airflow UI**: acesso via Service interno, `kubectl port-forward` para debug, Ingress
  autenticado para UIs.
- Bancos gerenciados fora do cluster: **ExternalName** ou endpoint privado.

```bash
kubectl port-forward svc/airflow-web 8080:8080     # acesso local temporário
```

## Erros comuns

- Selector/labels que não casam → Service sem endpoints (`kubectl get endpoints`).
- Expor UIs/bancos via LoadBalancer público sem autenticação.
- Sem NetworkPolicy (qualquer Pod acessa o banco).
- Usar IP de Pod em vez do nome do Service.
- Esquecer a readiness probe (tráfego para Pod não pronto).

## Boas práticas

- Services ClusterIP por padrão; Ingress com TLS e autenticação para o que for externo.
- NetworkPolicies default-deny; labels consistentes.
- Verifique `kubectl get endpoints <svc>` ao depurar conectividade.

## Relação com outros conceitos

- [Pods/Deployments](../02-pods-deployments/README.md), [cloud networking](../../19-cloud/05-networking/README.md),
  [segurança de rede](../../26-security/05-network-security/README.md).

## Exercícios

1. Exponha um Deployment com um Service ClusterIP e chame-o de outro Pod pelo nome.
2. Escreva um Ingress com TLS para uma UI interna.
3. Escreva uma NetworkPolicy que só permite o namespace `dados` acessar o banco.
4. Depure um Service sem tráfego usando `get endpoints` e `describe`.

## Referências

- Kubernetes Docs — Services, Ingress/Gateway API, Network Policies, DNS.
