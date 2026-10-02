# Incremental models

> 🔵 Analytics Platforms · Parte de [28 — dbt](../README.md)

## O que é

Um **modelo incremental** é uma [materialization](../02-models/README.md) do dbt que processa
**apenas os dados novos/alterados** a cada execução, em vez de reconstruir a tabela inteira. É como o
dbt implementa [cargas incrementais](../../09-etl-elt/05-full-vs-incremental/README.md) — essencial
para tabelas grandes (fatos/eventos) onde reprocessar tudo seria lento e caro.

## Por que existe

Materializar um fato de 1 bilhão de linhas como `table` (recriar do zero) a cada run é inviável
(tempo/custo). O incremental processa só o delta (ex.: o dia de hoje), **anexando/mesclando** ao que
já existe — o trade-off clássico full vs incremental (ver
[full vs incremental](../../09-etl-elt/05-full-vs-incremental/README.md)).

## Como funciona

```sql
-- models/marts/fct_eventos.sql
{{ config(materialized='incremental', unique_key='event_id') }}

select *
from {{ ref('stg_eventos') }}
{% if is_incremental() %}
  -- só no modo incremental: filtra o que é novo em relação ao que já está na tabela
  where event_ts > (select max(event_ts) from {{ this }})
{% endif %}
```

- `materialized='incremental'` ativa o modo.
- `is_incremental()` é verdadeiro **exceto** na primeira execução/full-refresh → o `where` filtra o
  delta.
- `{{ this }}` refere-se à própria tabela (o estado atual).
- Na **primeira** run (ou `--full-refresh`), processa tudo; nas seguintes, só o novo.

## Estratégias incrementais

Como o dbt aplica o delta (depende do warehouse):

- **`append`** — só insere as novas linhas (para eventos imutáveis; cuidado com duplicação — ver
  [idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **`merge`** (padrão em muitos adaptadores) — usa `unique_key` para **upsert** (insere novos,
  atualiza existentes) → idempotente. Base para dados mutáveis/[CDC](../../09-etl-elt/06-cdc/README.md).
- **`delete+insert`** — apaga as chaves afetadas e reinsere.
- **`insert_overwrite`** — sobrescreve **partições** inteiras (ótimo para
  [overwrite por partição](../../09-etl-elt/04-loading/README.md), idempotente por janela) — comum em
  BigQuery/Spark.

```sql
{{ config(materialized='incremental', incremental_strategy='insert_overwrite',
          partition_by={'field':'dt','data_type':'date'}) }}
```

## O `unique_key` e idempotência

Com estratégia `merge`/`delete+insert`, o `unique_key` garante que reprocessar os mesmos dados
**não duplica** (upsert). Sem `unique_key` + `append`, reexecutar **duplica** — o erro mais comum em
incrementais. Prefira `merge`/`insert_overwrite` para idempotência (ver
[idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).

## Lookback window (dados tardios)

Filtrar por `event_ts > max(event_ts)` perde [dados tardios](../../09-etl-elt/05-full-vs-incremental/README.md)
(que chegam com timestamp antigo). Use uma **janela de segurança**:

```sql
where event_ts > (select max(event_ts) from {{ this }}) - interval '3 days'
```

Reprocessa os últimos 3 dias (com `merge`/overwrite por partição, não duplica) para capturar
atrasados.

## Full-refresh e backfill

```bash
dbt run --select fct_eventos --full-refresh   # reconstrói do zero (ignora is_incremental)
```

Use `--full-refresh` após mudar a lógica do model ou para [backfill](../../09-etl-elt/08-backfill/README.md).
Para backfill por partição, combine com `insert_overwrite` e filtre o período.

## Quando usar / quando NÃO usar

- **Use** em tabelas **grandes** (fatos/eventos) onde full é caro/lento.
- **NÃO complique** tabelas pequenas (use `table`/`view` — incremental adiciona complexidade e
  risco de bugs sutis). Comece simples; migre para incremental quando o custo/tempo doer.

## Erros comuns

- `append` sem `unique_key` → duplicação ao reexecutar.
- Sem lookback → perde dados tardios.
- Lógica do model mudou e não rodou `--full-refresh` (tabela fica inconsistente com o novo código).
- Incremental em tabela pequena (complexidade desnecessária).
- Esquecer que `is_incremental()` é falso na primeira run (teste os dois caminhos).

## Boas práticas

- Prefira `merge`/`insert_overwrite` (idempotente) a `append` cego.
- Defina `unique_key` e uma **lookback window** para dados tardios.
- `--full-refresh` ao mudar a lógica; combine com partição para backfill.
- Só use incremental quando o full realmente pesar.

## Relação com outros conceitos

- [Full vs incremental](../../09-etl-elt/05-full-vs-incremental/README.md),
  [idempotência](../../09-etl-elt/07-idempotency-retries/README.md),
  [loading](../../09-etl-elt/04-loading/README.md), [backfill](../../09-etl-elt/08-backfill/README.md).
- [Materializations](../02-models/README.md),
  [partitioning do warehouse](../../13-data-warehouse/03-partitioning-clustering/README.md).

## Exercícios

1. Converta um model `table` grande em `incremental` com `is_incremental()` e `unique_key`.
2. Mostre por que `append` sem `unique_key` duplica ao reexecutar e corrija com `merge`.
3. Adicione uma lookback window de 3 dias e explique o que ela resolve.
4. Use `insert_overwrite` por partição e faça um backfill de um dia específico.

## Referências

- Documentação do dbt — Incremental models, incremental strategies.
