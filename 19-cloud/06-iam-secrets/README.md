# IAM e secrets

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)
>
> Visão cloud prática. Fundamentos conceituais em [26 — Security](../../26-security/README.md)
> ([IAM](../../26-security/02-iam/README.md), [secrets](../../26-security/04-secrets-management/README.md)).

## IAM (Identity and Access Management)

IAM define **quem** (identidade) pode fazer **o quê** (ações) em **quais recursos**, sob quais condições.
Em cloud, toda chamada de API passa por IAM — é a camada de segurança mais importante.

### Conceitos

| Conceito | Significado |
| --- | --- |
| **Principal/identidade** | usuário, grupo, **role/service account** (identidade de máquina/serviço) |
| **Policy** | documento de permissões (Allow/Deny de ações em recursos) |
| **Role** | conjunto de permissões **assumível** (credenciais temporárias) |
| **Resource-based policy** | permissão anexada ao recurso (ex.: bucket policy) |

Equivalentes: AWS IAM (users/roles/policies) · GCP IAM (members/roles/service accounts) · Azure
RBAC + Entra ID (managed identities).

### Princípios

- **Menor privilégio** — conceda só o necessário (`s3:GetObject` num prefixo, não `s3:*` em `*`).
- **Roles/identidade de serviço, não chaves estáticas** — jobs assumem uma role e recebem credenciais
  **temporárias e rotacionadas** (instance profile, IRSA no EKS, Workload Identity no GKE, Managed
  Identity). **Evite access keys de longa duração.**
- **Separação por ambiente/função** (dev/prod; ingestão vs leitura).
- **Federação/SSO** para humanos; MFA obrigatório; sem usuário root no dia a dia.
- **Auditoria** — CloudTrail/Audit Logs para ver quem fez o quê.

### Exemplo de policy (conceitual, AWS)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:ListBucket"],
    "Resource": ["arn:aws:s3:::dados-prod", "arn:aws:s3:::dados-prod/silver/*"]
  }]
}
```

## Secrets (segredos)

Credenciais de banco, tokens de API, chaves — **nunca** em código, Git ou imagens (ver
[.gitignore](../../.gitignore), [pré-commit com detect-private-key](../../03-git-software-engineering/06-linting-formatting/README.md)).

### Secret managers

**AWS Secrets Manager / SSM Parameter Store**, **GCP Secret Manager**, **Azure Key Vault**,
**HashiCorp Vault**. Oferecem: armazenamento criptografado (KMS), **controle de acesso por IAM**,
**rotação automática**, versionamento e auditoria.

```python
# em vez de hardcode: buscar em runtime (a identidade do job autoriza)
import boto3, json
sm = boto3.client("secretsmanager")
cred = json.loads(sm.get_secret_value(SecretId="prod/dw/postgres")["SecretString"])
```

### Boas práticas

- Injete segredos em runtime (env var a partir do secret manager, secret do Kubernetes sincronizado) —
  ver [Kubernetes secrets](../../21-kubernetes/README.md).
- **Rotacione** regularmente; revogue ao suspeitar de vazamento.
- Minimize segredos: prefira **identidade federada/IAM auth** (ex.: IAM database auth) a senhas.
- Segredo vazado em commit = considerado **comprometido** (rotacione, não só apague do histórico).

## KMS (chaves de criptografia)

**KMS/Cloud KMS/Key Vault** gerencia chaves de criptografia (CMK/CMEK) para dados em repouso (buckets,
bancos, discos) e envelope encryption; controle de quem pode usar/gerir cada chave (ver
[encryption](../../26-security/03-encryption/README.md)).

## Erros comuns

- Permissões amplas (`*:*`) "para funcionar".
- Access keys estáticas em código/CI/máquinas de dev.
- Segredos em variáveis commitadas, logs ou imagens Docker.
- Mesma credencial para dev e prod / compartilhada entre serviços.
- Sem rotação nem auditoria.

## Boas práticas (resumo)

- Roles com menor privilégio por job/serviço; credenciais temporárias via identidade federada.
- Secret manager + rotação; KMS para criptografia; auditoria ativada.
- Revisões periódicas de acesso; IaC para versionar políticas ([IaC](../../22-infrastructure-as-code/README.md)).

## Relação com outros conceitos

- [Security](../../26-security/README.md), [LGPD](../../26-security/08-lgpd/README.md),
  [object storage](../02-object-storage/README.md), [networking](../05-networking/README.md).
- [Governança/acesso](../../25-data-governance/README.md).

## Exercícios

1. Escreva uma policy de menor privilégio para um job que lê `silver/` e escreve `gold/` num bucket.
2. Explique por que roles com credenciais temporárias são melhores que access keys.
3. Descreva como um job em Kubernetes obtém uma credencial de banco sem hardcode.
4. O que fazer se um segredo foi commitado no Git?

## Referências

- Documentação de AWS IAM/Secrets Manager/KMS, GCP IAM/Secret Manager, Azure RBAC/Key Vault.
- OWASP Secrets Management Cheat Sheet.
