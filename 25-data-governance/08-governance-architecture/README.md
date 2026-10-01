# Arquitetura de governança

> 🟣 Production · Parte de [25 — Data Governance](../README.md)

## O que é

A **arquitetura de governança** define **como** as políticas e controles de governança são organizados,
implementados e automatizados na plataforma de dados e na organização: modelo organizacional
(centralizado vs federado), componentes técnicos (catálogo, lineage, políticas, qualidade, auditoria) e
como se integram ao fluxo de engenharia.

## Dimensão organizacional

### Centralizada
Um **time central** define e aplica as regras e geralmente também detém/curando os dados.
- ✅ Consistência, controle forte, simples de começar.
- ❌ **Gargalo** (tudo passa pelo time central), distante do contexto de negócio, não escala.

### Descentralizada (sem coordenação)
Cada área governa por conta própria.
- ✅ Rápido localmente. ❌ Silos, padrões divergentes, risco regulatório, "dados que não conversam".

### Federada (o equilíbrio moderno)
**Padrões e plataforma globais** (políticas, segurança, interoperabilidade) + **responsabilidade e execução
nos domínios** (donos de dados de cada área). É o modelo do [data mesh](../../30-advanced/03-data-mesh/README.md):
*federated computational governance*.

```text
Conselho/Time central de governança  → define políticas globais, padrões, plataforma self-service, auditoria
Domínios (vendas, risco, produto)     → donos/stewards: dados como produto, qualidade, acesso do domínio
```

**Quando usar**: centralizada em organizações pequenas/início ou setores muito regulados; **federada**
quando há vários domínios, escala e maturidade; evite descentralização sem padrões mínimos.

## Dimensão técnica: os componentes

```text
                ┌────────────── Camada de políticas (policy-as-code) ──────────────┐
Fontes ─► Ingestão ─► Lake/Warehouse/Lakehouse ─► Serving/BI/ML
   │            │                │                       │
   └─────────── Catálogo + Metadados + Lineage + Classificação (plano de metadados) ───────────┘
                     Qualidade/contratos · Acesso/mascaramento · Auditoria · Retenção
```

| Componente | Função | Referência |
| --- | --- | --- |
| **Catálogo/metadados** | inventário, glossário, ownership | [02](../02-metadata-catalog/README.md), [27](../../27-data-catalog-metadata/README.md) |
| **Lineage** | origem/impacto | [03](../03-lineage/README.md) |
| **Classificação** | sensibilidade por coluna | [05](../05-access-control-classification/README.md) |
| **Controle de acesso/mascaramento** | enforcement (RBAC/ABAC, RLS/CLS) | [05](../05-access-control-classification/README.md), [security](../../26-security/README.md) |
| **Qualidade e contratos** | testes, expectativas, acordos | [Data Quality](../../12-data-quality/README.md), [contracts](../../29-data-contracts/README.md) |
| **Retenção/auditoria** | lifecycle, trilhas | [06](../06-retention-auditing/README.md) |
| **Observabilidade de dados** | frescor, volume, anomalias | [24](../../24-observability/README.md) |
| **Orquestração/CI-CD** | aplicar controles no fluxo | [DataOps](../../23-cicd-dataops/05-dataops/README.md) |

## Princípios arquiteturais

- **Governança como código (policy-as-code)** — políticas versionadas, testáveis e aplicadas
  automaticamente (OPA, Terraform/IaC, regras do warehouse/catálogo, dbt tests). O que não é automatizado
  não é consistentemente aplicado.
- **Shift-left** — verificar **no desenvolvimento/CI** (contratos, classificação obrigatória, owner
  obrigatório) antes de chegar à produção ([CI](../../23-cicd-dataops/01-continuous-integration/README.md)).
- **Guarda-corpos, não portões** — self-service rápido dentro de limites seguros; exceções auditadas.
- **Metadados como plano de controle** — tags/classificação/owner no catálogo **acionam** políticas
  (acesso, mascaramento, retenção) — *active metadata*.
