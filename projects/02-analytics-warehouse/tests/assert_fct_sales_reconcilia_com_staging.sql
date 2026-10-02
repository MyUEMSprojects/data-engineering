-- Reconciliação: o fato não pode perder nem multiplicar linhas/valores em relação ao staging
-- (pega fan-out de join e perda por inner join). Retorna linhas SOMENTE se houver divergência.
with f as (select count(*) as n, sum(net_amount) as total from {{ ref('fct_sales') }}),
     s as (select count(*) as n, sum(net_amount) as total from {{ ref('stg_order_items') }})
select f.n as fct_rows, s.n as stg_rows, f.total as fct_total, s.total as stg_total
from f, s
where f.n <> s.n or f.total <> s.total
