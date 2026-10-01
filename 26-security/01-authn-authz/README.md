# Autenticação e autorização

> 🟣 Production · Parte de [26 — Security](../README.md)

## O que é

- **Autenticação (AuthN)** — provar **quem você é** (identidade): senha, token, certificado, biometria.
- **Autorização (AuthZ)** — decidir **o que você pode fazer** depois de autenticado: ler tabela X, escrever
  no bucket Y.
- **Contabilização/auditoria (Accounting)** — registrar **o que foi feito** ([auditoria](../../25-data-governance/06-retention-auditing/README.md)).

> "Autenticado" ≠ "autorizado": saber quem é não diz o que pode acessar. Confundir os dois é a origem de
> muitas falhas de segurança.

## Autenticação

### Fatores

- **Algo que você sabe** (senha/PIN), **que você tem** (token, chave, celular), **que você é**
  (biometria). **MFA** combina ≥ 2 fatores — reduz drasticamente o risco de credenciais roubadas.

### Para humanos
- **SSO** (Single Sign-On) via IdP corporativo (Entra ID, Okta, Google Workspace) com **SAML/OIDC**; **MFA**
  obrigatório; sem contas compartilhadas; ciclo de vida atrelado ao RH (desligou, perdeu acesso).

### Para máquinas/serviços (workloads)
Pipelines, jobs e serviços também precisam se autenticar:
- **Preferir identidade gerenciada/federada** (roles IAM, Service Accounts, Managed Identities, IRSA/
  Workload Identity, OIDC no CI) → **credenciais temporárias**, sem segredo estático ([IAM](../02-iam/README.md)).
- Quando inevitável (SaaS de terceiros): **tokens/API keys** em [secret manager](../04-secrets-management/README.md),
  com escopo mínimo e **rotação**.
- **mTLS** (certificados mútuos) para serviço↔serviço sensível.

### Protocolos comuns
| Protocolo | Uso |
| --- | --- |
| **OAuth 2.0** | **autorização delegada** (um app acessa recursos em nome do usuário/serviço; tokens de acesso) |
| **OpenID Connect (OIDC)** | camada de **identidade/autenticação** sobre OAuth2 (SSO, federação) |
| **SAML** | SSO corporativo (XML) |
| **Kerberos** | autenticação em redes corporativas/Hadoop |
| **JWT** | formato de token assinado (claims) — valide assinatura/expiração/audiência |
| **API keys** | credencial simples por aplicação (menos segura; trate como senha) |

## Autorização

### Modelos
- **RBAC** — permissões por **papel** (role) atribuídos a usuários/grupos.
- **ABAC** — decisão por **atributos** (usuário, recurso, ambiente, finalidade).
- **ACLs** — listas por recurso (quem pode o quê); difícil de escalar.
- **Políticas baseadas em recurso** (bucket policy) e **em identidade** (IAM policy).
- **Row/column-level security** em dados ([acesso/classificação](../../25-data-governance/05-access-control-classification/README.md)).

### Princípios
- **Menor privilégio** e **negar por padrão** ([least privilege](../06-least-privilege/README.md)).
- **Separação de funções**; **just-in-time access** (acesso temporário elevado com aprovação).
- **Autorizar em cada camada**: API, warehouse, lake, BI, broker (ACLs de Kafka).

## Em plataformas de dados

| Camada | AuthN | AuthZ |
| --- | --- | --- |
| Cloud/APIs | IdP/SSO + roles | IAM policies |
| Warehouse | SSO/OIDC, key-pair para serviços | roles/grants, RLS/CLS |
| Lake | roles/Workload Identity | Lake Formation/Unity Catalog, bucket policies |
| Kafka | SASL/OAuth/mTLS | ACLs por tópico/grupo |
| Orquestrador (Airflow) | SSO | RBAC de DAGs/conexões |
| Banco | senhas rotacionadas/IAM auth | GRANTs por schema/tabela |
| BI | SSO | permissões por dashboard/RLS |

## Boas práticas

- **SSO + MFA** para humanos; **identidade federada** para workloads; sem credenciais estáticas de longa
  duração.
- Tokens de **curta duração** com escopo mínimo; validação completa de JWT (assinatura, `exp`, `aud`, `iss`).
- Autorização **centralizada e por padrão negar**; revisão periódica; logs de acesso.
- Separe identidades por **ambiente e função**; sem contas compartilhadas/genéricas.

## Erros comuns

- Confundir autenticação com autorização.
- Credenciais compartilhadas/estáticas/hardcoded; ausência de MFA.
- Tokens eternos e com escopo amplo; JWT sem validar assinatura/expiração.
- Autorizar só na borda e deixar camadas internas abertas.
- Contas de ex-funcionários ativas; privilégios acumulados.

## Relação com outros conceitos

- [IAM](../02-iam/README.md), [menor privilégio](../06-least-privilege/README.md),
  [secrets](../04-secrets-management/README.md), [acesso/classificação](../../25-data-governance/05-access-control-classification/README.md),
  [auditoria](../../25-data-governance/06-retention-auditing/README.md).

## Exercícios

1. Diferencie AuthN e AuthZ com um exemplo de uma consulta ao warehouse.
2. Explique OAuth2 vs OIDC e quando cada um se aplica.
3. Como um job do Airflow acessa um bucket sem chave estática?
4. Liste verificações obrigatórias ao validar um JWT.

## Referências

- RFC 6749 (OAuth 2.0), OpenID Connect Core, RFC 7519 (JWT); OWASP Authentication/Authorization Cheat Sheets.
