-- SCD2 saudável: exatamente uma versão atual por cliente.
select customer_id, count(*) filter (where is_current) as n_current
from {{ ref('dim_customer') }}
group by customer_id
having count(*) filter (where is_current) <> 1
