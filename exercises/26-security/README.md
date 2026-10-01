# Exercícios — Módulo 26: Segurança

Teoria em [26-security](../../26-security/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — AuthN × AuthZ

Diferencie autenticação e autorização com um exemplo de dados.

<details><summary>Gabarito</summary>

**Autenticação:** provar quem você é (SSO, chave). **Autorização:** o que você pode fazer (papel pode `SELECT` em `gold.*` mas não em `raw.pii`). Ver [authn/authz](../../26-security/01-authn-authz/README.md).
</details>

## 2. 🟢 Debugging — Segredo no Git

Um `.env` com a senha do banco foi commitado e enviado. Liste a **sequência correta** de ações.

<details><summary>Gabarito</summary>

1) **Revogar/rotacionar** a credencial **agora**; 2) verificar uso indevido (logs); 3) remover do repositório e, se necessário, limpar o histórico (`git filter-repo`) — sabendo que cópias podem existir; 4) adicionar `.env` ao `.gitignore` e *secret scanning* no CI; 5) migrar para cofre/variáveis de ambiente. Reescrever histórico **não** invalida o segredo vazado. Ver [segredos](../../26-security/04-secrets-management/README.md).
</details>

## 3. 🔵 Implementação — Política IAM de menor privilégio

Escreva uma política que permita a um job **ler** `s3://raw/incoming/*` e **escrever** `s3://curated/curated/*`, e nada mais. Aponte o que **não** colocar.

<details><summary>Gabarito</summary>

```json
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":"s3:GetObject","Resource":"arn:aws:s3:::raw/incoming/*"},
 {"Effect":"Allow","Action":"s3:PutObject","Resource":"arn:aws:s3:::curated/curated/*"}]}
```
Não use `Action: "*"`, `Resource: "*"`, nem `s3:*`. Teste com o simulador do [Projeto 09](../../projects/09-cloud/src/policylint/iam_sim.py). Ver [menor privilégio](../../26-security/06-least-privilege/README.md).
</details>

## 4. 🔵 Implementação — Mascarar PII

Escreva SQL que expõe a analistas `email` mascarado (`a***@dominio.com`) e `cpf` apenas com os 3 últimos dígitos; e cite uma alternativa mais forte que mascarar.

<details><summary>Gabarito</summary>

```sql
CREATE VIEW analytics.customers_safe AS
SELECT customer_id,
       regexp_replace(email, '^(.).*(@.*)$', '\1***\2') AS email_masked,
       '***.***.***-' || right(cpf, 2)                   AS cpf_masked,
       country
FROM raw.customers;
```
(Ajuste a máscara à regra da empresa.) Mais forte: **tokenização/pseudonimização** com chave em cofre (reversível só por quem precisa), ou **mascaramento dinâmico** por papel no warehouse. Ver [mascaramento de PII](../../26-security/07-data-masking-pii/README.md).
</details>

## 5. 🟣 Arquitetura — Criptografia em três lugares

Descreva a criptografia **em trânsito**, **em repouso** e o papel do **KMS**, e o que muda com chaves gerenciadas pelo cliente (CMK).

<details><summary>Gabarito</summary>

Em trânsito: **TLS** (negar tráfego sem TLS por política de bucket). Em repouso: SSE no storage/banco. **KMS** guarda chaves mestras e emite *data keys* (criptografia de envelope), com **rotação**, auditoria e controle de acesso via IAM. **CMK:** você controla a política e a revogação (revogar a chave = dado ilegível), ao custo de mais responsabilidade e custo por chamada (use *bucket keys*). Ver [criptografia](../../26-security/03-encryption/README.md).
</details>

## 6. 🟣 Arquitetura — Modelo de ameaças

Para um bucket que recebe arquivos de **parceiros externos**, liste três ameaças e a mitigação de cada.

<details><summary>Gabarito (um caminho)</summary>

(1) **Arquivo malicioso/gigante** (DoS, *zip bomb*) → limites de tamanho, validação de formato, processamento isolado. (2) **Credenciais do parceiro vazadas** → permissão apenas de escrita no prefixo dele, rotação, URLs pré-assinadas de curta duração. (3) **Injeção de fórmula em CSV / dados maliciosos** → sanitizar na ingestão e quarentena. Plus: monitoramento de volume anômalo. Ver [segurança de rede](../../26-security/05-network-security/README.md).
</details>
