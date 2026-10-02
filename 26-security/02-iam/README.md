# IAM (Identity and Access Management)

> 🟣 Production · Parte de [26 — Security](../README.md)
>
> Aplicação prática no provedor de nuvem em [19 — IAM e secrets](../../19-cloud/06-iam-secrets/README.md).
> Aqui: o modelo conceitual e as práticas.

## O que é

**IAM** é o conjunto de **processos e tecnologias** para gerenciar **identidades digitais** e **controlar
seu acesso** a recursos. Responde: *quem* (identidade) pode fazer *o quê* (ações) em *quais recursos*, sob
quais *condições*. É a **camada de segurança central** da nuvem e das plataformas de dados — toda chamada
de API passa por ela.

## Componentes

| Conceito | Descrição |
| --- | --- |
| **Identidade/principal** | usuário humano, grupo, **service account/role** (identidade de workload) |
| **Credencial** | como a identidade prova quem é (senha+MFA, token temporário, certificado) |
| **Permissão/ação** | operação permitida (`s3:GetObject`, `bigquery.tables.getData`) |
| **Recurso** | objeto protegido (bucket, tabela, tópico, secret) |
| **Política (policy)** | documento que concede/nega permissões (Allow/Deny, condições) |
| **Role (papel)** | conjunto de permissões **assumível** por identidades (credenciais temporárias) |
| **Condições** | restrições (IP, horário, tag, MFA, finalidade) |

## Tipos de política

- **Baseadas em identidade** — anexadas a usuário/grupo/role ("esta role pode ler `silver/`").
- **Baseadas em recurso** — anexadas ao recurso ("este bucket aceita leitura da role X").
- **Limites e guardrails** — *permission boundaries*, **SCPs/Organization Policies** (teto de permissões
  para toda uma conta/OU) que impedem violações mesmo com admins.
- **Deny explícito vence** Allow na avaliação (em AWS); entenda a lógica de avaliação do seu provedor.

## Identidades de workload (o essencial para dados)

Pipelines/serviços **não devem** usar chaves estáticas. Use **roles com credenciais temporárias**:

- **AWS**: IAM Roles (instance profile, task role, **IRSA** em EKS, OIDC no CI).
- **GCP**: Service Accounts + **Workload Identity**.
- **Azure**: **Managed Identities**.
- **Federação OIDC** para CI/CD e entre nuvens (sem segredos de longa duração) — ver
  [CI/CD](../../23-cicd-dataops/03-testing-build-deploy/README.md).

```text
Job Spark/Airflow ─► assume role "etl-silver-writer" (credenciais temporárias, rotacionadas)
                       └─ Allow: s3:GetObject em bronze/*, s3:PutObject em silver/*
```

## Hierarquia e organização

- **Contas/projetos/subscriptions separadas** por ambiente/domínio (isolamento forte; blast radius
  pequeno) + organização com **guardrails** centrais.
- **Grupos/papéis por função** (`data-engineer`, `analyst-vendas`), não permissões por pessoa.
- **Namespacing por tags/prefixos** para escopar acesso (ex.: acesso só a recursos `domain=vendas`).

## Em warehouses e plataformas de dados

IAM da nuvem ≠ permissões **dentro** do warehouse/lake: combine IAM (quem entra na plataforma) com
**RBAC interno** (grants em schemas/tabelas, RLS/CLS, mascaramento) — [classificação/acesso](../../25-data-governance/05-access-control-classification/README.md).
Catálogos como **Unity Catalog/Lake Formation/Dataplex** centralizam permissões de dados.

## Ciclo de vida e governança de acesso

- **Joiner-Mover-Leaver**: provisionar/alterar/revogar acesso com o ciclo do RH (automatize via IdP/SCIM).
- **Acesso just-in-time** e **break-glass** (emergência) com aprovação, tempo limitado e auditoria.
- **Revisão/recertificação periódica** de acessos; remover permissões **não usadas** (Access Advisor/IAM
  Recommender mostram o que não é usado).
- **Auditoria** de todas as mudanças e usos ([CloudTrail/Audit Logs](../../25-data-governance/06-retention-auditing/README.md)).
- **IaC** para definir roles/policies (revisáveis, versionados — [IaC](../../22-infrastructure-as-code/README.md)).

## Exemplo de policy de menor privilégio (AWS, conceitual)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::dados-prod/bronze/pedidos/*" },
    { "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::dados-prod/silver/pedidos/*" },
    { "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::dados-prod",
      "Condition": { "StringLike": { "s3:prefix": ["bronze/pedidos/*", "silver/pedidos/*"] } } }
  ]
}
```

## Erros comuns

- Wildcards (`*:*`) e roles administrativas "para funcionar".
- Access keys de longa duração em código/CI/laptops.
- Um papel único e poderoso para todos os pipelines (blast radius enorme).
- Sem separação de contas/ambientes; dev com acesso de escrita a prod.
- Permissões acumuladas e nunca revisadas; sem MFA.
- Esquecer o RBAC **dentro** do warehouse/lake (só proteger a borda).

## Boas práticas

- Identidade federada/roles temporárias; **uma role por pipeline/função**, escopo mínimo.
- Contas separadas + guardrails organizacionais (SCP/Org Policy).
- MFA, SSO, automação do ciclo JML, revisão e remoção de permissões ociosas.
- Policies como código; auditoria e alertas de mudanças/uso anômalo.

## Relação com outros conceitos

- [AuthN/AuthZ](../01-authn-authz/README.md), [menor privilégio](../06-least-privilege/README.md),
  [secrets](../04-secrets-management/README.md), [19 — IAM/secrets](../../19-cloud/06-iam-secrets/README.md),
  [IaC](../../22-infrastructure-as-code/README.md).

## Exercícios

1. Escreva uma policy que permita a um job ler `bronze/pedidos` e escrever `silver/pedidos`, nada mais.
2. Explique por que contas separadas por ambiente reduzem o blast radius.
3. Diferencie policy baseada em identidade e em recurso, e o papel de SCPs/Org Policies.
4. Descreva o fluxo de acesso JIT com aprovação e auditoria a dados de produção.

## Referências

- AWS/GCP/Azure IAM Docs e Security Best Practices; NIST SP 800-53 (AC); OWASP Access Control.
