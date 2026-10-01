-- SCD tipo 2 construída a partir do snapshot. Uma linha por VERSÃO do cliente.
with versions as (
    select
        customer_id,
        name,
        email,
        uf,
        segment,
        (dbt_valid_from at time zone 'UTC')  as dbt_valid_from,   -- timestamp UTC -> timestamptz
        (dbt_valid_to   at time zone 'UTC')  as dbt_valid_to,
        row_number() over (partition by customer_id order by dbt_valid_from) as version_no
    from {{ ref('snap_customers') }}
)
select
    md5(customer_id || '|' || dbt_valid_from::text)                         as customer_sk,
    customer_id,
    name,
    email,
    uf,
    segment,
    -- 1ª versão vale "desde sempre": fatos anteriores ao 1º snapshot não ficam sem dimensão
    case when version_no = 1 then timestamptz '1900-01-01' else dbt_valid_from end as valid_from,
    coalesce(dbt_valid_to, timestamptz '9999-12-31')                         as valid_to,
    dbt_valid_to is null                                                     as is_current
from versions

union all

select md5('unknown'), 'unknown', 'Desconhecido', null, null, null,
       timestamptz '1900-01-01', timestamptz '9999-12-31', true
