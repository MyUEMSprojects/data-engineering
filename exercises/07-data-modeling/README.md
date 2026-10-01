# Exercícios — Módulo 07: Modelagem de dados

Teoria em [07-data-modeling](../../07-data-modeling/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Defina o grão

Para um fato de vendas, qual é o **grão** mais útil: "pedido", "item do pedido" ou "venda diária por loja"? Que métricas cada um suporta?

<details><summary>Gabarito</summary>

**Item do pedido** é o grão mais detalhado: suporta análise por produto, e métricas **aditivas** (`quantidade`, `valor`). "Pedido" perde o produto; "venda diária por loja" é um agregado — não responde "qual produto?". Regra: modele no **menor grão necessário** e agregue depois. Ver [tabelas fato](../../07-data-modeling/07-fact-tables/README.md).
</details>

## 2. 🟢 Conceitual — Aditivo, semi-aditivo, não aditivo

Classifique: (a) quantidade vendida; (b) saldo de conta no fim do dia; (c) preço unitário; (d) margem percentual.

<details><summary>Gabarito</summary>

(a) **aditiva**. (b) **semi-aditiva** — soma entre contas, **não** ao longo do tempo (use último/média). (c) **não aditiva** — some `qtd × preço`, nunca o preço. (d) **não aditiva** — guarde numerador/denominador e calcule a razão depois.
</details>

## 3. 🔵 Implementação — Star schema de uma locadora

Modele um star schema para "locações de filmes": defina o fato, as dimensões, o grão e as chaves. Liste **uma** dimensão degenerada e **uma** *role-playing*.

<details><summary>Gabarito (um caminho)</summary>

**Fato** `fct_rental` (grão: 1 locação por filme): `rental_id` (degenerada), FKs `date_rented_sk`, `date_returned_sk` (**role-playing**: a mesma `dim_date` usada duas vezes), `customer_sk`, `film_sk`, `store_sk`; métricas `rental_fee`, `days_rented`, `late_fee`.
**Dimensões:** `dim_date`, `dim_customer`, `dim_film` (categoria, classificação), `dim_store`. Ver [star schema](../../07-data-modeling/05-star-schema/README.md).
</details>

## 4. 🔵 SQL — SCD tipo 2 na mão

`dim_customer` tem `(customer_sk, customer_id, country, valid_from, valid_to, is_current)`. O cliente 7 mudou de `BR` para `PT` em 2024-05-01. Escreva as instruções para **fechar** a versão antiga e **inserir** a nova.

<details><summary>Gabarito</summary>

```sql
BEGIN;
UPDATE dim_customer
   SET valid_to = DATE '2024-05-01', is_current = false
 WHERE customer_id = 7 AND is_current;

INSERT INTO dim_customer (customer_sk, customer_id, country, valid_from, valid_to, is_current)
VALUES (nextval('dim_customer_sk_seq'), 7, 'PT', DATE '2024-05-01', DATE '9999-12-31', true);
COMMIT;
```
Janela **semiaberta** `[valid_from, valid_to)`: sem sobreposição. Tudo numa **transação**. Na prática use `dbt snapshot` ou `MERGE` ([Projeto 02](../../projects/02-analytics-warehouse/README.md)). Ver [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md).
</details>

## 5. 🟣 Debugging — A dimensão que duplica o fato

Depois de ligar `fct_sales` a `dim_customer` (SCD2) por `customer_id`, a receita total **aumentou**. Por quê e como ligar corretamente?

<details><summary>Gabarito</summary>

Juntar por `customer_id` casa o fato com **todas as versões** do cliente (fan-out). A ligação correta é **temporal**: `ON f.customer_id = d.customer_id AND f.order_ts >= d.valid_from AND f.order_ts < d.valid_to` — ou, melhor, gravar a **surrogate key** da versão no fato já na carga. Teste de reconciliação: `count(*)` e `sum(valor)` do fato devem **igualar** os da origem.
</details>

## 6. 🟣 Arquitetura — Kimball × Data Vault

Uma empresa integra 12 sistemas fonte que mudam o tempo todo e precisa de auditoria total, mas também de relatórios rápidos. Qual a combinação de modelagem e por quê?

<details><summary>Gabarito</summary>

**Data Vault** (hubs, links, satélites) na camada integrada: absorve mudanças de fonte, guarda histórico completo e rastreabilidade (`load_date`, `record_source`). Por cima, **marts dimensionais (Kimball)** para consumo rápido em BI. Custo: mais tabelas/joins e complexidade; só compensa com muitas fontes voláteis e requisitos de auditoria. Ver [Data Vault](../../07-data-modeling/11-data-vault/README.md).
</details>
