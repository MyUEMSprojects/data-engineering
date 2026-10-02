# 19 — Cloud

> 🟣 Nível 6 — Cloud & Infra · Pré: [13 — Warehouse](../13-data-warehouse/README.md),
> [14 — Lake](../14-data-lake/README.md) · Próximo: [20 — Containers](../20-containers/README.md)

Quase toda plataforma de dados moderna roda na nuvem. Este módulo cobre **primeiro os conceitos**
(independentes de provedor) e **depois** AWS, GCP e Azure, mostrando os **equivalentes conceituais** —
porque os serviços mudam de nome, mas os problemas e padrões são os mesmos.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Modelos de serviço](01-service-models/README.md) | IaaS, PaaS, SaaS, serverless |
| 02 | [Object storage](02-object-storage/README.md) | S3/GCS/Blob na prática |
| 03 | [Compute](03-compute/README.md) | VMs, containers, serverless, clusters |
| 04 | [Databases gerenciados](04-managed-databases/README.md) | RDS, Cloud SQL, warehouses |
| 05 | [Networking](05-networking/README.md) | VPC, sub-redes, segurança de rede |
| 06 | [IAM e secrets](06-iam-secrets/README.md) | Identidade, permissões, segredos |
| 07 | [Monitoring e autoscaling](07-monitoring-autoscaling/README.md) | Observar e escalar |
| 08 | [Cost management](08-cost-management/README.md) | FinOps para dados |
| 09 | [AWS](09-aws/README.md) | Serviços de dados da AWS |
| 10 | [GCP](10-gcp/README.md) | Serviços de dados do Google Cloud |
| 11 | [Azure](11-azure/README.md) | Serviços de dados da Azure |

## Dependências internas

```text
Modelos de serviço ─► Object storage · Compute · Databases · Networking
                              │
                   IAM/secrets ─► Monitoring/autoscaling ─► Cost management
                              │
                      AWS ⇄ GCP ⇄ Azure (equivalências)
```

## Checkpoint

- [ ] Diferenciar IaaS/PaaS/SaaS/serverless e a responsabilidade compartilhada.
- [ ] Explicar object storage, classes de armazenamento e custos (egress/requests).
- [ ] Escolher compute (VM, container, serverless) para uma carga de dados.
- [ ] Explicar VPC, sub-redes públicas/privadas e controle de acesso de rede.
- [ ] Aplicar IAM com menor privilégio e gerenciar segredos.
- [ ] Monitorar, escalar e controlar custo.
- [ ] Mapear serviços equivalentes entre AWS, GCP e Azure.

## Referências do módulo

- Documentação oficial: AWS, Google Cloud, Azure (Well-Architected Frameworks).
- Reis & Housley, *Fundamentals of Data Engineering* — cloud e storage.
