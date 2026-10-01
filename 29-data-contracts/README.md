# 29 — Data Contracts

> 🟣 Nível 8 — Advanced · Pré: [12 — Data Quality](../12-data-quality/README.md),
> [08 — Schema evolution](../08-data-formats/10-schema-evolution/README.md),
> [27 — Catalog](../27-data-catalog-metadata/README.md) · Próximo: [30 — Advanced](../30-advanced/README.md)

Um **data contract** é um **acordo explícito, versionado e verificável** entre quem **produz** um dado e
quem o **consome**: define **schema, semântica, qualidade, frescor, ownership e política de mudança**.
Resolve a maior fonte de incidentes em dados — **mudanças não comunicadas na origem** — tornando as
expectativas explícitas e **automaticamente verificadas**.

## Por que importa

Hoje, muitos pipelines dependem de dados de sistemas operacionais cujos times **não sabem** que alguém
consome seus dados. Um `ALTER TABLE` ou renomeação "inofensiva" quebra dashboards e modelos de ML a jusante.
Contratos deslocam a responsabilidade para a **origem** ("shift-left") e criam uma **fronteira clara** entre
times — pilar de [data mesh](../30-advanced/03-data-mesh/README.md) e de [DataOps](../23-cicd-dataops/05-dataops/README.md).

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Conceito e motivação](01-concept/README.md) | O que é, por que existe, o que cobre |
| 02 | [Schema e semântica](02-schema-semantics/README.md) | Estrutura, tipos, significado |
| 03 | [Ownership, produtor e consumidor](03-ownership-producer-consumer/README.md) | Responsabilidades e acordos |
| 04 | [Compatibilidade e versionamento](04-compatibility-versioning/README.md) | Evoluir sem quebrar |
| 05 | [Contract testing](05-contract-testing/README.md) | Verificar automaticamente |
| 06 | [Implementação na prática](06-implementation/README.md) | Formatos, ferramentas, rollout |

## Dependências internas

```text
Conceito ─► Schema/semântica ─► Ownership (produtor/consumidor)
                                        │
                  Compatibilidade/versionamento ─► Contract testing ─► Implementação
```

## Checkpoint

- [ ] Explicar o problema que contratos resolvem e o que um contrato contém.
- [ ] Especificar schema, semântica e garantias (qualidade, frescor) de um dataset.
- [ ] Definir responsabilidades de produtor e consumidor e o processo de mudança.
- [ ] Aplicar regras de compatibilidade (backward/forward/full) e SemVer a contratos.
- [ ] Implementar contract tests no CI e verificação em runtime.
- [ ] Escolher formato/ferramentas e planejar a adoção gradual.

## Referências do módulo

- Open Data Contract Standard (ODCS — Bitol), datacontract.com (Data Contract Specification).
- Confluent Schema Registry (compatibilidade); Pact (consumer-driven contract testing).
- Dehghani, Z. *Data Mesh*; Moses, B. *Data Quality Fundamentals*.
