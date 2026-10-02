# Conceitos de IaC

> 🟣 Cloud & Infra · Parte de [22 — IaC](../README.md)

## O que é

**Infrastructure as Code** descreve a infraestrutura em **arquivos de código** que uma ferramenta lê e
aplica para criar/alterar recursos. A infra deixa de ser um conjunto de passos manuais (e conhecimento
tribal) e vira um **artefato versionado, revisável e repetível**.

## Problema que resolve

Criar infraestrutura "no clique" gera:

- **Não reprodutibilidade** — ninguém sabe exatamente como o ambiente foi montado; recriar é arriscado.
- **Drift** — ambientes divergem (dev ≠ prod) por ajustes manuais ([drift](../06-drift/README.md)).
- **Erro humano**, falta de auditoria, "snowflake servers".
- **Lentidão** — provisionar ambientes novos leva dias.

## Benefícios

| Benefício | Como |
| --- | --- |
| **Reprodutibilidade** | mesmo código → mesma infra (dev/stg/prod, desastre) — princípio central de DE |
| **Versionamento** | Git: histórico, blame, rollback |
| **Revisão** | mudanças via [PR](../../03-git-software-engineering/03-pull-requests-code-review/README.md), com `plan` revisável |
| **Automação** | [CI/CD](../../23-cicd-dataops/README.md) aplica mudanças com segurança |
| **Documentação viva** | o código **é** a descrição da infra |
| **Recuperação (DR)** | recriar o ambiente do zero ([DR](../../06-databases/09-backup-recovery-dr/README.md)) |
| **Consistência entre ambientes** | mesmos módulos, parâmetros diferentes |

## Declarativo vs imperativo

- **Declarativo** — você descreve o **estado desejado** ("quero um bucket X com versioning"); a ferramenta
  calcula **como** chegar lá (diff entre desejado e atual). **Terraform, CloudFormation, Pulumi
  (híbrido), Bicep, Kubernetes YAML.** Idempotente por natureza.
- **Imperativo** — você descreve os **passos** ("crie, depois configure..."). **Scripts shell/Ansible
  procedural.** Mais flexível, mas mais frágil e propenso a não-idempotência.

Preferimos o declarativo para provisionamento: reexecutar converge ao mesmo estado
([idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).

## Ferramentas

| Ferramenta | Natureza | Notas |
| --- | --- | --- |
| **Terraform / OpenTofu** | declarativo, multi-cloud (HCL) | padrão de mercado; foco deste módulo |
| **Pulumi** | declarativo em linguagens gerais (Python/TS/Go) | IaC com código "de verdade" |
| **AWS CDK / CloudFormation** | AWS; CDK gera CloudFormation | nativo AWS |
| **Bicep / ARM** | Azure | nativo Azure |
| **Ansible** | configuração (procedural/declarativo) | configurar servidores/software |
| **Helm / Kustomize** | Kubernetes | empacotar/parametrizar manifests ([K8s](../../21-kubernetes/README.md)) |
| **Crossplane** | recursos cloud via K8s API | plataforma de controle |

**Provisionamento** (criar recursos: Terraform) vs **gerenciamento de configuração** (configurar o
interior de máquinas: Ansible) são papéis diferentes.

## O que codificar em dados

Buckets/lifecycle, [redes/VPC](../../19-cloud/05-networking/README.md), [IAM/roles](../../19-cloud/06-iam-secrets/README.md),
bancos gerenciados, clusters (K8s/EMR), tópicos Kafka, datasets/schemas do warehouse, orquestrador
(MWAA/Composer), budgets e alertas. Tudo reproduzível por ambiente.

## GitOps (extensão)

O repositório Git é a **fonte da verdade**; um agente (Argo CD/Flux) reconcilia o cluster/infra ao estado
declarado. Mudar infra = PR + merge.

## Princípios

- **Tudo versionado**, nada de mudança manual em produção (ou, se feita, reconciliada no código).
- **Pequenos módulos reutilizáveis** (DRY — [módulos](../04-modules-variables/README.md)).
- **Revisão do plano** antes de aplicar; **testes** (validate, lint, policy-as-code).
- **Segredos fora do código** ([secrets](../05-environments-secrets/README.md)).

## Erros comuns

- Misturar clique no console e IaC (gera [drift](../06-drift/README.md)).
- Um único arquivo/estado gigante para tudo.
- Aplicar sem revisar o plano; sem CI.
- Segredos em texto claro no repositório/estado.
- Over-engineering (abstrações excessivas para infra simples).

## Boas práticas

- IaC desde o início; PR + `plan` + aprovação + `apply` automatizado.
- Módulos pequenos e versionados; ambientes via parâmetros.
- Policy-as-code (OPA/Sentinel/Checkov) e lint (`tflint`, `terraform fmt`).

## Relação com outros conceitos

- [Terraform](../02-terraform-basics/README.md), [state](../03-state/README.md),
  [CI/CD & DataOps](../../23-cicd-dataops/README.md), [cloud](../../19-cloud/README.md),
  [Kubernetes](../../21-kubernetes/README.md).

## Exercícios

1. Liste 5 problemas de criar infra manualmente e como IaC resolve cada um.
2. Diferencie declarativo e imperativo com um exemplo de provisionar um bucket.
3. Escolha ferramenta para: VPC+bucket+IAM; configurar pacotes numa VM; parametrizar um app K8s.
4. Descreva o fluxo GitOps de uma mudança de infra.

## Referências

- Morris, K. *Infrastructure as Code*, 2ª ed.; documentação Terraform/OpenTofu, Pulumi, Argo CD.
