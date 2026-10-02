# Terraform básico

> 🟣 Cloud & Infra · Parte de [22 — IaC](../README.md)

## O que é

**Terraform** (HashiCorp; fork aberto **OpenTofu**) é a ferramenta de IaC declarativa multi-cloud mais
usada. Você descreve recursos em **HCL** (HashiCorp Configuration Language); o Terraform compara com o
estado atual e aplica as diferenças via **APIs dos provedores**.

> Os exemplos usam sintaxe estável de Terraform; confirme na documentação a versão do provider/Terraform
> que você utiliza, pois recursos/argumentos evoluem (ex.: o provider AWS dividiu configurações do bucket
> S3 em recursos separados).

## Conceitos

| Conceito | Função |
| --- | --- |
| **Provider** | plugin que fala com uma API (aws, google, azurerm, kubernetes, snowflake...) |
| **Resource** | um objeto de infra a gerenciar (`aws_s3_bucket`) |
| **Data source** | **lê** informação existente (não cria) |
| **Variable / output** | entradas e saídas ([módulos](../04-modules-variables/README.md)) |
| **Module** | pacote reutilizável de recursos |
| **State** | registro do que o Terraform gerencia ([state](../03-state/README.md)) |

## Exemplo: bucket de lake com versioning e criptografia

```hcl
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "lake" {
  bucket = "empresa-dados-prod-bronze"
  tags   = { time = "dados", ambiente = "prod" }
}

resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_public_access_block" "lake" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

Referências entre recursos (`aws_s3_bucket.lake.id`) criam **dependências implícitas** — o Terraform monta
o grafo e cria na ordem certa (como um [DAG](../../10-data-pipelines/02-dags-dependencies/README.md)).

## O workflow

```bash
terraform init       # baixa providers/módulos, configura backend
terraform fmt        # formata
terraform validate   # valida sintaxe/consistência
terraform plan       # MOSTRA o que mudaria (diff) — REVISE
terraform apply      # aplica (pede confirmação)
terraform destroy    # destrói o que foi gerenciado
```

- **`plan` é a peça-chave**: mostra `+` criar, `~` alterar, `-` destruir, `-/+` recriar. Revise
  principalmente destruições/recriações (podem apagar dados!).
- Em CI: `plan` no PR (comentado), `apply` após aprovação/merge ([CI/CD](../../23-cicd-dataops/README.md)).
- `-target` e `terraform import` (trazer recurso existente para o state) são de uso excepcional.

## Dependências e ciclo de vida

- **Implícitas** por referência; **explícitas** com `depends_on` quando não há referência direta.
- `lifecycle { prevent_destroy = true }` protege recursos críticos (bancos, buckets);
  `create_before_destroy`, `ignore_changes` para casos específicos.
- `count` / `for_each` criam múltiplas instâncias a partir de listas/mapas (DRY).

```hcl
resource "aws_s3_bucket" "camadas" {
  for_each = toset(["bronze", "silver", "gold"])
  bucket   = "empresa-dados-prod-${each.key}"
}
```

## Data sources

```hcl
data "aws_caller_identity" "atual" {}        # lê conta atual
data "aws_vpc" "principal" { tags = { Name = "dados" } }
```

## Cuidados com dados

- **Nunca** deixe o Terraform destruir/recriar recursos com dados sem perceber (banco, bucket) — leia o
  `plan`, use `prevent_destroy`, versioning e backups.
- Alterar certos atributos força **recriação** (replace). O `plan` avisa ("forces replacement").

## Linguagem e ecossistema

HCL é declarativa, com expressões, funções, `locals`, condicionais (`cond ? a : b`). Registry público com
módulos/providers. Ferramentas: `tflint` (lint), `terraform-docs`, **Checkov/tfsec/Trivy** (segurança),
Infracost (custo estimado no PR), Terragrunt (DRY de configs).

## Erros comuns

- Aplicar sem ler o `plan`.
- Recursos com dados sem `prevent_destroy`/backup.
- Versões de provider sem *pin* (comportamento muda).
- Misturar mudanças manuais no console (drift — [drift](../06-drift/README.md)).
- Um único `main.tf` gigante.

## Boas práticas

- Pin de versões (`required_version`, `required_providers`); `fmt/validate/plan` no CI.
- Revisão do `plan` por PR; proteção para recursos críticos; tags padronizadas.
- Estrutura em módulos e arquivos organizados (`main.tf`, `variables.tf`, `outputs.tf`).

## Relação com outros conceitos

- [Conceitos de IaC](../01-iac-concepts/README.md), [state](../03-state/README.md),
  [módulos](../04-modules-variables/README.md), [cloud](../../19-cloud/README.md),
  [CI/CD](../../23-cicd-dataops/README.md); usado no [Projeto 09](../../projects/09-cloud/README.md).

## Exercícios

1. Escreva um Terraform que cria 3 buckets (bronze/silver/gold) com `for_each`, versioning e bloqueio
   público.
2. Rode `plan` após mudar um atributo que força recriação e interprete a saída.
3. Proteja um recurso crítico com `prevent_destroy` e tente destruí-lo.
4. Explique dependência implícita vs `depends_on`.

## Referências

- Documentação do Terraform (language, CLI) e do provider AWS/Google/AzureRM; OpenTofu.
