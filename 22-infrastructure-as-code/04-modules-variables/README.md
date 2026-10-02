# Modules, variables e outputs

> 🟣 Cloud & Infra · Parte de [22 — IaC](../README.md)

## Por que módulos

Repetir o mesmo bloco de recursos (um "lake" com buckets + IAM + lifecycle) em vários ambientes/projetos
viola **DRY**. **Módulos** empacotam um conjunto coeso de recursos num componente **reutilizável e
parametrizável** — como funções/pacotes em código ([organização](../../03-git-software-engineering/07-project-organization/README.md)).

## Variables (entradas)

Parametrizam um módulo/configuração.

```hcl
variable "ambiente" {
  type        = string
  description = "dev | stg | prod"
  validation {
    condition     = contains(["dev", "stg", "prod"], var.ambiente)
    error_message = "ambiente deve ser dev, stg ou prod."
  }
}

variable "camadas" {
  type    = list(string)
  default = ["bronze", "silver", "gold"]
}

variable "retencao_dias" {
  type    = number
  default = 365
}
```

Formas de fornecer valores: `terraform.tfvars`/`*.auto.tfvars`, `-var-file=prod.tfvars`, `-var`, variáveis
de ambiente `TF_VAR_nome`. **Segredos** não vão em tfvars versionados ([secrets](../05-environments-secrets/README.md)).

Tipos: `string`, `number`, `bool`, `list`, `map`, `object({...})`, `set`. Use `validation` e `description`.

## Outputs (saídas)

Expõem valores de um módulo/stack (IDs, ARNs, endpoints) para outros módulos ou para uso externo.

```hcl
output "bucket_arns" {
  value       = { for k, b in aws_s3_bucket.camadas : k => b.arn }
  description = "ARNs dos buckets por camada"
}
```

`sensitive = true` oculta no CLI (mas continua no [state](../03-state/README.md)).

## Locals

Valores calculados reutilizáveis dentro do módulo (nomes, tags):

```hcl
locals {
  prefixo = "empresa-dados-${var.ambiente}"
  tags    = { time = "dados", ambiente = var.ambiente, gerenciado_por = "terraform" }
}
```

## Criando um módulo

```text
modules/lake/
├── main.tf        # recursos
├── variables.tf   # entradas
├── outputs.tf     # saídas
└── README.md      # documentação (terraform-docs)
```

```hcl
# modules/lake/main.tf
resource "aws_s3_bucket" "camada" {
  for_each = toset(var.camadas)
  bucket   = "${var.prefixo}-${each.key}"
  tags     = var.tags
}
# + versioning, public access block, lifecycle por camada...
```

## Usando um módulo

```hcl
module "lake" {
  source   = "./modules/lake"          # local; ou git::https://...?ref=v1.2.0 ; ou registry
  prefixo  = local.prefixo
  camadas  = ["bronze", "silver", "gold"]
  tags     = local.tags
}

output "lake_buckets" { value = module.lake.bucket_arns }
```

### Fontes de módulos

- **Local** (`./modules/x`), **Git** com tag (`?ref=v1.2.0`), **Terraform Registry** (módulos da
  comunidade/oficiais, ex.: `terraform-aws-modules/vpc/aws`).
- **Versione** módulos (SemVer — [versionamento](../../03-git-software-engineering/04-conventional-commits-versioning/README.md))
  e fixe a versão no consumo; mudança incompatível = major.

## Composição e boas práticas de design

- **Módulos pequenos e focados** (uma responsabilidade); componha-os (rede, lake, plataforma, IAM).
- **Interface clara**: poucas variáveis obrigatórias, defaults sensatos, `validation`, outputs úteis.
- **Sem lógica de ambiente dentro do módulo** — o ambiente é parâmetro (mesmo módulo em dev e prod).
- Evite over-abstração: um módulo que apenas embrulha um recurso sem agregar valor só adiciona
  indireção (KISS).
- Documente (`terraform-docs`) e teste (`terraform validate`, exemplos, Terratest/`terraform test`).

## Em dados: módulos úteis

`lake` (buckets+lifecycle+criptografia), `warehouse-dataset` (datasets/schemas+IAM), `kafka-topics`,
`airflow-platform`, `iam-data-role` (roles de menor privilégio), `monitoring-budget` (alertas/orçamento).

## Erros comuns

- Copiar/colar blocos entre ambientes em vez de módulo.
- Módulo sem versionamento (mudança quebra consumidores).
- Variáveis demais/sem validação; outputs expondo segredos.
- Módulos monolíticos "faz tudo".
- Lógica de ambiente hardcoded no módulo.

## Boas práticas

- Módulos coesos, versionados, documentados, com interface enxuta e validada.
- Ambiente por parâmetros; tags padronizadas via `locals`.
- Pin da versão do módulo no consumo.

## Relação com outros conceitos

- [Terraform básico](../02-terraform-basics/README.md), [ambientes/secrets](../05-environments-secrets/README.md),
  [state](../03-state/README.md); DRY em [organização de projetos](../../03-git-software-engineering/07-project-organization/README.md).

## Exercícios

1. Extraia um módulo `lake` (buckets por camada + versioning + bloqueio público) com variáveis validadas.
2. Use o módulo em dev e prod com `tfvars` diferentes.
3. Versione o módulo via tag Git e consuma com `?ref=`.
4. Explique por que a lógica de ambiente deve ficar fora do módulo.

## Referências

- Terraform Docs — Modules, Input Variables, Outputs, Locals; Terraform Registry; `terraform-docs`.
