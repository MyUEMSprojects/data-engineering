# Ambientes e secrets

> 🟣 Cloud & Infra · Parte de [22 — IaC](../README.md)

## Ambientes (dev / staging / prod)

Plataformas de dados precisam de **ambientes isolados** para desenvolver e testar sem afetar produção
(ver [CI/CD & ambientes](../../23-cicd-dataops/README.md)). Com IaC, ambientes são **a mesma infra
parametrizada**.

### Estratégias de organização

| Estratégia | Como | Prós | Contras |
| --- | --- | --- | --- |
| **Diretório/stack por ambiente** | `envs/dev`, `envs/prod` cada um com seu backend/state, chamando os mesmos [módulos](../04-modules-variables/README.md) | isolamento forte, blast radius pequeno, aprovações distintas | alguma repetição (mitigada por módulos/Terragrunt) |
| **Workspaces** | `terraform workspace` (states paralelos no mesmo código) | pouca duplicação | fácil aplicar no ambiente errado; ambientes muito parecidos apenas |
| **Repositórios/contas separados** | conta/projeto cloud por ambiente | **isolamento máximo** (IAM, custo, segurança) | mais overhead |

**Recomendado**: **conta/projeto cloud separado por ambiente** (ou ao menos prod separado) + **stack e
state por ambiente**, reutilizando módulos versionados. Evite workspaces para prod vs dev.

```text
infra/
├── modules/            (lake, platform, iam...)
└── envs/
    ├── dev/   main.tf (module "lake" {... ambiente="dev"})   backend: tfstate-dev
    ├── stg/
    └── prod/  main.tf (module "lake" {... ambiente="prod"})  backend: tfstate-prod
```

### Paridade e diferenças controladas

Mantenha dev/stg **estruturalmente iguais** a prod (mesmos módulos); varie **escala/tamanho/retenção**
(instâncias menores, menos réplicas, retenção curta) por variáveis — reduz "funciona em dev, quebra em
prod" e custo ([cost](../../19-cloud/08-cost-management/README.md)).

### Promoção entre ambientes

Mudança de infra: PR → CI faz `plan` em dev → aplica → valida → promove (mesmo código/versão de módulo)
para stg → prod, com **aprovação manual** em prod ([deployment strategies](../../23-cicd-dataops/06-deployment-strategies/README.md)).

## Secrets em IaC

### O risco

Segredos (senhas de banco, tokens, chaves) podem vazar por: código/tfvars versionados, **state** (texto
claro), logs do CI, outputs. Trate como incidente se vazar (rotacione).

### Princípios

1. **Nunca** commitar segredos (`*.tfvars` com senha, chaves) — [.gitignore](../../.gitignore),
   [pre-commit com detect-private-key](../../03-git-software-engineering/06-linting-formatting/README.md).
2. **Prefira não ter segredo**: use **identidade/roles** (IAM, Workload Identity) em vez de chaves.
3. **Gerencie segredos em um secret manager** ([IAM/secrets](../../19-cloud/06-iam-secrets/README.md)) e
   deixe o recurso **referenciar** o segredo, não conter o valor.
4. **Proteja o state** (criptografado, acesso mínimo — [state](../03-state/README.md)): ele pode conter
   segredos mesmo com `sensitive = true`.

### Padrões práticos

```hcl
# Banco gerenciado: deixe o provedor gerar/guardar a senha no secret manager (quando suportado)
resource "aws_db_instance" "dw" {
  # ...
  manage_master_user_password = true     # senha gerida no Secrets Manager (confira o suporte/versão)
}

# Ler segredo existente em vez de declará-lo
data "aws_secretsmanager_secret_version" "api" { secret_id = "prod/api-token" }
```

- **Variáveis sensíveis** via env var no CI (`TF_VAR_db_password`) a partir do secret store do CI
  (GitHub Actions secrets / OIDC) — nunca em arquivos.
- **`sensitive = true`** em variáveis/outputs: oculta do CLI/logs (não do state).
- **SOPS / Sealed Secrets / Vault** para segredos criptografados versionáveis (GitOps).
- **OIDC federado** do CI à nuvem (sem chaves de longa duração no pipeline).

## Em dados: o que costuma ser segredo

Senhas de banco/warehouse, tokens de APIs de ingestão (Fivetran/Airbyte), chaves de Kafka, credenciais de
serviços SaaS. Para acesso a buckets/warehouse **entre serviços da mesma nuvem**, use roles — sem segredo.

## Erros comuns

- `terraform.tfvars` com senhas no Git.
- State sem criptografia/com acesso amplo (vaza segredos).
- Workspaces para isolar prod (aplicar no ambiente errado).
- Mesmos recursos/conta para dev e prod.
- Chaves de acesso de longa duração no CI.
- Output expondo segredo.

## Boas práticas

- Conta/projeto + state por ambiente; módulos reutilizados; diferenças por variáveis.
- Segredos fora do código; identidade/role em vez de chave; secret manager + rotação; OIDC no CI.
- Aprovação manual e plan revisado para prod; promoção gradual.

## Relação com outros conceitos

- [State](../03-state/README.md), [módulos/variáveis](../04-modules-variables/README.md),
  [IAM/secrets](../../19-cloud/06-iam-secrets/README.md), [CI/CD](../../23-cicd-dataops/README.md),
  [security](../../26-security/04-secrets-management/README.md).

## Exercícios

1. Estruture `envs/dev` e `envs/prod` usando o mesmo módulo com tamanhos diferentes.
2. Explique por que workspaces são arriscados para separar prod de dev.
3. Mostre como evitar uma senha de banco no código/state usando secret manager/role.
4. Configure (conceitualmente) o CI para autenticar na nuvem via OIDC sem chaves estáticas.

## Referências

- Terraform Docs — Sensitive data in state, Workspaces; HashiCorp Vault; SOPS; OIDC no GitHub Actions.
