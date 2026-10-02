# 12 — Data Quality

> 🔵 Nível 3 — Pipelines · Pré: [09 — ETL/ELT](../09-etl-elt/README.md),
> [10 — Pipelines](../10-data-pipelines/README.md) · Próximo:
> [13 — Data Warehouse](../13-data-warehouse/README.md)

Dados errados são piores que dados ausentes: quando falta dado, você sabe; quando o dado está
**errado mas parece certo**, decisões são tomadas sobre mentiras. **Data Quality** é o
conjunto de dimensões, técnicas e ferramentas para garantir que os dados são confiáveis — e
para **detectar** quando deixam de ser.

## Por que importa

A confiança é o ativo mais frágil de uma plataforma de dados. Um número errado num dashboard
executivo destrói a credibilidade de todo o time. Qualidade não é um "extra" — é parte do
produto de dados, e deve ser automatizada e monitorada como código.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Dimensões de qualidade](01-dimensions-of-quality/README.md) | Completude, acurácia, consistência... |
| 02 | [Data contracts](02-data-contracts/README.md) | Acordos de schema/semântica (intro) |
| 03 | [Schema validation](03-schema-validation/README.md) | Validar estrutura e tipos |
| 04 | [Expectation testing](04-expectation-testing/README.md) | Testes baseados em expectativas |
| 05 | [Great Expectations](05-great-expectations/README.md) | Framework de qualidade |
| 06 | [dbt tests](06-dbt-tests/README.md) | Testes de dados no dbt |
| 07 | [Anomaly detection](07-anomaly-detection/README.md) | Detectar o anômalo automaticamente |

## Dependências internas

```text
Dimensões de qualidade ─► Data contracts
          │                     │
          ▼                     ▼
Schema validation ─► Expectation testing ─┬─► Great Expectations
                                          └─► dbt tests
          │
          ▼
Anomaly detection
```

## Checkpoint

- [ ] Enumerar as dimensões de qualidade e dar um teste para cada.
- [ ] Explicar o papel de um data contract na prevenção de problemas.
- [ ] Validar schema e tipos de um dataset (fail/quarentena).
- [ ] Escrever testes de expectativa (unicidade, not-null, faixa, referência).
- [ ] Usar Great Expectations e/ou dbt tests num pipeline.
- [ ] Explicar detecção de anomalias (volume/frescor/distribuição) e seus limites.

## Referências do módulo

- Reis & Housley, *Fundamentals of Data Engineering* — qualidade e governança.
- Documentação de Great Expectations, dbt tests, Soda.
- *Data Quality Fundamentals*, Moses et al. (O'Reilly).
