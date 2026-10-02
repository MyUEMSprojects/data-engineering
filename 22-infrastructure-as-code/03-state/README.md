# State

> 🟣 Cloud & Infra · Parte de [22 — IaC](../README.md)

## O que é

O **state** (estado) do Terraform é um arquivo (JSON) que **mapeia** os recursos declarados no código aos
**recursos reais** existentes na nuvem, com seus atributos. É como o Terraform sabe **o que já gerencia**
e calcula o diff do `plan` (desejado × estado × realidade).

```text
código (.tf)  ──┐
                ├─► plan = diff ─► apply ─► atualiza state e infraestrutura real
state (.tfstate)┘
```

## Por que importa (e por que é delicado)

- Sem state, o Terraform não saberia que o bucket `X` já existe — tentaria recriá-lo.
- O state contém **identificadores e atributos** dos recursos — **inclusive valores sensíveis** (senhas
  geradas, chaves) em texto claro. **Trate o state como segredo.**
- Perder/corromper o state = perder o vínculo com a infra (recursos "órfãos").

## Local vs remote state

### Local (padrão)

`terraform.tfstate` no disco. **Inadequado para times**: sem compartilhamento, sem lock, risco de perda,
fácil de vazar (**nunca** commite — ver [.gitignore](../../.gitignore)).

### Remote state (o correto em equipe)

Armazene o state num **backend remoto** compartilhado, durável e com **locking**:

| Backend | Observações |
| --- | --- |
| **S3 + DynamoDB (lock)** / S3 com lock nativo (versões recentes) | clássico na AWS |
| **GCS** | locking embutido |
| **Azure Blob** | locking por lease |
| **Terraform Cloud / HCP / Spacelift / Terraform Enterprise** | gerenciado, com runs/RBAC |

```hcl
terraform {
  backend "s3" {
    bucket         = "empresa-tfstate"
    key            = "dados/prod/lake.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "tfstate-lock"     # locking (consulte a doc da sua versão)
  }
}
```

### Benefícios do remote state

- **Colaboração** — todos usam a mesma fonte da verdade.
- **Locking** — impede dois `apply` simultâneos corromperem o state.
- **Durabilidade e versionamento** — habilite **versioning** do bucket para recuperar versões antigas.
- **Criptografia e controle de acesso** — IAM restrito (quem lê o state vê segredos).
- **Compartilhamento entre stacks** via `terraform_remote_state` (ou, melhor, outputs publicados/data
  sources) — com cautela de acoplamento.

## Estrutura de states (blast radius)

Dividir a infra em **vários states pequenos** (por camada/componente/ambiente) reduz o "raio de
explosão" e acelera `plan`:

```text
states/
├── rede/prod         (VPC, subnets)
├── dados-lake/prod   (buckets, catálogo)
├── dados-plataforma/prod (Airflow, Kafka)
└── dados-lake/dev
```

Um único state gigante: `plan` lento, risco alto, conflitos de lock constantes.

## Operações de state

```bash
terraform state list                       # recursos no state
terraform state show aws_s3_bucket.lake
terraform state mv A B                     # renomear/mover sem recriar (refactor)
terraform state rm aws_s3_bucket.lake      # tirar do state (sem destruir o recurso)
terraform import aws_s3_bucket.lake nome   # trazer recurso existente para o state
terraform force-unlock <ID>                # liberar lock preso (cuidado)
```

Use `moved {}` blocks (declarativo) para refatorar nomes com segurança em vez de `state mv` manual quando
possível.

## Segurança do state

- Backend **criptografado**, **acesso mínimo** (IAM), logs de acesso.
- **Evite** colocar segredos como valores de recurso quando possível (use secret managers/identidade —
  [secrets](../05-environments-secrets/README.md)); marque `sensitive = true` nas variáveis/outputs (ajuda a
  ocultar em logs, mas **não** remove do state).
- Nunca commitar `*.tfstate` (inclusive backups `.tfstate.backup`).

## Problemas comuns

- **State desatualizado/drift** — a realidade mudou fora do Terraform ([drift](../06-drift/README.md));
  `terraform plan -refresh-only` mostra.
- **Lock preso** após falha de CI.
- **State perdido/corrompido** — restaure da versão anterior do bucket.
- **Recurso apagado manualmente** — o `plan` propõe recriar.

## Erros comuns

- State local em projeto de equipe / commitado no Git.
- Backend sem locking → corrupção por `apply` concorrente.
- State sem versioning/backup.
- Acesso amplo ao bucket do state (vaza segredos).
- State monolítico para toda a empresa.

## Boas práticas

- Remote state criptografado, versionado, com locking e IAM mínimo.
- States pequenos por componente/ambiente; `moved` blocks para refactors.
- Pipeline único aplica mudanças (ninguém aplica da máquina local em prod).

## Relação com outros conceitos

- [Terraform básico](../02-terraform-basics/README.md), [drift](../06-drift/README.md),
  [ambientes/secrets](../05-environments-secrets/README.md), [IAM](../../19-cloud/06-iam-secrets/README.md).
- Locking ⇄ [concorrência](../../06-databases/08-concurrency-consistency/README.md).

## Exercícios

1. Configure um backend remoto (S3 ou GCS) com versioning e locking e migre um state local.
2. Explique por que o state é sensível e como protegê-lo.
3. Divida uma infra em 3 states e justifique o raio de explosão menor.
4. Use `import` para trazer um bucket existente ao Terraform.

## Referências

- Terraform Docs — State, Backends, Remote State, `moved` blocks.
- Brikman, Y. *Terraform: Up & Running* — gerenciamento de state.