- **Plataforma de dados como produto** — a plataforma central oferece governança "pronta" (templates, IaC,
  catálogo, mascaramento por tag) para os domínios.
- **Proporcionalidade ao risco** — controles fortes onde há PII/regulação; leves onde não há.
- **Interoperabilidade** — padrões comuns (formatos abertos, contratos, OpenLineage) entre domínios e
  ferramentas ([data contracts](../../29-data-contracts/README.md)).

## Escolha de ferramentas (sem hype)

| Necessidade | Opções |
| --- | --- |
| Catálogo/metadados/lineage | DataHub, OpenMetadata, Atlas (open source); Purview, Dataplex, Glue/Lake Formation, Unity Catalog (nativos); Collibra, Alation, Atlan (comerciais) — [ferramentas](../../27-data-catalog-metadata/04-tools/README.md) |
| Políticas de acesso | IAM + Lake Formation/Unity Catalog/Snowflake/BigQuery policy tags; OPA/Ranger |
| Qualidade | dbt tests, Great Expectations, Soda ([Data Quality](../../12-data-quality/README.md)) |
| Descoberta de PII | Macie, DLP API, Purview, scanners do catálogo |
| Lineage | dbt, OpenLineage + backend |

Prefira o que **integra bem ao seu stack** e é **automatizável**; evite comprar suíte cara sem adoção.

## Maturidade e roadmap prático

1. **Fundamento**: inventário dos dados críticos, **owners**, classificação básica de PII, acesso por papéis.
2. **Automação**: catálogo alimentado por dbt/plataforma; lineage; tags de PII aplicando mascaramento;
   testes/contratos no CI.
3. **Escala**: governança federada, produtos de dados, certificação, política baseada em tags,
   recertificação automática, métricas.
4. **Otimização**: governança preditiva/ativa (alertas de risco, descontinuação de ativos sem uso).

Comece pelo **tier 1 e pelos dados pessoais**; expanda.

## Métricas de governança

- % de datasets com **dono**, **descrição**, **classificação**, **lineage**.
- % de colunas PII **mascaradas/protegidas**; nº de acessos fora da política; tempo de concessão de acesso.
- Cobertura de testes de qualidade/contratos; SLAs de frescor cumpridos.
- Tempo de resposta a solicitações de titulares; incidentes de privacidade.
- Datasets órfãos/sem uso removidos.

## Erros comuns

- Comprar uma ferramenta de governança esperando que "resolva" sem processo/donos.
- Governança só em documentos (sem automação/enforcement).
- Centralizar tudo (gargalo) ou descentralizar sem padrões (caos).
- Tentar cobrir tudo de uma vez; sem foco em risco.
- Governança alheia ao fluxo de engenharia (sem CI/policy-as-code).
- Não medir (sem métricas de cobertura/eficácia).

## Boas práticas

- Federada com padrões globais + domínios responsáveis; plataforma com guarda-corpos.
- Policy-as-code, shift-left, tags acionando controles, catálogo vivo.
- Foco em risco/valor; medir e iterar; formatos e contratos abertos.

## Relação com outros conceitos

- [Conceitos de governança](../01-governance-concepts/README.md), [ownership](../04-ownership-stewardship/README.md),
  [data mesh](../../30-advanced/03-data-mesh/README.md), [27 — Catalog](../../27-data-catalog-metadata/README.md),
  [security](../../26-security/README.md), [IaC](../../22-infrastructure-as-code/README.md).

## Exercícios

1. Compare governança centralizada, descentralizada e federada para uma empresa com 6 domínios.
2. Desenhe a arquitetura de governança (componentes e fluxo) para um lakehouse com PII.
3. Dê 3 exemplos de policy-as-code que impedem violações antes da produção.
4. Defina 6 métricas para acompanhar a maturidade de governança.

## Referências

- Dehghani, Z. *Data Mesh* (governança computacional federada); DAMA-DMBOK; Eryurek et al.,
  *Data Governance: The Definitive Guide*.
- Documentação de OPA, DataHub, OpenMetadata, Purview, Dataplex, Unity Catalog.
