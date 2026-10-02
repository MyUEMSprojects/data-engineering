select
    order_id,
    line_no,
    product_id,
    quantity,
    unit_price,
    discount,
    -- métricas aditivas no grão da linha (item do pedido)
    round(quantity * unit_price, 2)                    as gross_amount,
    round(quantity * unit_price * discount, 2)         as discount_amount,
    round(quantity * unit_price * (1 - discount), 2)   as net_amount
from {{ source('raw', 'order_items') }}
