# Implementação na prática

> 🟣 Advanced · Parte de [29 — Data Contracts](../README.md)

## Objetivo

Sair do conceito e **adotar contratos** de forma incremental: escolher formato e ferramentas, integrá-los
ao fluxo (Git, CI, catálogo, runtime) e conduzir a **mudança organizacional** — que costuma ser a parte
mais difícil.

## Stack mínima viável (comece simples)

```text
1. Contrato em YAML no repo do PRODUTOR (versionado)        ← fonte única da verdade
2. CI: lint + breaking-change check + testes de contrato     ← bloqueia mudanças incompatíveis
3. Validação em runtime (gate/WAP) + monitoramento           ← garante o dado publicado
4. Publicação no catálogo (descoberta, donos, lineage)       ← consumidores acham e se registram
5. Notificação aos consumidores em mudanças/violações        ← Slack/e-mail/webhooks
```

## Formato do contrato (escolhas)

| Opção | Notas |
| --- | --- |
| **Open Data Contract Standard (ODCS)** — Bitol/Linux Foundation | padrão aberto em YAML: schema, qualidade, SLAs, ownership, termos; foco em interoperabilidade |
| **Data Contract Specification** (datacontract.com) + **Data Contract CLI** | YAML + CLI com `lint/test/breaking/export`; convergindo com o ODCS |
| **Schemas de formato** (Avro/Protobuf/JSON Schema) | ótimos para **estrutura**; precisam de camada para qualidade/SLA/ownership |
| **dbt model contracts + tests** | contrato de **tabelas** no warehouse; colunas/tipos impostos + testes |
| **Custom (JSON/YAML próprio)** | só se necessário — evite reinventar; prefira padrões |

> Padrões e ferramentas evoluem rápido: **confirme a versão vigente** do ODCS/Data Contract Specification
> e do CLI na documentação oficial antes de adotar; o exemplo abaixo é **ilustrativo**.

### Exemplo ilustrativo (YAML)

```yaml
apiVersion: v3.0.0                 # versão do padrão (ilustrativo)
kind: DataContract
id: urn:datacontract:vendas:orders
name: Pedidos
version: 1.3.0
status: active
domain: vendas
owner: time-pedidos@empresa.com
description:
  purpose: "Pedidos confirmados para analytics, finanças e ML."
  limitations: "Não inclui rascunhos; correções retroativas até D+3."
schema:
  - name: orders
    description: "Uma linha por pedido confirmado."
    properties:
      - { name: order_id,   logicalType: string,  required: true, unique: true }
      - { name: amount,     logicalType: number,  required: true, description: "BRL, com impostos, sem frete" }
      - { name: status,     logicalType: string,  description: "CREATED|PAID|SHIPPED|CANCELED" }
      - { name: customer_id,logicalType: string,  required: true, classification: internal }
      - { name: email,      logicalType: string,  classification: restricted, tags: [pii] }
quality:
  - { rule: "amount >= 0" }
  - { rule: "row_count between 0.8*avg_7d and 1.2*avg_7d" }
slaProperties:
  - { property: freshness, value: 1, unit: h }
  - { property: availability, value: 99.5, unit: percent }
```

## Integração no ciclo de vida

### 1. Desenvolvimento (Git + PR)
Contrato junto do código/schema do produtor; mudanças por **PR**, com **CODEOWNERS** (dono + consumidores
críticos) ([PRs](../../03-git-software-engineering/03-pull-requests-code-review/README.md)).

### 2. CI/CD
- **Lint** do contrato; **breaking-change check** vs versão publicada; **testes de contrato**; geração de
  artefatos (SQL/dbt/Avro/JSON Schema/docs) **a partir do contrato**
  ([contract testing](../05-contract-testing/README.md), [CI](../../23-cicd-dataops/01-continuous-integration/README.md)).
- Publicação automática no **registry/catálogo** ao mergear.

### 3. Runtime
- **Streaming**: Schema Registry + validação semântica no produtor; consumidor tolerante.
- **Batch/warehouse**: **Write-Audit-Publish**, dbt `contract: enforced`, testes (dbt/GX/Soda) como gate do
  [DAG](../../10-data-pipelines/02-dags-dependencies/README.md).
- **Monitoramento** de SLAs/qualidade com alertas ao dono ([observability](../../24-observability/README.md)).

### 4. Catálogo e governança
Importar contratos para o catálogo (ownership, classificação, SLAs, lineage, consumidores) —
**DataHub/OpenMetadata** têm suporte a contratos ([ferramentas](../../27-data-catalog-metadata/04-tools/README.md)).
PII declarada no contrato **aciona** políticas de mascaramento/acesso
([classificação](../../25-data-governance/05-access-control-classification/README.md)).

