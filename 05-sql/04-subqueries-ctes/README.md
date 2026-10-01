# Subqueries e CTEs

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

- **Subquery** — uma consulta dentro de outra.
- **CTE (Common Table Expression)** — uma subquery nomeada, definida com `WITH`, que
  deixa consultas complexas legíveis e permite reaproveitamento e recursão.

Ambas permitem compor a lógica em etapas, como uma "variável temporária" de query.

## Tipos de subquery

### Escalar (retorna um valor)

```sql
SELECT nome, valor,
       valor - (SELECT AVG(valor) FROM pedidos) AS desvio_da_media
FROM pedidos;
```

### Em lista (`IN`)

```sql
SELECT * FROM clientes
WHERE id IN (SELECT cliente_id FROM pedidos WHERE valor > 1000);
```

### Correlacionada (depende da linha externa)

```sql
SELECT c.nome
FROM clientes c
WHERE EXISTS (SELECT 1 FROM pedidos p
              WHERE p.cliente_id = c.id);   -- referencia c (externa)
```

A subquery correlacionada é avaliada "por linha" conceitualmente — o planejador
costuma otimizá-la, mas cuidado com casos que viram `O(n²)`.

### Na cláusula FROM (derived table)

```sql
SELECT uf, total
FROM (SELECT uf, SUM(valor) AS total FROM pedidos GROUP BY uf) t
WHERE total > 100000;
```

## EXISTS vs IN vs JOIN

Três formas de expressar "clientes com pedidos". Diferenças importam:

```sql
-- IN
WHERE id IN (SELECT cliente_id FROM pedidos)
-- EXISTS (semi-join) — seguro com NULL, geralmente ótimo
WHERE EXISTS (SELECT 1 FROM pedidos p WHERE p.cliente_id = c.id)
-- JOIN — pode multiplicar linhas se cliente tem vários pedidos (cuidado)
```

- **`NOT IN` é perigoso com NULL**: se a subquery retorna algum `NULL`, `NOT IN` não
  retorna nada. **Prefira `NOT EXISTS`** para negação.
- Nos bancos modernos, `IN`/`EXISTS`/`JOIN` costumam ser otimizados de forma
  semelhante; escolha pela clareza e pela semântica (evitar fan-out/NULL).

## CTEs — `WITH`

CTEs transformam uma consulta aninhada ilegível em etapas nomeadas:

```sql
WITH pagos AS (
    SELECT * FROM pedidos WHERE status = 'pago'
),
receita_por_cliente AS (
    SELECT cliente_id, SUM(valor) AS total
    FROM pagos
    GROUP BY cliente_id
)
SELECT c.nome, r.total
FROM receita_por_cliente r
JOIN clientes c ON c.id = r.cliente_id
WHERE r.total > 10000
ORDER BY r.total DESC;
```

Vantagens:

- **Legibilidade** — leia de cima para baixo, etapa a etapa.
- **Reuso** — referencie a mesma CTE várias vezes.
- **Modularidade** — base do estilo de [dbt](../../28-dbt/README.md).

> **Materialização:** historicamente, CTEs no PostgreSQL eram "fences" de otimização
> (materializadas), o que podia piorar a performance. Desde o **PostgreSQL 12**, CTEs
> não-recursivas e usadas uma vez podem ser *inlined* pelo planejador; use `MATERIALIZED`
> / `NOT MATERIALIZED` para controlar. Em outros bancos o comportamento varia.

## CTE recursiva

Para hierarquias (org charts, categorias, grafos) e séries geradas:

```sql
WITH RECURSIVE subordinados AS (
    -- caso base
    SELECT id, nome, gerente_id, 1 AS nivel
    FROM funcionarios
    WHERE id = 10                    -- começa num gerente
  UNION ALL
    -- passo recursivo
    SELECT f.id, f.nome, f.gerente_id, s.nivel + 1
    FROM funcionarios f
    JOIN subordinados s ON f.gerente_id = s.id
)
SELECT * FROM subordinados;
```

Gerar uma série de datas (útil para preencher lacunas em séries temporais):

```sql
WITH RECURSIVE dias AS (
    SELECT DATE '2024-01-01' AS d
  UNION ALL
    SELECT d + 1 FROM dias WHERE d < DATE '2024-01-31'
)
SELECT d FROM dias;
-- (no Postgres, generate_series() é mais simples para isso)
```

Cuidado: recursão sem condição de parada = loop infinito.

## Subquery vs CTE vs View vs Temp table

| Construção | Escopo | Uso |
| --- | --- | --- |
| Subquery | dentro da query | lógica pontual |
| CTE | a mesma query | legibilidade, reuso, recursão |
| [View](../06-views-materialized-views/README.md) | persistente | abstração reutilizável |
| Temp table | sessão | materializar um intermediário caro |

## Erros comuns

- `NOT IN` com subquery que contém `NULL` → zero resultados.
- Subquery correlacionada custosa que vira `O(n²)` (verifique o plano).
- CTE recursiva sem condição de parada.
- Assumir que CTE sempre materializa (varia por banco/versão).

## Boas práticas

- Use **CTEs** para quebrar consultas complexas em etapas nomeadas.
- Prefira `NOT EXISTS` a `NOT IN` para negação.
- Nomeie CTEs descritivamente (viram a documentação da lógica).
- Verifique o [plano](../10-query-planning-explain/README.md) em CTEs/subqueries
  pesadas.

## Relação com outros conceitos

- Estilo modular de CTEs é a base de [dbt](../../28-dbt/README.md).
- Alternativa persistente: [views](../06-views-materialized-views/README.md).
- Semi/anti-join conecta a [JOINs](../03-joins/README.md).

## Exercícios

1. Reescreva uma subquery aninhada de 3 níveis como CTEs legíveis.
2. Liste clientes sem pedidos usando `NOT EXISTS` e explique por que é melhor que
   `NOT IN` aqui.
3. Use uma CTE recursiva para listar toda a cadeia de subordinados de um gerente.
4. Gere todas as datas de um mês e faça `LEFT JOIN` com vendas para preencher dias
   sem venda com zero.

## Referências

- Documentação do PostgreSQL — "WITH Queries (CTEs)".
- PostgreSQL 12 release notes (inlining de CTEs).
