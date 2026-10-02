-- GRÃO: uma linha por ITEM de pedido (order_id + line_no).
-- Cada fato aponta para a versão do cliente VIGENTE NA DATA DO PEDIDO (join "as-of").
select
    i.order_id,
    i.line_no,
    coalesce(d.date_sk, to_char(o.order_date, 'YYYYMMDD')::int)  as date_sk,
    coalesce(c.customer_sk, md5('unknown'))                      as customer_sk,
    coalesce(p.product_sk,  md5('unknown'))                      as product_sk,
    o.status                                                     as order_status,   -- degenerate attr.
    o.order_ts,
    i.quantity,
    i.unit_price,
    i.gross_amount,
    i.discount_amount,
    i.net_amount
from {{ ref('stg_order_items') }} i
join {{ ref('stg_orders') }} o using (order_id)
left join {{ ref('dim_customer') }} c
       on c.customer_id = o.customer_id
      and o.order_ts >= c.valid_from
      and o.order_ts <  c.valid_to
left join {{ ref('dim_product') }} p on p.product_id = i.product_id
left join {{ ref('dim_date') }}    d on d.date_day   = o.order_date
