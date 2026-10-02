# Camada marts

`dim_date`, `dim_product` (SCD1), `dim_customer` (SCD2 sobre o snapshot) e `fct_sales` (grão: item do pedido). `_marts.yml` define testes de unicidade, `relationships` e `accepted_values`.
