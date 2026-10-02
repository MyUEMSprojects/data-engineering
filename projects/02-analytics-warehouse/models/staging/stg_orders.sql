select
    order_id,
    customer_id,
    order_ts,
    (order_ts at time zone 'UTC')::date as order_date,
    lower(status)                       as status,
    updated_at
from {{ source('raw', 'orders') }}
where order_id is not null
