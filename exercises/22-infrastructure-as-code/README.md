# Exercícios — Módulo 22: Infraestrutura como código

Teoria em [22-infrastructure-as-code](../../22-infrastructure-as-code/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Declarativo × imperativo

Qual a vantagem de descrever o **estado desejado** (Terraform) em vez de scripts que executam passos?

<details><summary>Gabarito</summary>

A ferramenta calcula o **diff** entre o estado desejado e o real e aplica só o necessário — é **idempotente** e auditável por `plan`. Scripts imperativos repetidos podem duplicar/quebrar recursos. Ver [conceitos de IaC](../../22-infrastructure-as-code/01-iac-concepts/README.md).
</details>

## 2. 🟢 Conceitual — Para que serve o `plan`?

Por que `terraform plan` deve ser lido (e comentado no PR) antes do `apply`? O que procurar?

<details><summary>Gabarito</summary>

É a **prévia** das mudanças. Procure `-/+` (destruir e recriar), deleções inesperadas, mudanças em recursos com dados (bancos, buckets) e *drift*. Em CI: `plan` no PR, `apply` com aprovação. Ver [Terraform básico](../../22-infrastructure-as-code/02-terraform-basics/README.md).
</details>

## 3. 🔵 Debugging — O estado local perdido

Um colega apagou `terraform.tfstate` do notebook. O que acontece no próximo `apply` e como evitar?

<details><summary>Gabarito</summary>

O Terraform "esquece" os recursos existentes e tenta **criar de novo** (erros de duplicidade) — ou duplica o que pode. Prevenção: **backend remoto** (S3 + *locking*, ou Terraform Cloud) com versionamento e criptografia; nunca versionar o `tfstate` no Git (contém segredos). Recuperação: `terraform import`. Ver [state](../../22-infrastructure-as-code/03-state/README.md).
</details>

## 4. 🔵 Implementação — Variáveis e validação

Crie uma variável `environment` que só aceita `dev|staging|prod` e use `for_each` para criar dois buckets (`raw`, `curated`).

<details><summary>Gabarito</summary>

```hcl
variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment deve ser dev, staging ou prod."
  }
}
resource "aws_s3_bucket" "lake" {
  for_each = toset(["raw", "curated"])
  bucket   = "orders-${var.environment}-${each.key}"
}
```
Ver o conjunto completo no [Projeto 09](../../projects/09-cloud/infra/variables.tf). Referências: [módulos e variáveis](../../22-infrastructure-as-code/04-modules-variables/README.md).
</details>

## 5. 🟣 Arquitetura — Drift

Alguém alterou um *security group* no console. Como detectar, decidir e prevenir *drift*?

<details><summary>Gabarito</summary>

Detectar: `terraform plan` agendado (CI) que alerta diferenças. Decidir: **a mudança foi legítima?** Se sim, refletir no código; se não, `apply` reverte. Prevenir: acesso ao console **somente leitura** em produção, IAM restrito, auditoria (CloudTrail) e *policy-as-code* (ver `policylint` no [Projeto 09](../../projects/09-cloud/README.md)). Ver [drift](../../22-infrastructure-as-code/06-drift/README.md).
</details>

## 6. 🟣 Implementação — Policy-as-code

Escreva em Python uma regra que, dado o JSON de `terraform show -json`, **reprova** buckets S3 sem criptografia. Mencione a armadilha do **plano × estado**.

<details><summary>Gabarito</summary>

```python
import json, sys

doc = json.load(open(sys.argv[1]))
res = doc["values"]["root_module"]["resources"]          # ESTADO (valores já conhecidos)

def key(address: str) -> str:                              # casa pelo índice do for_each: ...["raw"]
    return address[address.index("["):] if "[" in address else ""

buckets = {key(r["address"]): r["address"] for r in res if r["type"] == "aws_s3_bucket"}
encrypted = {key(r["address"]) for r in res if r["type"] == "aws_s3_bucket_server_side_encryption_configuration"}
missing = [addr for k, addr in buckets.items() if k not in encrypted]
print("violações:", missing)
sys.exit(1 if missing else 0)
```
**Armadilha:** no **plano**, valores computados aparecem como "conhecidos após o apply" e somem do JSON — por isso lint do **estado** ou da *configuração*. Implementação real e testada: [`policylint`](../../projects/09-cloud/src/policylint/lint.py).
</details>
