# Exercícios — Módulo 28: dbt

Teoria em [28-dbt](../../28-dbt/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — O que o dbt faz (e não faz)

Em uma frase: o que é o dbt? Que etapa do ELT ele cobre e o que **não** faz?

<details><summary>Gabarito</summary>

Ferramenta de **transformação** (o T do ELT): compila SQL + Jinja em `CREATE TABLE/VIEW` dentro do warehouse, com testes, documentação e linhagem. **Não** extrai/carrega dados nem orquestra por si só (use Fivetran/Airbyte/Airflow). Ver [o que é dbt](../../28-dbt/01-what-is-dbt/README.md).
</details>

## 2. 🟢 Implementação — Modelo e `ref`

Escreva um modelo `stg_orders` que lê de `source('raw','orders')` e um modelo `fct_daily_revenue` que depende dele via `ref`.

<details><summary>Gabarito</summary>

```sql
-- models/staging/stg_orders.sql
SELECT order_id, customer_id, cast(order_date AS date) AS order_date, lower(status) AS status, amount
FROM {{ source('raw', 'orders') }}

-- models/marts/fct_daily_revenue.sql
SELECT order_date, sum(amount) AS revenue
FROM {{ ref('stg_orders') }}
WHERE status <> 'canceled'
GROUP BY 1
```
`ref`/`source` constroem o **DAG** e resolvem o schema por ambiente. Ver [modelos](../../28-dbt/02-models/README.md) e o [Projeto 02](../../projects/02-analytics-warehouse/README.md).
</details>

## 3. 🔵 Implementação — Testes

Declare em YAML: `order_id` único e não nulo, `status` em um conjunto, `customer_id` relacionado a `dim_customer`. Escreva também um **teste singular** (receita não negativa).

<details><summary>Gabarito</summary>

```yaml
models:
  - name: stg_orders
    columns:
      - name: order_id
        data_tests: [unique, not_null]
      - name: status
        data_tests:
          - accepted_values: {arguments: {values: [created, paid, shipped, delivered, canceled]}}
      - name: customer_id
        data_tests:
          - relationships: {arguments: {to: ref('dim_customer'), field: customer_id}}
```
```sql
-- tests/assert_revenue_not_negative.sql  (retorna linhas = falha)
SELECT * FROM {{ ref('fct_daily_revenue') }} WHERE revenue < 0
```
(A sintaxe `arguments:` é a atual do dbt 1.10+.) Ver [testes](../../28-dbt/05-tests/README.md).
</details>

## 4. 🔵 Implementação — Incremental

Torne `fct_events` **incremental** com `delete+insert` por `event_date` e reprocessamento de 3 dias (eventos atrasados).

<details><summary>Gabarito</summary>

```sql
{{ config(materialized='incremental', incremental_strategy='delete+insert', unique_key='event_id') }}
SELECT event_id, cast(event_ts AS date) AS event_date, user_id, amount
FROM {{ ref('stg_events') }}
{% if is_incremental() %}
WHERE cast(event_ts AS date) >= (SELECT max(event_date) - interval '3 days' FROM {{ this }})
{% endif %}
```
O *lookback* de 3 dias absorve atrasos; `unique_key` evita duplicar. Rode `--full-refresh` ao mudar a lógica. Ver [incremental](../../28-dbt/08-incremental-models/README.md).
</details>

## 5. 🟣 Debugging — Snapshot que "inventa" versões

Um snapshot (estratégia `timestamp`) cria uma nova versão a cada execução embora nada tenha mudado. Quais causas prováveis?

<details><summary>Gabarito</summary>

`updated_at` que **muda sempre** (ex.: `now()` no staging, ou reprocessamento que regrava o timestamp), tipos/fuso inconsistentes entre execuções (naïve × UTC), ou `unique_key` errada. Use o timestamp **real** da origem (e normalize para UTC) — foi exatamente o aviso que o [Projeto 02](../../projects/02-analytics-warehouse/README.md) corrigiu. Ver [snapshots](../../28-dbt/04-snapshots/README.md).
</details>

## 6. 🟣 Arquitetura — dbt em produção

Descreva um fluxo de CI/CD para dbt: o que roda no PR, o que roda em produção e como garantir que **só o modificado** seja testado.

<details><summary>Gabarito</summary>

PR: `dbt build --select state:modified+ --defer --state prod-artifacts` em schema efêmero (testa só o impactado, reaproveitando produção), `sqlfluff`, verificação de docs. Merge: *job* de produção agendado/orquestrado (`dbt build`), `source freshness`, artefatos (`manifest.json`) publicados para o próximo `state:`. Alertas em falha de teste. Ver [deployment](../../28-dbt/09-deployment/README.md) e [CI/CD](../../23-cicd-dataops/README.md).
</details>
