{% snapshot snap_customers %}
{{
    config(
        unique_key='customer_id',
        strategy='timestamp',
        updated_at='updated_at',
    )
}}
-- SCD2 automático: toda mudança de atributos gera uma nova versão (dbt_valid_from/to).
-- updated_at em UTC *sem fuso*: é o tipo que o dbt usa nas colunas dbt_valid_from/to (evita o aviso de tipos).
select
    customer_id, name, email, uf, segment,
    (updated_at at time zone 'UTC') as updated_at
from {{ ref('stg_customers') }}
{% endsnapshot %}
