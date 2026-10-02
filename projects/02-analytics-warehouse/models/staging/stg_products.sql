select
    product_id,
    name,
    lower(category) as category,
    list_price,
    updated_at
from {{ source('raw', 'products') }}
where product_id is not null
