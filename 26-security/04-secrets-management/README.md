# Gestão de secrets e credenciais

> 🟣 Production · Parte de [26 — Security](../README.md)

> Aplicação em cloud/K8s/IaC em [IAM e secrets](../../19-cloud/06-iam-secrets/README.md),
> [K8s Secrets](../../21-kubernetes/05-configmaps-secrets/README.md) e
> [IaC secrets](../../22-infrastructure-as-code/05-environments-secrets/README.md). Aqui: princípios.

## O que são

**Secrets** são credenciais e materiais sensíveis que dão acesso a sistemas: senhas de banco, **API keys/
tokens**, chaves privadas/SSH, certificados, chaves de criptografia, strings de conexão. **Gestão de
secrets** é como **armazená-los, distribuí-los, rotacioná-los e auditá-los** sem expô-los.

## Por que é crítico em dados

Pipelines precisam acessar muitos sistemas (bancos, warehouse, APIs, brokers, buckets) → **muitas
credenciais**. Vazamentos de secrets (em Git, logs, imagens) estão entre as **causas mais comuns de
incidentes**, e um único token de produção comprometido pode expor toda a base de dados.

## Hierarquia de preferência (do melhor ao pior)

1. **Não ter secret** — usar **identidade/credenciais temporárias** (roles IAM, Workload Identity, Managed
   Identity, IAM database auth, OIDC federado) ([IAM](../02-iam/README.md)).
2. **Secret manager** com acesso por identidade, **rotação automática** e auditoria.
3. **Secrets injetados em runtime** (variáveis/arquivos montados) a partir do secret manager.
4. ❌ **Nunca**: hardcoded no código, `.env`/tfvars commitados, na imagem Docker, em logs, em chat/wiki.

## Secret managers

**AWS Secrets Manager / SSM Parameter Store**, **GCP Secret Manager**, **Azure Key Vault**, **HashiCorp
Vault** (inclusive *dynamic secrets*), **Kubernetes Secrets** (+ External Secrets Operator / Secrets Store
CSI). Oferecem: criptografia (KMS), **controle de acesso por IAM**, **versionamento**, **rotação**, **auditoria
de acesso**.

```python
# busca em runtime — a identidade do job autoriza (sem chave no código)
import boto3, json
cred = json.loads(boto3.client("secretsmanager").get_secret_value(SecretId="prod/dw/postgres")["SecretString"])
```

### Dynamic secrets (Vault e similares)
Em vez de uma senha fixa, o sistema **gera credenciais efêmeras sob demanda** (usuário de banco com TTL de
1h) e as **revoga** — reduz a janela de exposição e elimina rotação manual.

## Ciclo de vida

- **Criação** com escopo mínimo (somente o necessário).
- **Distribuição** segura (runtime, nunca por e-mail/chat).
- **Rotação** regular (e imediata após suspeita); automatize para evitar "ninguém mexe porque quebra".
- **Revogação** rápida; **expiração** (TTL).
- **Auditoria** de quem leu qual secret e quando.
- **Descarte** de secrets obsoletos.

## Prevenção e detecção de vazamento

- `.gitignore` para `.env`, `*.pem`, `*.tfvars`, credenciais ([.gitignore](../../.gitignore)).
- **pre-commit** com `detect-private-key`/`gitleaks`/`detect-secrets` ([lint](../../03-git-software-engineering/06-linting-formatting/README.md)).
- **Secret scanning** no repositório e no CI (GitHub secret scanning/push protection, TruffleHog, gitleaks).
- **Não logar** secrets/tokens/strings de conexão com senha ([logging](../../24-observability/01-logging/README.md)).
- **Imagens**: sem secrets; `--mount=type=secret` no build ([container security](../../20-containers/07-container-security/README.md)).
- Mascarar em UIs/outputs (`sensitive`).

### Se um secret vazou
1. **Revogue/rotacione imediatamente** (apagar do histórico do Git **não basta** — considere comprometido).
2. **Investigue o uso** (logs de auditoria) por acessos indevidos.
3. Remova do histórico (BFG/`git filter-repo`) como higiene, e **corrija a causa** (pre-commit, scanning).
4. Siga o processo de [incident response](../../24-observability/07-incident-response/README.md).

## Específico: plataformas de dados

| Onde | Prática |
| --- | --- |
| **Airflow** | *Secrets backend* (Secrets Manager/Vault) para Connections/Variables; nada em texto no metadata DB |
| **Spark/Databricks** | secret scopes/integração com Key Vault/Secrets Manager |
| **dbt** | variáveis de ambiente/`env_var()` no `profiles.yml`; credenciais por ambiente |
| **Kubernetes** | External Secrets/CSI; criptografia at-rest do etcd; RBAC mínimo |
| **CI/CD** | secrets do CI por ambiente + **OIDC** em vez de chaves estáticas |
| **Kafka/Connect** | config providers (ex.: `${secret:...}`) |
| **Terraform** | segredos fora do código; state protegido ([state](../../22-infrastructure-as-code/03-state/README.md)) |

## Erros comuns

- Secrets no Git (inclusive no histórico), imagens, logs, notebooks.
- Credenciais compartilhadas entre ambientes/serviços/pessoas.
- Sem rotação (secrets "eternos"); sem inventário de onde cada um é usado.
- Achar que Secret do Kubernetes é criptografado (é base64 por padrão).
- Permissões amplas de leitura de secrets.
- Responder a vazamento só "apagando o commit".

## Boas práticas

- Prefira identidade/credenciais temporárias; senão, secret manager + rotação + auditoria.
- Menor privilégio por secret; ambientes separados; sem secrets em código/imagem/logs.
- Scanning no pre-commit/CI/repositório; runbook de vazamento (revogar → investigar → corrigir).
- Inventário e dono para cada secret; expirar/descartar o obsoleto.

## Relação com outros conceitos

- [IAM](../02-iam/README.md), [criptografia/KMS](../03-encryption/README.md),
  [19 — IAM/secrets](../../19-cloud/06-iam-secrets/README.md),
  [K8s secrets](../../21-kubernetes/05-configmaps-secrets/README.md),
  [IaC secrets](../../22-infrastructure-as-code/05-environments-secrets/README.md).

## Exercícios

1. Liste 5 lugares onde secrets costumam vazar e uma prevenção para cada.
2. Descreva o procedimento completo para um token de produção commitado no GitHub.
3. Explique dynamic secrets e a vantagem sobre uma senha fixa rotacionada mensalmente.
4. Configure (conceitualmente) o Airflow para buscar conexões num secrets backend.

## Referências

- OWASP Secrets Management Cheat Sheet; documentação de AWS Secrets Manager, GCP Secret Manager,
  Azure Key Vault, HashiCorp Vault; gitleaks/TruffleHog.