## Exemplo: contrato → dbt (geração/aplicação)

```yaml
# models/marts/_orders.yml (gerado a partir do contrato ou mantido em sincronia)
models:
  - name: orders
    config: { contract: { enforced: true } }      # dbt valida colunas/tipos na materialização
    columns:
      - { name: order_id,  data_type: string,        constraints: [{ type: not_null }, { type: primary_key }] }
      - { name: amount,    data_type: numeric(12,2), tests: [{ dbt_utils.accepted_range: { min_value: 0 } }] }
      - { name: status,    data_type: string,        tests: [{ accepted_values: { values: [CREATED, PAID, SHIPPED, CANCELED] } }] }
```
(Constraints de warehouse podem ser **informativas** — complemente com testes: ver
[constraints](../../05-sql/09-constraints/README.md).)

## Roteiro de adoção (rollout)

```text
Fase 0 — Descoberta: mapear datasets críticos (tier-1), seus donos e consumidores (lineage/catálogo); eleger 2–3 pilotos com pares colaborativos
Fase 1 — Piloto: contrato leve (schema + dono + SLA) + CI com breaking-change check + validação básica; medir incidentes evitados
Fase 2 — Qualidade: semântica + regras executáveis + WAP; monitoramento e alertas ao dono
Fase 3 — Escala: templates/geradores, registro de consumidores, políticas por tag (PII), publicação automática no catálogo
Fase 4 — Cultura: dados como produto, métricas por domínio, depreciação disciplinada, contratos como pré-requisito para novos produtores
```

## Métricas de sucesso

- % de datasets tier-1 com contrato verificado automaticamente.
- Nº de **breaking changes bloqueadas** no CI / **incidentes por mudança de schema** (↓).
- Tempo de resposta a violações; SLAs de frescor/qualidade cumpridos.
- % de consumidores registrados; tempo de migração entre versões.
- Satisfação/adoção por produtores e consumidores.

## Desafios e como lidar

| Desafio | Mitigação |
| --- | --- |
| **Resistência dos produtores** ("é mais trabalho") | mostre dor evitada; automatize (geração/CI); comece pelos dados que **já** causam incidentes; patrocínio executivo |
| **Contratos desatualizados** | fonte única no repo do produtor; verificação automática; contrato gerado do código quando possível |
| **Muitos consumidores/versões** | view pública estável; política de depreciação; ferramentas de migração |
| **Legado sem donos** | priorize por criticidade; atribua ownership; "contrato mínimo" retroativo |
| **Complexidade de ferramentas** | adote padrão aberto e CLI; evite plataforma pesada antes de maturidade |
| **Falsos positivos** | calibre regras; severidades; revisão periódica |

## Anti-padrões

- "Contract-washing": contratos escritos mas **sem verificação** nem dono.
- Imposição top-down do time de dados sem colaboração.
- Reinventar formato proprietário e ferramentas.
- Cobrir tudo antes de provar valor; ou cobrir só schema.
- Duplicar a definição (contrato ≠ schema real) sem sincronização.

## Boas práticas

- Fonte única no repo do produtor; geração de artefatos; verificação no CI + runtime.
- Padrão aberto (ODCS/Data Contract Spec) + CLI; integrar ao catálogo/lineage.
- Piloto → escala; medir; tratar contratos como produto interno.
- Combinar com [data mesh](../../30-advanced/03-data-mesh/README.md)/governança federada.

## Relação com outros conceitos

- [Conceito](../01-concept/README.md), [contract testing](../05-contract-testing/README.md),
  [compatibilidade](../04-compatibility-versioning/README.md), [dbt](../../28-dbt/README.md),
  [catálogo](../../27-data-catalog-metadata/README.md), [DataOps](../../23-cicd-dataops/05-dataops/README.md).

## Exercícios

1. Escreva o contrato (YAML) de um dataset real seu, com schema, qualidade, SLA, dono e PII.
2. Monte o workflow de CI que valida o contrato e bloqueia breaking changes.
3. Gere (manual ou com CLI) o modelo dbt com `contract: enforced` a partir do contrato.
4. Planeje um piloto de 6 semanas: dataset, produtor/consumidores, métricas e riscos.

## Referências

- datacontract.com (Data Contract Specification/CLI); Open Data Contract Standard (Bitol);
  dbt model contracts; docs de DataHub/OpenMetadata (data contracts); Confluent Data Contracts.
