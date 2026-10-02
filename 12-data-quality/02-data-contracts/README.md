# Data contracts (no contexto de qualidade)

> 🔵 Pipelines · Parte de [12 — Data Quality](../README.md)

## O que é

Um **data contract** (contrato de dados) é um acordo **explícito e versionado** entre quem
**produz** um dado e quem **consome**, definindo schema, semântica, garantias de qualidade,
frescor e políticas de mudança. É a formalização das expectativas de qualidade — a prevenção
levada a sério.

> Este tópico é uma **introdução** sob a ótica de qualidade. O tratamento completo (schema,
> ownership, compatibilidade, versionamento, contract testing) está no
> [módulo 29 — Data Contracts](../../29-data-contracts/README.md).

## Por que existe / que problema resolve

A maior fonte de incidentes de dados é a **mudança não comunicada na origem**: o time de
produto renomeia uma coluna, muda um tipo ou um significado, e o pipeline a jusante quebra (ou,
pior, processa errado em silêncio). Sem contrato, o consumidor depende da boa vontade/memória
do produtor. O contrato torna as expectativas **explícitas e verificáveis** — mudanças passam
a ser negociadas, não surpresas.

```text
Sem contrato:  produtor muta o schema ─► consumidor quebra sem aviso  ❌
Com contrato:  mudança incompatível é bloqueada/negociada antes de quebrar  ✅
```

## O que um contrato especifica

- **Schema** — colunas, tipos, obrigatoriedade.
- **Semântica** — o que cada campo *significa* (unidade, formato, domínio).
- **Garantias de qualidade** — unicidade de chave, não-nulos, faixas (as
  [dimensões](../01-dimensions-of-quality/README.md)).
- **Frescor/SLA** — quão atualizado o dado estará.
- **Política de mudança** — compatibilidade e versionamento (ver
  [schema evolution](../../08-data-formats/10-schema-evolution/README.md)).
- **Ownership** — quem é o dono/responsável.

## Como o contrato vira qualidade na prática

O contrato só tem valor se for **verificado automaticamente**:

- Na **origem/CI** — bloquear mudanças incompatíveis antes do deploy (ex.: Schema Registry
  rejeita schema incompatível — ver [Avro](../../08-data-formats/05-avro/README.md)).
- Na **ingestão/pipeline** — validar que os dados recebidos cumprem o contrato (ver
  [schema validation](../03-schema-validation/README.md),
  [validação](../../09-etl-elt/10-data-validation/README.md)).
- O [expectation testing](../04-expectation-testing/README.md) é, em essência, a verificação
  automatizada de um contrato.

## Contrato vs testes de qualidade

- **Testes de qualidade** verificam o dado **que chegou**.
- **Contrato** define o que **deveria** chegar e **quem responde** se não chegar, além de
  governar **mudanças**. O teste é o mecanismo; o contrato é o acordo (com dono e política).

## Erros comuns

- Depender de conhecimento tribal em vez de contrato explícito.
- Contrato que ninguém verifica (vira documento morto).
- Não versionar o contrato / não ter política de compatibilidade.
- Sem dono claro — ninguém responde quando quebra.

## Boas práticas

- Formalize expectativas com os produtores; versione o contrato.
- **Verifique** o contrato automaticamente (CI + ingestão).
- Defina compatibilidade e tratamento de breaking changes.
- Atribua ownership (ver [governança](../../25-data-governance/04-ownership-stewardship/README.md)).

## Relação com outros conceitos

- Completo em [29 — Data Contracts](../../29-data-contracts/README.md).
- [Dimensões de qualidade](../01-dimensions-of-quality/README.md),
  [schema validation](../03-schema-validation/README.md),
  [schema evolution](../../08-data-formats/10-schema-evolution/README.md).
- [Governança/ownership](../../25-data-governance/04-ownership-stewardship/README.md).

## Exercícios

1. Escreva um contrato (schema + semântica + garantias + frescor + dono) para uma tabela de
   eventos de clique.
2. Explique como um Schema Registry impõe parte desse contrato automaticamente.
3. Dê um exemplo de mudança na origem que o contrato pegaria antes de quebrar o consumidor.
4. Diferencie "teste de qualidade" de "data contract".

## Referências

- Documentação de data contracts (ver [módulo 29](../../29-data-contracts/README.md)).
- Reis & Housley, *Fundamentals of Data Engineering*.
