-- SCD2 saudável: janelas de vigência de um mesmo cliente não se sobrepõem (senão o join as-of duplicaria linhas).
select a.customer_id, a.valid_from as a_from, a.valid_to as a_to, b.valid_from as b_from
from {{ ref('dim_customer') }} a
join {{ ref('dim_customer') }} b
  on a.customer_id = b.customer_id
 and a.customer_sk <> b.customer_sk
 and a.valid_from < b.valid_to
 and b.valid_from < a.valid_to
