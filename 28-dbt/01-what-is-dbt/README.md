# O que é dbt

> 🔵 Analytics Platforms · Parte de [28 — dbt](../README.md)

## O que é

**dbt (data build tool)** é um framework de transformação que deixa você construir pipelines de
dados analíticos escrevendo **apenas `SELECT`s**. O dbt compila esses SELECTs em DDL/DML, gerencia a
**ordem de dependências**, **materializa** o resultado como tabelas/views no
[warehouse](../../13-data-warehouse/README.md), roda **testes**, gera **documentação** e
**lineage** — tudo versionado em Git.

Resumindo: dbt é o "**T**" do [ELT](../../09-etl-elt/01-etl-vs-elt/README.md), com práticas de
engenharia de software aplicadas a SQL.

## O que dbt faz e o que NÃO faz

- **Faz:** transformação (SQL → tabelas/views), dependências, testes de dados, docs/lineage,
  snapshots (SCD2), materializações incrementais.
- **NÃO faz:** extração/carga (o "E" e "L" — isso é [ingestão](../../09-etl-elt/02-ingestion-extraction/README.md)/
  Airbyte/Fivetran), orquestração (é [Airflow/Dagster](../../11-orchestration/README.md) que *roda*
  o dbt), nem é um banco (ele roda **dentro** do seu warehouse).

```text
Extract/Load (Airbyte/Fivetran/scripts) ─► Warehouse (dados brutos)
                                                  │
                                              dbt (TRANSFORM: staging → marts)
                                                  │
                                              BI / ML
   (dbt é disparado por um orquestrador; roda SQL no warehouse)
```

## Por que mudou o jogo

Antes do dbt, transformação em SQL era:

- Scripts/procedures soltos, sem versionamento nem testes.
- Dependências implícitas ("rode esse antes daquele" na cabeça de alguém).
- Sem lineage, sem docs, difícil de manter.

dbt trouxe **engenharia de software para analytics**:

| Prática de SWE | Como o dbt traz |
| --- | --- |
| Versionamento | models são arquivos SQL/YAML em Git |
| Modularidade/DRY | `ref()` entre models; [macros/Jinja](../06-macros-jinja/README.md) |
| Testes | [data tests](../05-tests/README.md) declarativos |
| Documentação | [docs + lineage](../07-documentation-lineage/README.md) automáticos |
| CI/CD | `dbt build` em [pipelines](../09-deployment/README.md) |
| Ambientes | dev/staging/prod via *targets* |

## Como funciona na prática

1. Você escreve **models** (`.sql`), cada um um `SELECT` que referencia outros com `ref('outro')`.
2. dbt monta o **DAG** de dependências a partir dos `ref()`/`source()` (lineage grátis — ver
   [DAGs](../../10-data-pipelines/02-dags-dependencies/README.md)).
3. `dbt run` compila e executa na ordem certa, **materializando** cada model (view/table/incremental).
4. `dbt test` valida os dados; `dbt docs` gera documentação navegável.
5. `dbt build` faz tudo na ordem (run + test), parando dependentes se um teste falha.

```sql
-- models/marts/fct_vendas.sql
select
    p.id,
    c.cliente_sk,
    p.valor
from {{ ref('stg_pedidos') }} p          -- dependência explícita → vira o DAG
join {{ ref('dim_cliente') }} c on c.cliente_id = p.cliente_id
```

## dbt Core vs dbt Cloud

- **dbt Core** — open source, CLI; você orquestra/roda (via Airflow, cron, CI).
- **dbt Cloud** — SaaS com IDE, scheduler, CI integrado, docs hospedadas.

## O papel do Analytics Engineer

dbt consolidou um papel entre [Data Engineer e Analyst](../../01-foundations/02-data-engineer-vs-other-roles/README.md):
o **Analytics Engineer**, que transforma dados já ingeridos em modelos limpos e confiáveis usando
SQL + dbt, aplicando modelagem [dimensional](../../07-data-modeling/04-dimensional-modeling/README.md)
e boas práticas.

## Onde dbt se encaixa (arquitetura)

- **Camadas** [medallion](../../14-data-lake/03-medallion-architecture/README.md): `sources` (raw/
  bronze) → `staging` (silver) → `marts` (gold).
- **Adaptadores** para o warehouse: BigQuery, Snowflake, Redshift, Postgres, Databricks/Spark,
  DuckDB — o mesmo projeto roda em vários (com cuidado com dialeto).
- Disparado por um [orquestrador](../../11-orchestration/README.md); integra nativamente com
  [Dagster](../../11-orchestration/03-dagster/README.md).

## Erros comuns

- Achar que dbt faz extração/carga (não faz — é só o T).
- Usar dbt sem testes/docs (perde metade do valor).
- SQL sem `ref()` (perde o DAG/lineage).
- Rodar `dbt run` sem `dbt test` em produção (ver [tests](../05-tests/README.md)).

## Boas práticas

- Estruture em staging → intermediate → marts; use `ref()`/`source()` sempre.
- Teste e documente desde o início; rode `dbt build`.
- Versione tudo em Git; ambientes separados (dev/prod).
- Deixe E/L para ferramentas de ingestão e a orquestração para o orquestrador.

## Relação com outros conceitos

- O "T" do [ELT](../../09-etl-elt/01-etl-vs-elt/README.md); roda no
  [warehouse](../../13-data-warehouse/README.md).
- [Models](../02-models/README.md), [tests](../05-tests/README.md),
  [lineage](../07-documentation-lineage/README.md).
- Orquestrado por [Airflow/Dagster](../../11-orchestration/README.md); usado no
  [Projeto 02](../../projects/02-analytics-warehouse/README.md).

## Exercícios

1. Explique o que o dbt faz e o que NÃO faz (E/L, orquestração).
2. Escreva dois models encadeados com `ref()` e descreva o DAG resultante.
3. Diferencie dbt Core e dbt Cloud.
4. Descreva onde o dbt se encaixa numa arquitetura medallion.

## Referências

- Documentação oficial do dbt (docs.getdbt.com) — "What is dbt?".
- dbt Labs — Analytics Engineering guide.
