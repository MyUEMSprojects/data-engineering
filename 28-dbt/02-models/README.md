# Models

> 🔵 Analytics Platforms · Parte de [28 — dbt](../README.md)

## O que é

Um **model** é a unidade central do dbt: um arquivo `.sql` contendo um `SELECT`. O dbt o
**materializa** no [warehouse](../../13-data-warehouse/README.md) como uma view ou tabela, resolvendo
as dependências com outros models. Um projeto dbt é, essencialmente, uma coleção de models encadeados
que formam o [DAG](../../10-data-pipelines/02-dags-dependencies/README.md) de transformação.

## Anatomia de um model

```sql
-- models/staging/stg_pedidos.sql
with source as (
    select * from {{ source('raw', 'pedidos') }}      -- fonte declarada
),
limpo as (
    select
        id,
        cliente_id,
        cast(valor as numeric(12,2)) as valor,
        lower(trim(status)) as status,
        created_at::date as dia
    from source
    where id is not null
)
select * from limpo
```

- O nome do arquivo (`stg_pedidos`) vira o nome do model.
- `{{ source(...) }}` referencia uma [fonte](../03-sources-seeds/README.md);
  `{{ ref('outro_model') }}` referencia outro model → **cria a dependência** no DAG.
- O dbt envolve seu `SELECT` no DDL de materialização (não escreva `CREATE TABLE`).

## `ref()` — o coração do dbt

`{{ ref('stg_pedidos') }}` faz duas coisas: resolve o nome real da tabela (no schema/ambiente
correto) **e** declara que este model depende daquele. É assim que o dbt sabe a **ordem de execução**
e constrói o [lineage](../07-documentation-lineage/README.md) automaticamente.

```sql
-- models/marts/fct_vendas.sql
select p.id, c.cliente_sk, p.valor, p.dia
from {{ ref('stg_pedidos') }} p
join {{ ref('dim_cliente') }} c on c.cliente_id = p.cliente_id
```

> **Nunca** escreva o nome físico da tabela direto — sempre `ref()`/`source()`. É o que dá
> portabilidade entre ambientes e o DAG.

## Materializations (como o model vira dados)

Configurável por model (no YAML, no bloco `config()`, ou em `dbt_project.yml`):

| Materialization | O que faz | Quando usar |
| --- | --- | --- |
| **view** | cria uma view (recalcula na consulta) | leve, dados pequenos, staging |
| **table** | materializa como tabela (recria a cada run) | médio, acesso frequente |
| **incremental** | insere/atualiza só o novo | tabelas grandes ([incremental](../08-incremental-models/README.md)) |
| **ephemeral** | não materializa; vira CTE inline em quem referencia | reaproveitar lógica sem criar objeto |
| **materialized_view** | MV do warehouse (onde suportado) | pré-agregação gerenciada |

```sql
{{ config(materialized='table') }}
select ...
```

Trade-off: `view` é barata de criar mas recalcula a cada leitura; `table` é cara de criar mas rápida
de ler; `incremental` evita reprocessar tudo (ver [incremental](../08-incremental-models/README.md)).

## Estrutura de camadas (convenção)

Organize os models seguindo [medallion](../../14-data-lake/03-medallion-architecture/README.md):

```text
models/
├── staging/      stg_*  (1:1 com a fonte, limpeza leve) — silver
│   └── _sources.yml
├── intermediate/ int_*  (lógica reutilizável, joins intermediários)
└── marts/        fct_* / dim_*  (modelos de negócio dimensionais) — gold
```

Convenção dbt Labs: `stg_` (staging), `int_` (intermediate), `fct_`/`dim_` (marts). Isso torna o
projeto legível e o lineage claro.

## Configuração e nomes

- `config(materialized=..., schema=..., tags=..., cluster_by=...)` por model.
- Configs em massa no `dbt_project.yml` (ex.: tudo em `staging/` como `view`).
- Boas práticas de SQL: use **CTEs nomeadas** (ver [CTEs](../../05-sql/04-subqueries-ctes/README.md)),
  um model = uma responsabilidade.

## Model contracts (versões recentes)

dbt permite declarar o **schema esperado** de um model (colunas/tipos) como *contract*; o warehouse
impõe na materialização — útil para estabilidade/[data contracts](../../29-data-contracts/README.md).

## Rodando

```bash
dbt run                      # materializa todos os models (na ordem do DAG)
dbt run --select stg_pedidos+   # esse model e seus dependentes
dbt run --select marts.*     # por pasta
dbt build                    # run + test (recomendado)
```

O `--select` (seleção de grafo) permite rodar subconjuntos — essencial em projetos grandes.

## Erros comuns

- Escrever nome físico da tabela em vez de `ref()`/`source()` (perde DAG/portabilidade).
- `CREATE TABLE` dentro do model (o dbt já materializa).
- Tudo como `table` (custo) ou tudo como `view` (lento) sem pensar no trade-off.
- Models gigantes que fazem tudo (viole uma responsabilidade por model).
- Pular a camada de staging (acoplar marts direto à fonte).

## Boas práticas

- `ref()`/`source()` sempre; camadas staging → intermediate → marts.
- Escolha a materialization pelo tamanho/uso; incremental para tabelas grandes.
- CTEs legíveis; um model = uma responsabilidade.
- Use `--select` para rodar subconjuntos; `dbt build` para incluir testes.

## Relação com outros conceitos

- [Sources/seeds](../03-sources-seeds/README.md), [tests](../05-tests/README.md),
  [incremental](../08-incremental-models/README.md),
  [lineage](../07-documentation-lineage/README.md).
- Modelagem [dimensional](../../07-data-modeling/04-dimensional-modeling/README.md);
  camadas [medallion](../../14-data-lake/03-medallion-architecture/README.md).

## Exercícios

1. Crie um `stg_pedidos` a partir de uma source e um `fct_vendas` que o referencia com `ref()`.
2. Configure um model como `view` e outro como `table`; explique o trade-off.
3. Use `dbt run --select` para rodar só um model e seus dependentes.
4. Reorganize um model monolítico em staging + intermediate + mart.

## Referências

- Documentação do dbt — Models, Materializations, Model contracts.
- dbt Labs — "How we structure our dbt projects".
