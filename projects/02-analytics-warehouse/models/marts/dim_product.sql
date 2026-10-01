-- SCD tipo 1 (sobrescreve): só o estado atual do produto interessa à análise.
select
    md5(product_id) as product_sk,
    product_id,
    name,
    category,
    list_price
from {{ ref('stg_products') }}

union all

-- "membro desconhecido": FKs ausentes caem aqui em vez de sumirem do fato num join
select md5('unknown'), 'unknown', 'Desconhecido', 'desconhecido', null
