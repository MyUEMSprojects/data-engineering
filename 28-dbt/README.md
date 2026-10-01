# 28 — dbt (data build tool)

> 🔵 Nível 4 — Analytics Platforms · Pré: [05 — SQL](../05-sql/README.md),
> [07 — Modeling](../07-data-modeling/README.md),
> [13 — Warehouse](../13-data-warehouse/README.md) · Relacionado:
> [09 — ETL/ELT](../09-etl-elt/README.md), [11 — Orquestração](../11-orchestration/README.md)

**dbt** é a ferramenta que trouxe boas práticas de engenharia de software (versionamento, testes,
documentação, modularidade) para a **transformação de dados com SQL**. É o "T" do
[ELT](../09-etl-elt/01-etl-vs-elt/README.md) moderno: você escreve `SELECT`s, e o dbt gerencia
dependências, materialização, testes, lineage e docs no [warehouse](../13-data-warehouse/README.md).
Transformou o papel de "Analytics Engineer".

## Por que importa

Antes do dbt, transformação em SQL era um amontoado de scripts/procedures sem versionamento, testes
nem lineage. O dbt trouxe disciplina: SQL versionado em Git, modular (CTEs/refs), testado, documentado
e com lineage automático — tudo rodando **dentro** do warehouse (aproveitando a separação
storage/compute).

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [O que é dbt](01-what-is-dbt/README.md) | Conceito, lugar na arquitetura |
| 02 | [Models](02-models/README.md) | SELECTs como modelos; materializations |
| 03 | [Sources e seeds](03-sources-seeds/README.md) | Declarar fontes; carregar CSVs pequenos |
| 04 | [Snapshots](04-snapshots/README.md) | SCD2 automatizado |
| 05 | [Tests](05-tests/README.md) | Testes de dados |
| 06 | [Macros e Jinja](06-macros-jinja/README.md) | Templating e reuso |
| 07 | [Documentação e lineage](07-documentation-lineage/README.md) | Docs e DAG automáticos |
| 08 | [Incremental models](08-incremental-models/README.md) | Processar só o novo |
| 09 | [Deployment](09-deployment/README.md) | CI/CD, ambientes, orquestração |

## Dependências internas

```text
O que é dbt ─► Models ─► Sources/seeds ─► Snapshots
                 │           │
                 ▼           ▼
             Tests ─► Macros/Jinja ─► Documentação/lineage ─► Incremental ─► Deployment
```

## Checkpoint

- [ ] Explicar onde o dbt se encaixa (o "T" do ELT, dentro do warehouse).
- [ ] Escrever models com `ref()`/`source()` e escolher materializations.
- [ ] Declarar sources (com freshness) e usar seeds.
- [ ] Implementar SCD2 com snapshots.
- [ ] Adicionar tests (`unique`/`not_null`/`relationships`/custom).
- [ ] Usar Jinja/macros para reuso (DRY).
- [ ] Entender o lineage/docs gerados e configurar um modelo incremental.
- [ ] Rodar dbt em CI/CD com ambientes separados.

## Referências do módulo

- Documentação oficial do dbt (docs.getdbt.com).
- dbt Labs — guias de Analytics Engineering.
