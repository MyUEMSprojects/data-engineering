# 22 — Infrastructure as Code (IaC)

> 🟣 Nível 6 — Cloud & Infra · Pré: [19 — Cloud](../19-cloud/README.md),
> [03 — Git/SWE](../03-git-software-engineering/README.md) · Próximo:
> [23 — CI/CD & DataOps](../23-cicd-dataops/README.md)

**Infrastructure as Code** é gerenciar infraestrutura (redes, buckets, bancos, clusters, IAM) por meio de
**código versionado**, em vez de cliques no console. Traz para a infraestrutura as mesmas práticas de
software: Git, revisão, testes, reprodutibilidade e automação — essencial para plataformas de dados
confiáveis e para os [CI/CD](../23-cicd-dataops/README.md).

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Conceitos de IaC](01-iac-concepts/README.md) | Declarativo vs imperativo, benefícios, ferramentas |
| 02 | [Terraform básico](02-terraform-basics/README.md) | HCL, providers, resources, workflow |
| 03 | [State](03-state/README.md) | O estado e remote state |
| 04 | [Modules, variables e outputs](04-modules-variables/README.md) | Reuso e parametrização |
| 05 | [Ambientes e secrets](05-environments-secrets/README.md) | dev/stg/prod e segredos |
| 06 | [Drift](06-drift/README.md) | Detectar e corrigir divergências |

## Dependências internas

```text
Conceitos ─► Terraform básico ─► State ─► Modules/variables ─► Ambientes/secrets ─► Drift
```

## Checkpoint

- [ ] Explicar IaC declarativa e seus benefícios (reprodutibilidade, revisão, auditoria).
- [ ] Escrever recursos Terraform e rodar `init/plan/apply/destroy`.
- [ ] Explicar o *state*, por que usar *remote state* com *locking*.
- [ ] Criar módulos reutilizáveis e parametrizar com variáveis/outputs.
- [ ] Separar ambientes e tratar segredos sem expô-los.
- [ ] Detectar e corrigir *drift*; integrar IaC ao CI/CD.

## Referências do módulo

- Documentação oficial do Terraform/OpenTofu (developer.hashicorp.com/terraform).
- Brikman, Y. *Terraform: Up & Running*. O'Reilly.
- Morris, K. *Infrastructure as Code*. O'Reilly.
