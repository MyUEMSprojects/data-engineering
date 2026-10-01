# Macros e Jinja

> 🔵 Analytics Platforms · Parte de [28 — dbt](../README.md)

## O que é

dbt compila seus arquivos SQL usando **Jinja**, uma linguagem de templating. Isso permite SQL
**dinâmico e reutilizável**: variáveis, condicionais, loops e **macros** (funções SQL reutilizáveis).
É o que torna o dbt DRY (ver [princípios](../../03-git-software-engineering/07-project-organization/README.md))
e poderoso — mas também o que pode torná-lo ilegível se exagerado.

## Jinja no dbt: o básico

```sql
-- expressões {{ }}, statements {% %}, comentários {# #}
select * from {{ ref('stg_pedidos') }}          -- ref() é uma função Jinja!
{% if target.name == 'prod' %}
where created_at >= '2020-01-01'
{% endif %}
```

Na verdade, `ref()`, `source()`, `config()` que você já usa **são Jinja**. O compilador do dbt
resolve o template e gera o SQL final (veja com `dbt compile`).

## Variáveis e `target`

```sql
{% set limite = var('limite_valor', 1000) %}     -- var com default
where valor > {{ limite }}

-- target traz info do ambiente (dev/prod, schema, etc.)
{{ target.schema }}   {{ target.name }}
```

`{{ var('x') }}` lê variáveis do `dbt_project.yml`/linha de comando (`--vars`) — útil para
parametrizar (datas, limites, flags).

## Loops (gerar SQL repetitivo)

```sql
select
  id,
  {% for status in ['pago', 'cancelado', 'aberto'] %}
  sum(case when status = '{{ status }}' then valor end) as valor_{{ status }}{{ "," if not loop.last }}
  {% endfor %}
from {{ ref('fct_vendas') }}
group by id
```

Gera uma coluna por status sem repetir código — um [pivot](../../05-sql/13-analytical-sql/README.md)
dinâmico. Loops sobre listas/resultados de query evitam copiar-colar.

## Macros (funções SQL reutilizáveis)

Definidas em `macros/`, chamadas como funções — o jeito DRY de reusar lógica SQL:

```sql
-- macros/cents_to_reais.sql
{% macro cents_to_reais(coluna) %}
    round({{ coluna }} / 100.0, 2)
{% endmacro %}
```

```sql
select {{ cents_to_reais('valor_cents') }} as valor from {{ ref('stg_pedidos') }}
```

Macros encapsulam lógica repetida (conversões, geração de SQL, testes customizados), inclusive
lidando com **diferenças de dialeto** entre warehouses.

## Pacotes (reutilizar macros de terceiros)

O **dbt Hub** tem pacotes com macros/testes prontos — instale via `packages.yml` + `dbt deps`:

- **`dbt_utils`** — utilidades (surrogate keys, `pivot`, `union_relations`, testes, `date_spine`).
- **`dbt_expectations`** — testes ricos (ver [tests](../05-tests/README.md)).
- Pacotes específicos de fonte/adaptador.

```sql
{{ dbt_utils.generate_surrogate_key(['cliente_id', 'valid_from']) }}   -- surrogate key por hash
{{ dbt_utils.star(from=ref('stg_pedidos'), except=['_loaded_at']) }}   -- seleciona colunas exceto...
```

## Hooks e operations

- **Hooks** (`pre-hook`/`post-hook`, `on-run-start`/`on-run-end`) — SQL executado antes/depois de um
  model ou do run (ex.: grants, logging).
- **`dbt run-operation`** — rodar uma macro como comando (ex.: manutenção).

## O risco: Jinja demais

Jinja é poderoso, mas **SQL coberto de lógica Jinja fica ilegível e difícil de depurar**. Use com
parcimônia (KISS): macros para o que realmente se repete, não para "mostrar esperteza". Sempre dá
para ver o SQL final com `dbt compile`.

## Erros comuns

- Macros complexas demais que ninguém entende (ilegibilidade).
- Lógica de negócio escondida em Jinja em vez de SQL claro.
- Reinventar o que `dbt_utils` já faz (surrogate key, pivot, date spine).
- Não usar `dbt compile`/`--vars` para depurar/parametrizar.

## Boas práticas

- DRY com macros **para o que se repete de verdade**; prefira SQL claro ao invés de Jinja esperto.
- Use `dbt_utils`/`dbt_expectations` em vez de reinventar.
- Parametrize com `var()`/`target` (datas, ambientes); depure com `dbt compile`.
- Documente macros (o que fazem, parâmetros).

## Relação com outros conceitos

- Habilita [models](../02-models/README.md), [tests customizados](../05-tests/README.md),
  [incremental](../08-incremental-models/README.md).
- DRY/[organização](../../03-git-software-engineering/07-project-organization/README.md);
  surrogate keys ([modelagem](../../07-data-modeling/09-surrogate-natural-keys/README.md)).

## Exercícios

1. Escreva uma macro `cents_to_reais` e use-a em dois models.
2. Use um loop Jinja para gerar colunas de `sum(case when...)` por status (pivot dinâmico).
3. Instale `dbt_utils` e use `generate_surrogate_key` e `star`.
4. Rode `dbt compile` e inspecione o SQL gerado de um model com Jinja.

## Referências

- Documentação do dbt — Jinja & macros, Packages, Hooks.
- dbt Hub — `dbt_utils`, `dbt_expectations`.
