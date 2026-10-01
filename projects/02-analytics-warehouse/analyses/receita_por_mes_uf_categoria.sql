-- Receita líquida por mês, UF DO CLIENTE NA ÉPOCA do pedido (SCD2) e categoria.
select
    d.year_month,
    c.uf,
    p.category,
    count(distinct f.order_id)  as pedidos,
    sum(f.net_amount)           as receita_liquida
from {{ ref('fct_sales') }} f
join {{ ref('dim_date') }}     d using (date_sk)
join {{ ref('dim_customer') }} c using (customer_sk)
join {{ ref('dim_product') }}  p using (product_sk)
where f.order_status <> 'canceled'
group by 1, 2, 3
order by 1, 2, 3
