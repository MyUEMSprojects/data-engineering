# Menor privilégio (least privilege)

> 🟣 Production · Parte de [26 — Security](../README.md)

## O que é

O **princípio do menor privilégio** diz que **cada identidade (humana ou de máquina) deve ter somente as
permissões estritamente necessárias para sua função, pelo tempo necessário — e nada além**. É o princípio
de controle de acesso mais importante: limita o dano de erros, contas comprometidas e abusos internos.

## Por que importa

Permissões excessivas transformam qualquer incidente em desastre: uma credencial vazada de um pipeline
com `admin` permite apagar/expor **tudo**; um engano de um analista com escrita em produção pode corromper
dados. Com menor privilégio, o **raio de explosão (blast radius)** de qualquer falha é **pequeno e
conhecido**.

```text
Pipeline X comprometido com role de menor privilégio → acesso só a silver/pedidos (leitura+escrita)
Pipeline X comprometido com role AdministratorAccess → acesso a todos os dados e à conta inteira
```

## Princípios relacionados

- **Need-to-know** — só acessa o dado necessário à função/finalidade.
- **Deny by default** — sem permissão explícita, nega.
- **Separação de funções (SoD)** — quem desenvolve ≠ quem aprova ≠ quem implanta em prod; ninguém controla
  um processo crítico sozinho.
- **Just-in-time (JIT)** — privilégios elevados concedidos **temporariamente**, sob demanda, com aprovação.
- **Privilégios mínimos no tempo, escopo e recurso** — ação específica, recurso específico, prazo limitado.
- **Defesa em profundidade** — menor privilégio em **todas** as camadas (cloud, rede, warehouse, aplicação).

## Como aplicar em plataformas de dados

### 1. Uma identidade por função/pipeline

Evite uma role "poderosa" compartilhada. Cada pipeline/serviço tem sua **service account/role** com
permissões **exatas** (ler `bronze/X`, escrever `silver/X`) ([IAM](../02-iam/README.md)).

### 2. Escopo fino em recursos e ações

- **Ações**: `GetObject` ≠ `*`; separe leitura de escrita e de administração.
- **Recursos**: prefixo/tabela/tópico específico, não `*`.
- **Condições**: tag/domínio, origem de rede, MFA, horário.

### 3. Humanos

- **Acesso de leitura por padrão**; escrita em produção só via pipeline/CI (humano não altera prod à mão).
- **Papéis por função** (analista, engenheiro) em vez de permissões individuais.
- **JIT/break-glass** para elevação, com **aprovação, justificativa, prazo e auditoria**
  ([auditoria](../../25-data-governance/06-retention-auditing/README.md)).
- Ambientes separados: dev **sem** acesso a dados reais de prod.

### 4. Dentro do warehouse/lake

- Grants por **schema/tabela/coluna**, **row-level** e **column-level** security, **mascaramento** de PII
  ([acesso e classificação](../../25-data-governance/05-access-control-classification/README.md),
  [masking](../07-data-masking-pii/README.md)).
- Contas de BI/ferramentas externas com **somente leitura** e escopo restrito.

### 5. Infraestrutura e CI/CD

- Roles de deploy **por ambiente**, com **OIDC** (sem chaves) e **aprovação** para prod ([CI/CD](../../23-cicd-dataops/03-testing-build-deploy/README.md)).
- **IaC** com o plano revisado; contas separadas por ambiente; **guardrails organizacionais** (SCP/Org
  Policy) como teto ([IaC](../../22-infrastructure-as-code/05-environments-secrets/README.md)).
- Containers: não-root, capabilities mínimas ([container security](../../20-containers/07-container-security/README.md)).

## Chegando ao menor privilégio (processo)

1. **Comece estrito** (negar tudo) e conceda o necessário — mais seguro que começar aberto e restringir.
2. Se herdado/amplo, **analise o uso real**: ferramentas de análise de acesso (IAM Access Analyzer/Access
   Advisor, IAM Recommender, logs de auditoria) mostram **permissões não usadas** → remova.
3. **Itere** com logs (CloudTrail) para gerar policies mínimas do uso observado.
4. **Revise periodicamente** (recertificação) e remova acessos ociosos/de ex-integrantes.
5. **Teste** que o job funciona com a role mínima (CI/ambiente de teste).

## Equilíbrio: segurança × produtividade

Menor privilégio **não** significa burocracia insuportável. Torne fácil **pedir e obter** o acesso certo:
**self-service com aprovação e prazo**, roles pré-definidas por função, automação (IaC), acessos
temporários. O objetivo é **acesso mínimo fluido**, não bloqueio.

## Erros comuns

- Roles `admin`/`*:*` "para funcionar" (e nunca reduzidas).
- Uma credencial/role para todos os pipelines e ambientes.
- Humanos com escrita permanente em produção.
- Acúmulo de privilégios (mudou de time e manteve tudo); sem revisão/remoção.
- Esquecer o acesso **dentro** do warehouse (só proteger a nuvem).
- Contas de serviço/BI com acesso total "por conveniência".

## Boas práticas

- Deny by default; uma identidade por função; ações e recursos específicos + condições.
- JIT e break-glass auditados; produção alterada só por pipeline.
- Use análise de acesso para podar permissões; recertificação periódica.
- Guardrails organizacionais; policies como código; ambientes isolados.

## Relação com outros conceitos

- [IAM](../02-iam/README.md), [AuthN/AuthZ](../01-authn-authz/README.md),
  [acesso/classificação](../../25-data-governance/05-access-control-classification/README.md),
  [mascaramento](../07-data-masking-pii/README.md), [rede](../05-network-security/README.md).

## Exercícios

1. Reduza uma role `s3:*` de um pipeline a permissões mínimas, usando o que ele realmente acessa.
2. Descreva um fluxo JIT para um engenheiro acessar dados de prod num incidente, com auditoria.
3. Explique blast radius e como menor privilégio o reduz, com um exemplo de vazamento de credencial.
4. Liste controles de menor privilégio dentro do warehouse para analistas, engenheiros e ferramentas de BI.

## Referências

- NIST SP 800-53 (AC-6); Saltzer & Schroeder, "The Protection of Information in Computer Systems" (1975);
  documentação de IAM Access Analyzer/Recommender.
