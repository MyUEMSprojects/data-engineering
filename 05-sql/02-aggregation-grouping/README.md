# Agregação e GROUP BY

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

Agregação resume muitas linhas em um valor: soma, média, contagem. `GROUP BY` divide
as linhas em grupos e aplica a agregação **por grupo**. É o coração do SQL analítico
— "faturamento por região", "pedidos por cliente".

## Funções de agregação

```sql
SELECT
  COUNT(*)              AS total_linhas,     -- conta linhas
  COUNT(email)          AS com_email,        -- conta não-nulos (ignora NULL!)
  COUNT(DISTINCT uf)    AS ufs_distintas,
  SUM(valor)            AS receita,
  AVG(valor)            AS ticket_medio,
  MIN(valor), MAX(valor),
  STRING_AGG(nome, ', ') AS nomes            -- concatena (Postgres)
FROM pedidos;
```

Ponto crítico: **agregações ignoram `NULL`** (exceto `COUNT(*)`). `AVG` divide pela
contagem de **não-nulos**, não pelo total de linhas.

## GROUP BY

```sql
SELECT uf, COUNT(*) AS pedidos, SUM(valor) AS receita
FROM pedidos
GROUP BY uf
ORDER BY receita DESC;
```

**Regra fundamental:** toda coluna no `SELECT` que **não** está dentro de uma função
de agregação **precisa** estar no `GROUP BY`. (O Postgres permite exceção se a coluna
for funcionalmente dependente de uma PK já agrupada.)

```sql
-- ERRADO: nome não está no GROUP BY nem agregado
SELECT uf, nome, SUM(valor) FROM pedidos GROUP BY uf;
-- CERTO
SELECT uf, SUM(valor) FROM pedidos GROUP BY uf;
```

Agrupar por várias colunas:

```sql
SELECT uf, EXTRACT(YEAR FROM criado_em) AS ano, SUM(valor)
FROM pedidos
GROUP BY uf, ano;        -- Postgres aceita alias/posição no GROUP BY
```

## HAVING — filtrar grupos

`WHERE` filtra **linhas** (antes de agrupar); `HAVING` filtra **grupos** (depois de
agregar).

```sql
SELECT cliente_id, SUM(valor) AS total
FROM pedidos
WHERE status = 'pago'        -- filtra linhas antes
GROUP BY cliente_id
HAVING SUM(valor) > 10000;   -- filtra grupos depois
```

Erro clássico: tentar usar agregação no `WHERE` (`WHERE SUM(valor) > 100` é inválido
— use `HAVING`).

## WHERE vs HAVING (quando usar cada)

```text
filtra ANTES de agregar  → WHERE   (mais eficiente: reduz o que será agrupado)
filtra DEPOIS de agregar → HAVING  (só quando a condição envolve a agregação)
```

Prefira `WHERE` sempre que possível — filtrar cedo processa menos dados.

## COUNT: *, 1, coluna, DISTINCT

```sql
COUNT(*)            -- todas as linhas (inclui as com NULL)
COUNT(coluna)       -- linhas onde coluna IS NOT NULL
COUNT(DISTINCT col) -- valores distintos não-nulos
```

`COUNT(*)` e `COUNT(1)` são equivalentes em performance nos bancos modernos.

## Agregação com FILTER (elegante)

Postgres permite agregar condicionalmente sem `CASE`:

```sql
SELECT
  COUNT(*) FILTER (WHERE status = 'pago')      AS pagos,
  COUNT(*) FILTER (WHERE status = 'cancelado') AS cancelados,
  SUM(valor) FILTER (WHERE uf = 'SP')          AS receita_sp
FROM pedidos;
```

Equivalente portátil: `SUM(CASE WHEN status='pago' THEN 1 ELSE 0 END)`.

## Agregação sem GROUP BY

Sem `GROUP BY`, a agregação cobre a tabela inteira (um grupo só):

```sql
SELECT COUNT(*), SUM(valor) FROM pedidos;   -- uma linha de resultado
```

## Ligação com window functions

`GROUP BY` **colapsa** linhas (uma por grupo). Quando você quer a agregação **sem
perder as linhas individuais** (ex.: valor de cada pedido + total do cliente na mesma
linha), use [window functions](../05-window-functions/README.md) com `OVER
(PARTITION BY ...)`.

## Performance

- `GROUP BY` pode exigir ordenação/hash de muitos dados — veja o plano com
  [EXPLAIN](../10-query-planning-explain/README.md).
- Filtrar no `WHERE` antes reduz o custo.
- `COUNT(DISTINCT)` em alta cardinalidade é caro; em warehouses há
  `APPROX_COUNT_DISTINCT` (HyperLogLog) quando aproximação serve.

## Erros comuns

- Coluna no `SELECT` fora do `GROUP BY` e sem agregação.
- Usar agregação no `WHERE` (deve ser `HAVING`).
- Esquecer que agregações ignoram `NULL` (`AVG` enganoso).
- Confundir `COUNT(*)` com `COUNT(coluna)`.

## Boas práticas

- Filtre no `WHERE`, agrupe, filtre grupos no `HAVING`.
- Use `FILTER`/`CASE` para métricas condicionais.
- Nomeie as métricas com aliases claros.
- Cuidado com nulos ao calcular médias/percentuais.

## Relação com outros conceitos

- Precede [JOINs](../03-joins/README.md) e [window functions](../05-window-functions/README.md).
- Base do [SQL analítico](../13-analytical-sql/README.md) e da
  [modelagem dimensional](../../07-data-modeling/04-dimensional-modeling/README.md).

## Exercícios

1. Receita e ticket médio por UF e ano, só para pedidos pagos, ordenado por receita.
2. Clientes com soma de compras acima de 10 mil (`HAVING`).
3. Em uma consulta só, conte pedidos pagos, cancelados e enviados usando `FILTER`.
4. Explique por que `AVG(bonus)` pode enganar quando muitos `bonus` são `NULL`.

## Referências

- Documentação do PostgreSQL — "Aggregate Functions", `FILTER`, `GROUP BY`.
