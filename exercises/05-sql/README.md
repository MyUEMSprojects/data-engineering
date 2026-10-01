# Exercícios — Módulo 05: SQL

Teoria em [05-sql](../../05-sql/README.md) · [índice de exercícios](../README.md)

Esquema usado em todos os exercícios (PostgreSQL ou DuckDB):

```sql
CREATE TABLE customers (customer_id int PRIMARY KEY, name text, country text, signup_date date);
CREATE TABLE orders    (order_id int PRIMARY KEY, customer_id int, order_date date, status text, amount numeric(10,2));
CREATE TABLE order_items (order_id int, line_no int, product text, qty int, price numeric(10,2), PRIMARY KEY (order_id, line_no));
```

## 1. 🟢 SQL — Filtros e NULL

Liste os pedidos **pagos** (`status = 'paid'`) de 2024 com valor ≥ 100, mais recentes primeiro. Depois: por que `WHERE status <> 'canceled'` **não** retorna pedidos com `status` NULL?

<details><summary>Gabarito</summary>

```sql
SELECT order_id, customer_id, order_date, amount
FROM orders
WHERE status = 'paid' AND order_date >= DATE '2024-01-01' AND order_date < DATE '2025-01-01' AND amount >= 100
ORDER BY order_date DESC;
```

Intervalo **semiaberto** (`>= início AND < próximo ano`) funciona com `date` e `timestamp`. `NULL <> 'canceled'` é `NULL` (desconhecido), não `TRUE` — a linha é descartada. Use `status IS DISTINCT FROM 'canceled'` (PostgreSQL/DuckDB) ou `COALESCE`.
</details>

## 2. 🟢 SQL — Agregação com HAVING

Receita total por país (apenas pedidos pagos), mostrando só países com **mais de 3 clientes distintos**.

<details><summary>Gabarito</summary>

```sql
SELECT c.country, SUM(o.amount) AS revenue, COUNT(DISTINCT o.customer_id) AS customers
FROM orders o JOIN customers c USING (customer_id)
WHERE o.status = 'paid'
GROUP BY c.country
HAVING COUNT(DISTINCT o.customer_id) > 3;
```

`WHERE` filtra **linhas** antes de agrupar; `HAVING` filtra **grupos** depois.
</details>

## 3. 🔵 SQL — Clientes sem pedidos (anti-join)

Liste os clientes que **nunca** compraram. Mostre **duas** formas e diga qual cuidado `NOT IN` exige.

<details><summary>Gabarito</summary>

```sql
SELECT c.* FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);
-- ou
SELECT c.* FROM customers c LEFT JOIN orders o USING (customer_id) WHERE o.order_id IS NULL;
```

`NOT IN (SELECT customer_id FROM orders)` **retorna vazio** se a subconsulta tiver **um único NULL** (comparação com NULL é desconhecida). `NOT EXISTS` não tem essa armadilha.
</details>

## 4. 🔵 SQL — Janela: maior pedido por cliente e total acumulado

(a) O **pedido de maior valor** de cada cliente (empate: o mais recente). (b) Total acumulado de receita por mês.

<details><summary>Gabarito</summary>

```sql
-- (a)
SELECT * FROM (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC, order_date DESC) AS rn
  FROM orders o
) t WHERE rn = 1;

-- (b)
SELECT month, revenue, SUM(revenue) OVER (ORDER BY month) AS running_total
FROM (SELECT date_trunc('month', order_date) AS month, SUM(amount) AS revenue FROM orders GROUP BY 1) m;
```

`ROW_NUMBER` desempata de forma determinística (`RANK` devolveria empates). No PostgreSQL, `DISTINCT ON (customer_id) ... ORDER BY customer_id, amount DESC` é uma alternativa específica (não padrão SQL).
</details>

## 5. 🟣 Debugging — A receita que dobrou

```sql
SELECT o.order_id, SUM(o.amount) AS revenue
FROM orders o JOIN order_items i ON i.order_id = o.order_id
GROUP BY o.order_id;
```

Um pedido de R$ 100 com 3 itens aparece como R$ 300. Explique e corrija de **duas** formas.

<details><summary>Gabarito</summary>

**Fan-out**: `orders` (1) × `order_items` (N) repete `o.amount` N vezes e o `SUM` multiplica. Correções: (1) **agregue antes de juntar** — `SELECT o.order_id, o.amount FROM orders o` (sem join) ou junte com `(SELECT order_id, SUM(qty*price) total FROM order_items GROUP BY 1)`;
(2) some no **grão correto**: `SUM(i.qty * i.price)` (receita pelos itens) em vez de `o.amount`. Regra: conheça o **grão** de cada tabela antes do join. Ver [joins](../../05-sql/03-joins/README.md).
</details>

## 6. 🟣 SQL — Ilhas: sequências de dias consecutivos

Para cada cliente, ache os **períodos contínuos** de dias com pelo menos um pedido (início, fim, nº de dias).

<details><summary>Gabarito</summary>

```sql
WITH days AS (SELECT DISTINCT customer_id, order_date AS d FROM orders),
g AS (
  SELECT customer_id, d, d - CAST(ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY d) AS int) AS grp
  FROM days
)
SELECT customer_id, MIN(d) AS start_date, MAX(d) AS end_date, COUNT(*) AS days
FROM g GROUP BY customer_id, grp ORDER BY customer_id, start_date;
```

Truque *gaps and islands*: em dias consecutivos, `d − row_number` é **constante**; ao quebrar a sequência, o valor muda. Ver [SQL analítico](../../05-sql/13-analytical-sql/README.md).
</details>
