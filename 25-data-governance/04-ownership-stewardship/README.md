# Ownership e stewardship

> 🟣 Production · Parte de [25 — Data Governance](../README.md)

## O que é

Governança exige **responsabilidade nominal**: para cada dado, alguém responde por ele. Dois conceitos:

- **Data Ownership (propriedade)** — responsabilidade **de decisão e prestação de contas** sobre um dado/
  domínio: define acesso, uso aceitável, requisitos de qualidade e aprova mudanças. Geralmente de **negócio**
  (ou do time produtor, no data mesh).
- **Data Stewardship (curadoria/zeladoria)** — responsabilidade **operacional e cotidiana** pela qualidade,
  definições, metadados e conformidade do dado, em nome do owner.

> Dado **sem dono** é dado sem responsável: ninguém corrige, documenta, aprova acesso ou responde a
> incidente. É a causa-raiz de muito "pântano".

## Papéis e responsabilidades

| Papel | Responde por | Exemplo |
| --- | --- | --- |
| **Data Owner** | decisões e responsabilização; aprova acesso, define criticidade/SLAs/retenção | diretor de Vendas p/ domínio vendas |
| **Data Steward** | qualidade, glossário, metadados, resolução de dúvidas/defeitos do domínio | analista sênior de vendas |
| **Data Producer** | gera/publica o dado (app/time fonte); mantém o [contrato](../../29-data-contracts/README.md) | time do app de pedidos |
| **Data Custodian/Engineer** | implementa controles técnicos, pipelines, segurança, backup | engenharia de dados/plataforma |
| **Data Consumer** | usa conforme políticas; reporta problemas | analistas, DS, ML |
| **DPO/Encarregado** | privacidade ([LGPD](../../26-security/08-lgpd/README.md)) | jurídico/compliance |

Em modelos federados/[data mesh](../../30-advanced/03-data-mesh/README.md), o **time de domínio** é dono do
**data product** (ownership alinhado a quem melhor conhece o dado).

## Ownership na prática (técnico)

Materialize ownership **no código e no catálogo**, não só em slides:

```yaml
# dbt: dono e metadados no YAML do modelo
models:
  - name: fct_vendas
    meta:
      owner: time-vendas@empresa.com
      steward: ana.silva
      tier: 1
      pii: false
      sla_freshness: "06:00 BRT"
      on_call: "#dados-vendas"
```

- **Catálogo** ([DataHub/OpenMetadata](../../27-data-catalog-metadata/04-tools/README.md)): campo
  owner/steward/domínio obrigatório; sincronizado de dbt/IaC.
- **CODEOWNERS** no Git: revisão obrigatória do dono em mudanças dos seus modelos/DAGs
  ([PRs](../../03-git-software-engineering/03-pull-requests-code-review/README.md)).
- **Alertas roteados ao dono** ([alertas](../../24-observability/04-alerting/README.md)).
- **Tags de IAM/cloud** (`owner`, `team`) para custo e acesso ([cost](../../19-cloud/08-cost-management/README.md)).
- **Contratos** declaram o produtor responsável.

## O que o owner/steward decide e faz

- **Definição e semântica** (glossário), **criticidade/tier** e SLAs ([SLO](../../24-observability/05-sli-slo-sla/README.md)).
- **Aprova/nega acesso** (ou delega política) — [controle de acesso](../05-access-control-classification/README.md).
- **Qualidade**: define regras/limiares ([data quality](../../12-data-quality/README.md)), triagem de defeitos.
- **Mudanças**: aprova alterações de schema/semântica (breaking changes — [contracts](../../29-data-contracts/README.md)).
- **Ciclo de vida**: retenção, arquivamento, descontinuação ([retenção](../06-retention-auditing/README.md)).
- **Incidentes**: responde por dados do domínio ([incident response](../../24-observability/07-incident-response/README.md)).

## Modelos de organização

- **Centralizado** — time central de governança/dados decide (consistente, pode virar gargalo).
- **Descentralizado/federado** — domínios donos, com **padrões e plataforma comuns** (escala; exige
  maturidade) — ver [arquitetura](../08-governance-architecture/README.md).
- **Híbrido** (mais comum): políticas globais + responsabilidade local.

## Como começar

1. **Inventarie** os datasets críticos (tier 1) e **atribua dono/steward** a cada um.
2. **Torne obrigatório** owner no catálogo/dbt para publicar/certificar.
3. **Defina o fluxo** (RACI) para: pedir acesso, mudar schema, reportar defeito, aposentar dataset.
4. **Meça**: % de datasets com dono; tempo de resposta a defeitos; datasets órfãos.
5. **Trate órfãos**: dono em X dias ou depreciação.

## Erros comuns

- Datasets sem dono ("é da TI/ninguém").
- Dono apenas nominal (não decide nem responde).
- Confundir owner (decisão) com custodian (implementação) → engenharia vira dona de tudo.
- Ownership só em documento, não em catálogo/código/alertas.
- Sobrecarregar poucos stewards; sem tempo/incentivo.
- Dono mudou de função e ninguém atualizou.

## Boas práticas

- Dono/steward obrigatórios para tier-1; registrados no catálogo, dbt, CODEOWNERS e alertas.
- Papéis claros (RACI); incentivos e tempo reservado para stewardship.
- Revisão periódica (atestado de ownership); tratar órfãos.
- Alinhar ownership a domínios de negócio ([data mesh](../../30-advanced/03-data-mesh/README.md)).

## Relação com outros conceitos

- [Catálogo](../02-metadata-catalog/README.md), [data contracts](../../29-data-contracts/README.md),
  [controle de acesso](../05-access-control-classification/README.md),
  [alertas](../../24-observability/04-alerting/README.md), [data mesh](../../30-advanced/03-data-mesh/README.md).

## Exercícios

1. Defina owner, steward e producer para o dataset "pedidos" e as decisões de cada um.
2. Escreva o `meta` do dbt com owner/steward/tier/SLA para um modelo crítico.
3. Proponha um processo para tratar datasets órfãos.
4. Compare ownership centralizado e federado em escala e riscos.

## Referências

- DAMA-DMBOK (Data Governance, Stewardship); Dehghani, Z. *Data Mesh* (ownership por domínio).
- Eryurek et al., *Data Governance: The Definitive Guide*.
