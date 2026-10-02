select
    customer_id,
    name,
    lower(email)        as email,
    upper(uf)           as uf,
    lower(segment)      as segment,
    updated_at
from {{ source('raw', 'customers') }}
where customer_id is not null
