# Networking

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)

## Por que o DE precisa entender

"Não consigo conectar no banco/Kafka/bucket" é uma das falhas mais comuns em pipelines cloud — quase
sempre rede ou permissão. Entender os blocos básicos de rede evita horas de debug e é essencial para
**segurança** (dados não devem ficar expostos à internet).

## Blocos fundamentais

### VPC / VNet (rede virtual privada)

Uma **rede isolada** na nuvem, onde você define faixas de IP (CIDR, ex.: `10.0.0.0/16`) e controla o
tráfego. **VPC** (AWS/GCP), **VNet** (Azure).

### Sub-redes (subnets)

Divisões da VPC, geralmente por **zona de disponibilidade**:

- **Públicas** — têm rota para a internet (via *Internet Gateway*); para balanceadores/bastions.
- **Privadas** — **sem** acesso direto da internet; onde ficam bancos, clusters, workers. Saída para a
  internet (atualizações, APIs) via **NAT Gateway**.

```text
Internet ─► [Load Balancer/Bastion: subnet pública]
                     │
              [Apps, Spark, Kafka, DB: subnets privadas] ─(NAT)─► internet (saída apenas)
```

### Security groups e NACLs (firewalls)

- **Security group** — firewall *stateful* por recurso: quais portas/origens podem acessar (ex.: DB só
  aceita :5432 do SG dos workers). **Menor privilégio**: nunca `0.0.0.0/0` em portas de dados.
- **NACL** — regras *stateless* por sub-rede (camada extra).

### Roteamento e DNS

Tabelas de rota definem para onde o tráfego vai; DNS interno resolve nomes de serviços. Falhas de DNS/
rota são causas frequentes de "timeout".

## Acesso privado a serviços gerenciados

Em vez de trafegar pela internet pública:

- **VPC endpoints / Private Link / Private Service Connect** — acessar S3, BigQuery, etc. de dentro da
  rede privada, sem sair para a internet (mais seguro, evita custo/latência de NAT).
- **Peering / Transit Gateway / VPN / Direct Connect (Interconnect, ExpressRoute)** — conectar VPCs
  entre si ou ao on-premises.

## Padrões comuns em dados

- **Bastion host / túnel** (ver [SSH](../../02-linux-shell-environment/07-ssh/README.md)) ou **IAP/SSM**
  para acessar recursos privados sem expor portas.
- Bancos/Kafka/clusters Spark em subnets privadas; BI acessa via conexão segura/VPN.
- **Egress**: tráfego saindo (inter-região/internet) é cobrado — mantenha compute e dados na mesma
  região/AZ quando possível ([cost](../08-cost-management/README.md)).

## Troubleshooting de conectividade (checklist)

```text
1. Resolução DNS ok?                       (nslookup/dig)
2. Rota existe? (subnet/route table)       
3. Security group libera a porta/origem?   
4. NACL/firewall bloqueando?
5. O serviço está escutando? (ss -tulpn)
6. IAM/permissão (às vezes parece rede, é auth)
```

Ferramentas: `nc -zv host porta`, `curl -v`, `traceroute`; ver
[troubleshooting](../../02-linux-shell-environment/08-logs-and-troubleshooting/README.md).

## Erros comuns

- Banco/Kafka com IP público e `0.0.0.0/0` liberado.
- Workers em subnet pública sem necessidade.
- Esquecer NAT/endpoint → job em subnet privada não alcança a API/bucket.
- Tráfego inter-região/AZ desnecessário (custo e latência).
- Confundir erro de permissão (IAM) com falha de rede.

## Boas práticas

- Recursos de dados em subnets **privadas**; acesso público apenas onde indispensável.
- Security groups com menor privilégio e referências entre SGs (não IPs soltos).
- VPC endpoints para serviços gerenciados; criptografia em trânsito (TLS).
- Defina a rede via [IaC](../../22-infrastructure-as-code/README.md).

## Relação com outros conceitos

- [Segurança de rede](../../26-security/05-network-security/README.md), [IAM](../06-iam-secrets/README.md),
  [databases gerenciados](../04-managed-databases/README.md), [Kubernetes](../../21-kubernetes/README.md).
- [SSH/túneis](../../02-linux-shell-environment/07-ssh/README.md).

## Exercícios

1. Desenhe uma VPC com subnets públicas/privadas para Airflow + Postgres + bucket; marque o fluxo.
2. Escreva as regras de security group para o DB aceitar só dos workers.
3. Explique por que um job em subnet privada falha ao chamar uma API externa e como corrigir.

## Referências

- Documentação de AWS VPC, GCP VPC, Azure VNet; AWS Well-Architected (Security).
