# Segurança de rede

> 🟣 Production · Parte de [26 — Security](../README.md)

> Mecânica de VPC/subnets/security groups em [19 — Networking](../../19-cloud/05-networking/README.md).
> Aqui: o **raciocínio de segurança**.

## O que é

Controlar **quem pode se comunicar com quem**, por quais caminhos e portas, reduzindo a **superfície de
ataque** e limitando o **movimento lateral** de um invasor. Em dados: bancos, brokers, clusters e buckets
**não devem estar expostos à internet**.

## Princípios

- **Defesa em profundidade** — múltiplas camadas (rede, identidade, criptografia, aplicação, dados); a
  falha de uma não derruba tudo.
- **Menor exposição** — só o necessário acessível, só de quem precisa (**deny by default**).
- **Zero trust** — "nunca confie, sempre verifique": estar na rede interna **não** concede confiança; cada
  requisição é autenticada/autorizada ([AuthN/AuthZ](../01-authn-authz/README.md)).
- **Segmentação** — separar ambientes/camadas para limitar o *blast radius*.
- **Criptografia em trânsito** mesmo em rede interna ([encryption](../03-encryption/README.md)).

## Controles principais

### Isolamento e segmentação
- **VPC/VNet** privadas; **subnets públicas** (apenas LB/bastion) e **privadas** (apps, bancos, clusters).
- **Contas/projetos separados** por ambiente/sensibilidade.
- **Kubernetes**: namespaces + **NetworkPolicies default-deny** ([K8s networking](../../21-kubernetes/03-services-networking/README.md)).

### Firewalls
- **Security groups** (stateful, por recurso): libere **portas mínimas** e **origens específicas** (outro
  security group), **nunca `0.0.0.0/0` em portas de dados** (5432, 3306, 9092, 6379, 22, 3389).
- **NACLs** (stateless, por sub-rede), **WAF** para aplicações web/APIs expostas.

### Acesso privado a serviços
- **VPC endpoints / PrivateLink / Private Service Connect**: S3, BigQuery, warehouse acessados **sem
  atravessar a internet pública**.
- **Peering/Transit Gateway/VPN/Direct Connect** para conectar redes de forma controlada.

### Acesso administrativo
- **Sem IP público** em bancos/clusters; acesso via **bastion**/**IAP/SSM Session Manager**/VPN com **MFA**
  e auditoria ([SSH](../../02-linux-shell-environment/07-ssh/README.md)); sem SSH aberto ao mundo.
- Túneis (`ssh -L`) em vez de abrir portas.

### Tráfego de saída (egress)
- Restringir saída (egress filtering) para reduzir **exfiltração** e C2; NAT com allowlist de domínios/IPs
  quando possível. Também reduz custo/risco de egress ([cost](../../19-cloud/08-cost-management/README.md)).

### Proteção contra ataques
- **DDoS** (Shield/Cloud Armor), **rate limiting**, **API gateway**, validação de entrada.
- **IDS/IPS**, **flow logs** (VPC Flow Logs) e **monitoramento** de tráfego anômalo
  ([observability](../../24-observability/README.md)).

## Em plataformas de dados (cenários)

| Componente | Postura recomendada |
| --- | --- |
| Banco gerenciado | subnet privada, sem IP público, SG só dos workers, TLS obrigatório |
| Kafka/MSK | privado, TLS+SASL/mTLS, ACLs, acesso de clientes via rede interna/PrivateLink |
| Cluster Spark/EMR/Databricks | subnets privadas, sem SSH público, endpoints para S3 |
| Object storage | **bloquear acesso público**, VPC endpoint + bucket policy restringindo à VPC |
| UIs (Airflow, Spark, Grafana) | atrás de SSO/VPN/Ingress autenticado, nunca expostas abertas |
| Warehouse (SaaS) | allowlist de IPs/PrivateLink, SSO+MFA |
| BI/ferramentas externas | conexão via IP fixo/PrivateLink; contas de serviço de leitura mínima |

## Erros comuns

- Banco/Kafka/Redis com IP público ou SG `0.0.0.0/0`.
- Confiar na "rede interna" (sem autenticação/TLS internos).
- SSH/RDP aberto à internet; chaves compartilhadas.
- Buckets públicos; UIs de Airflow/Spark/Jupyter sem autenticação expostas.
- Tudo na mesma rede/conta (movimento lateral livre); sem NetworkPolicies.
- Sem logs de fluxo/monitoramento; sem restrição de egress.

## Boas práticas

- Recursos de dados em **subnets privadas**; exposição apenas via camadas controladas (LB/WAF/Ingress com
  autenticação).
- Security groups com menor privilégio e referência entre SGs; default-deny também no K8s.
- Endpoints privados para serviços gerenciados; bastion/SSM com MFA e auditoria.
- Segmentação por ambiente/sensibilidade; flow logs e alertas; defina tudo via IaC.

## Relação com outros conceitos

- [Cloud networking](../../19-cloud/05-networking/README.md), [K8s networking](../../21-kubernetes/03-services-networking/README.md),
  [IAM](../02-iam/README.md), [criptografia em trânsito](../03-encryption/README.md),
  [container security](../../20-containers/07-container-security/README.md).

## Exercícios

1. Desenhe a rede de uma plataforma Kafka→Spark→warehouse com subnets públicas/privadas e endpoints.
2. Escreva as regras de SG para um Postgres que só aceite o SG dos workers.
3. Explique zero trust e por que "rede interna" não é fronteira de confiança.
4. Liste 5 componentes de dados comumente expostos por engano e como protegê-los.

## Referências

- NIST SP 800-207 (Zero Trust Architecture); CIS Benchmarks; AWS/GCP/Azure Security Best Practices
  (network).
