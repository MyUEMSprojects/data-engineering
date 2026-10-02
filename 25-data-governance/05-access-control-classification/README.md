# Controle de acesso e classificação

> 🟣 Production · Parte de [25 — Data Governance](../README.md)
>
> Mecanismos técnicos (IAM, criptografia, mascaramento) em [26 — Security](../../26-security/README.md).
> Aqui: a **política**: classificar dados e decidir **quem acessa o quê**.

## Classificação de dados

Rotular dados por **sensibilidade/impacto** para aplicar o nível certo de proteção (proporcional ao risco).

### Esquema típico

| Nível | Descrição | Exemplos | Controles |
| --- | --- | --- | --- |
| **Público** | sem restrição | dados abertos, marketing | mínimos |
| **Interno** | uso interno da empresa | métricas agregadas, docs internas | acesso a funcionários |
| **Confidencial** | impacto de negócio se vazar | contratos, financeiro detalhado | acesso por necessidade, auditoria |
| **Restrito / sensível** | dados pessoais sensíveis, regulados | **PII**, saúde, cartão, credenciais | mínimo privilégio, mascaramento, criptografia, auditoria rigorosa, retenção |

(Nomes variam por empresa; o importante é **poucos níveis claros** com **controles associados**.)

### Categorias relevantes para dados

- **Dado pessoal** (LGPD): identifica/torna identificável uma pessoa (nome, CPF, e-mail, IP, localização).
- **Dado pessoal sensível** (LGPD art. 5º): origem racial/étnica, saúde, biometria, convicção religiosa/
  política, vida sexual, filiação sindical → proteção reforçada ([LGPD](../../26-security/08-lgpd/README.md)).
- **Dados financeiros/regulados**: PCI-DSS (cartão), regulação bancária.
- **Segredos/credenciais** (tratados à parte — [secrets](../../26-security/04-secrets-management/README.md)).
- **Propriedade intelectual** / confidencial de negócio.

### Como classificar (e automatizar)

- **Por dataset e por coluna** — a sensibilidade vive nas **colunas** (uma tabela mistura públicas e PII).
- **Descoberta automática**: scanners (Macie, DLP API, Purview, OpenMetadata/DataHub classifiers) detectam
  padrões (CPF, e-mail, cartão) por regex/ML.
- **Tags no catálogo/warehouse** (`pii=true`, `sensitivity=restricted`) como **fonte da verdade** que
  aciona políticas ([metadata](../02-metadata-catalog/README.md)).
- **Propagação via lineage** ([lineage](../03-lineage/README.md)): derivados herdam a classificação.
- **Revisão humana** pelo owner/steward para casos ambíguos.

## Controle de acesso

### Modelos

- **RBAC** — acesso por **papel** (analista-vendas, engenharia). Simples, escalável.
- **ABAC** — acesso por **atributos** (departamento, sensibilidade, finalidade, localização). Mais flexível
  e granular.
- **Row-level / column-level security** — filtrar **linhas** (cada gerente vê só sua região) e
  **mascarar/ocultar colunas** conforme o usuário (vendedor vê CPF mascarado; o time de fraude, completo).
- **Acesso por finalidade (purpose-based)** — base legal/finalidade do uso (LGPD).

### Princípios

- **Menor privilégio** e **need-to-know**: só o necessário para a função ([least privilege](../../26-security/06-least-privilege/README.md)).
- **Padrão negar** (deny by default); acesso **concedido explicitamente**, com **justificativa e prazo**.
- **Grupos/papéis, não indivíduos**; revisão periódica (**recertificação** de acessos).
- **Separação de funções** (quem aprova ≠ quem implementa).
- **Acesso a produção/PII é exceção** auditada (break-glass).

### Onde se aplica (técnico)

| Camada | Mecanismo |
| --- | --- |
| Warehouse | grants/roles, **row access policies**, **dynamic data masking**, column-level security (Snowflake, BigQuery policy tags, Redshift) |
| Lake/lakehouse | Lake Formation, Unity Catalog, políticas por tabela/coluna/linha |
| Object storage | IAM/bucket policies, prefixos por sensibilidade ([object storage](../../19-cloud/02-object-storage/README.md)) |
| BI | permissões por dashboard/RLS |
| Kafka/streaming | ACLs por tópico |

### Política baseada em tags (escala)

Em vez de grants por tabela, defina **políticas ligadas a tags de classificação**:

```text
tag pii=true  → mascarar para papel "analista"; texto claro só para "fraude"; negar para "externo"
```

O mascaramento/acesso se aplica automaticamente a qualquer coluna tageada — escala e consistência
([masking](../../26-security/07-data-masking-pii/README.md)).

## Fluxo de pedido de acesso

```text
Solicitação (catálogo) ─► owner/steward aprova (justificativa, finalidade, prazo) ─► concessão automatizada (IaC/IAM) ─► auditoria ─► expira/recertificação
```

Automatize para ser rápido (self-service) mas controlado e auditável ([auditoria](../06-retention-auditing/README.md)).

## Erros comuns

- Classificar só no nível da tabela (PII escondida em colunas).
- Sem classificação → todos os dados tratados igual (ou todos abertos, ou tudo bloqueado).
- Acesso amplo "por conveniência"; contas compartilhadas; sem expiração.
- Políticas por usuário/tabela (não escala) em vez de papéis/tags.
- Esquecer derivados (cópias/extratos de PII em outros sistemas).
- Sem revisão de acessos → acúmulo de privilégios.

## Boas práticas

- Poucos níveis claros; classificação por coluna, automatizada + validada; tags como gatilho de política.
- RBAC/ABAC + RLS/CLS/mascaramento; deny by default; acesso com justificativa e prazo.
- Recertificação periódica; auditoria; propagar classificação por lineage.

## Relação com outros conceitos

- [Ownership](../04-ownership-stewardship/README.md), [catálogo](../02-metadata-catalog/README.md),
  [lineage](../03-lineage/README.md), [auditoria](../06-retention-auditing/README.md),
  [IAM](../../26-security/02-iam/README.md), [mascaramento/PII](../../26-security/07-data-masking-pii/README.md),
  [LGPD](../../26-security/08-lgpd/README.md).

## Exercícios

1. Defina 4 níveis de classificação e controles para cada, com exemplos de colunas.
2. Desenhe uma política por tag `pii=true` com 3 papéis e comportamentos distintos.
3. Explique row-level vs column-level security com um caso de vendas por região.
4. Descreva o fluxo de pedido de acesso a dados restritos, com prazo e recertificação.

## Referências

- LGPD (Lei 13.709/2018); ISO 27001/27701; NIST SP 800-53 (controle de acesso); docs de Lake Formation,
  Unity Catalog, BigQuery policy tags, Snowflake masking/row access policies.
