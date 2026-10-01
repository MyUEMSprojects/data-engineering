# Criptografia

> 🟣 Production · Parte de [26 — Security](../README.md)

## O que é

**Criptografia** transforma dados em uma forma ilegível sem a **chave** correta, protegendo a
**confidencialidade** (e, com assinaturas/MACs, a **integridade** e autenticidade). Em plataformas de dados,
aplica-se a dados **em repouso**, **em trânsito** e, em casos específicos, **em uso**.

## Conceitos essenciais

### Simétrica vs assimétrica

| | Simétrica | Assimétrica (chave pública/privada) |
| --- | --- | --- |
| Chave | **uma** chave para cifrar e decifrar | par: **pública** cifra/verifica, **privada** decifra/assina |
| Velocidade | rápida (dados em massa) | lenta |
| Uso | **AES-256/GCM** para dados | RSA/ECC para **troca de chaves**, assinaturas, certificados, SSH ([SSH](../../02-linux-shell-environment/07-ssh/README.md)) |

Na prática: **assimétrica troca/protege a chave**, **simétrica cifra os dados** (é o que o TLS faz).

### Hash vs criptografia vs assinatura

- **Hash** (SHA-256) — **unidirecional**, integridade/identificação; **não** é criptografia reversível.
  Para senhas use **hash lento com salt** (bcrypt/scrypt/Argon2), nunca SHA puro.
- **Criptografia** — reversível com a chave.
- **Assinatura digital/HMAC** — prova **integridade e origem**.

> Regra de ouro: **nunca invente criptografia**; use bibliotecas/serviços padrão e algoritmos modernos.

## Em repouso (at rest)

Protege dados armazenados (discos, buckets, bancos, backups, snapshots) contra acesso físico/indevido ao
storage.

- **Gerenciada pelo provedor/serviço**, quase sempre habilitável por padrão: S3 **SSE** (SSE-S3/SSE-KMS),
  GCS (CMEK), EBS/RDS/Snowflake/BigQuery/Redshift criptografados.
- **Chaves gerenciadas pelo cliente (CMK/CMEK)** via **KMS** dão **controle** (quem usa, rotação, auditoria,
  revogação) — recomendado para dados sensíveis/regulados.
- **Criptografia de campo/coluna** (application-level): cifrar valores específicos (CPF, cartão) antes de
  gravar; protege até de admins do banco — mais complexa (busca/ordenar exigem técnicas como criptografia
  determinística/tokenização).
- **Backups e snapshots** também cifrados (e com chaves protegidas).

## Em trânsito (in transit)

Protege dados trafegando pela rede (interceptação/MITM).

- **TLS 1.2+/1.3** em tudo: HTTPS, conexões de banco (`sslmode=verify-full`), Kafka (TLS/SASL_SSL), JDBC,
  Spark, entre serviços.
- **Valide certificados** (cadeia, hostname) — desabilitar a verificação (`verify=False`) anula a proteção.
- **mTLS** para autenticação mútua entre serviços; **VPN/Private Link** para redes privadas
  ([rede](../05-network-security/README.md)); **SSH** para acesso/túneis.
- Dentro do cluster/VPC também: não confie na "rede interna" (zero trust).

## Em uso (in use)

Dados protegidos **durante o processamento** (memória): **confidential computing** (enclaves/TEEs),
**criptografia homomórfica** (nicho). Relevante em cenários de alto risco/multi-parte.

## Gerenciamento de chaves (KMS) e envelope encryption

```text
Dados ──cifrados com──► DEK (Data Encryption Key, simétrica, por objeto/dataset)
DEK ──cifrada com──► KEK/CMK (chave mestra no KMS/HSM)   ← guarda só a DEK cifrada junto ao dado
```

- **KMS/Cloud KMS/Key Vault** (HSM) guarda a **chave mestra**; **nunca** sai em claro. Apps pedem ao KMS
  para cifrar/decifrar DEKs.
- **Vantagens**: rotação barata (re-cifrar só as DEKs), **controle de acesso e auditoria** por chave,
  **revogação** (desabilitar a chave torna os dados ilegíveis).
- **Rotação** periódica; **separação de funções** (quem administra chaves ≠ quem acessa dados); chaves por
  ambiente/domínio/tenant.
- **Crypto-shredding**: apagar a chave de um titular/dataset torna os dados irrecuperáveis — técnica para
  **exclusão** em backups/imutáveis ([retenção](../../25-data-governance/06-retention-auditing/README.md),
  [LGPD](../08-lgpd/README.md)).

## O que a criptografia NÃO resolve

- **Não substitui controle de acesso**: com permissão de uso da chave + acesso ao dado, quem tem acesso lê
  em claro. Combine com [IAM](../02-iam/README.md)/[menor privilégio](../06-least-privilege/README.md).
- Dados **descriptografados na aplicação** podem vazar por logs, extratos, notebooks, BI.
- Não protege contra **credenciais comprometidas** com permissões legítimas.
- **Metadados** (nomes de tabela/objeto, tamanhos) podem vazar mesmo com conteúdo cifrado.

## Boas práticas para dados

- **Habilite criptografia em repouso por padrão** (buckets, bancos, warehouses, volumes, backups); CMK para
  dados sensíveis.
- **TLS obrigatório** com validação de certificados; bloqueie conexões sem TLS (policy `aws:SecureTransport`).
- **KMS** com rotação, separação de funções e auditoria; envelope encryption.
- Criptografia de **coluna/campo** (ou tokenização) para PII altamente sensível; evite cifrar tudo
  manualmente (complexidade).
- **Segredos/chaves nunca no código**; algoritmos modernos (AES-256-GCM, TLS 1.2+, Ed25519/RSA ≥ 2048,
  Argon2/bcrypt para senhas); evite MD5/SHA1/DES/RC4.
- Inclua criptografia na **IaC** (padrão do módulo de bucket/banco) ([IaC](../../22-infrastructure-as-code/README.md)).

## Erros comuns

- Achar que "criptografia = segurança total" (acesso/chaves/logs importam).
- TLS com verificação desligada; protocolos/ciphers obsoletos.
- Chaves hardcoded/versionadas ou sem rotação/controle.
- Guardar chave junto do dado cifrado em claro.
- Senhas com SHA simples/sem salt; inventar esquema próprio.
- Não cifrar backups/snapshots/exports.

## Relação com outros conceitos

- [IAM](../02-iam/README.md), [secrets](../04-secrets-management/README.md),
  [rede](../05-network-security/README.md), [mascaramento/PII](../07-data-masking-pii/README.md),
  [object storage](../../19-cloud/02-object-storage/README.md), [LGPD](../08-lgpd/README.md).

## Exercícios

1. Explique envelope encryption e por que rotacionar a chave mestra é barato.
2. Liste 4 lugares onde dados precisam de criptografia em repouso numa plataforma e como habilitar.
3. Por que `verify=False` em TLS é perigoso? Dê o que usar no lugar.
4. Descreva crypto-shredding como técnica de exclusão e seus pré-requisitos.

## Referências

- OWASP Cryptographic Storage / Transport Layer Security Cheat Sheets; NIST SP 800-57 (gestão de chaves).
- Documentação de AWS KMS, Cloud KMS, Azure Key Vault; Ferguson, Schneier, Kohno, *Cryptography Engineering*.
