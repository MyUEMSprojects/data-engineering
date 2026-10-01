# Window functions

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

Window functions calculam valores sobre um **conjunto de linhas relacionadas (a
"janela")** **sem colapsar as linhas** — diferente do `GROUP BY`, que reduz cada grupo
a uma linha. Você mantém o detalhe e, ao lado, obtém agregados/rankings/comparações.

São uma das ferramentas mais poderosas e subutilizadas do SQL. Para DE, resolvem
elegantemente: ranking, *running totals*, deduplicação, comparação com linha anterior,
percentis.

## A anatomia: `OVER (PARTITION BY ... ORDER BY ... frame)`

```sql
funcao() OVER (
    PARTITION BY coluna      -- divide em grupos (opcional); sem isso, tudo é 1 janela
    ORDER BY   coluna        -- ordena dentro da janela (necessário p/ ranking/running)
    ROWS BETWEEN ...         -- frame: quais linhas entram (opcional)
)
```

- **`PARTITION BY`** — como `GROUP BY`, mas sem colapsar (reinicia o cálculo por
  grupo).
- **`ORDER BY`** — define a ordem dentro da janela (essencial para ranking e
  acumulados).
- **frame** — subconjunto de linhas da janela relativo à linha atual.

## GROUP BY vs window (a diferença visual)

```text
GROUP BY uf:                  window SUM OVER (PARTITION BY uf):
uf | total                    id | uf | valor | total_uf
SP | 300                      1  | SP | 100   | 300
RJ | 150                      2  | SP | 200   | 300
                              3  | RJ | 150   | 150
(colapsa)                     (mantém as linhas + agregado ao lado)
```

```sql
SELECT id, uf, valor,
       SUM(valor) OVER (PARTITION BY uf) AS total_uf,
       valor::numeric / SUM(valor) OVER (PARTITION BY uf) AS share_uf
FROM pedidos;
```

## Funções de ranking

```sql
SELECT nome, uf, valor,
  ROW_NUMBER() OVER (PARTITION BY uf ORDER BY valor DESC) AS rn,
  RANK()       OVER (PARTITION BY uf ORDER BY valor DESC) AS rnk,
  DENSE_RANK() OVER (PARTITION BY uf ORDER BY valor DESC) AS drnk,
  NTILE(4)     OVER (ORDER BY valor) AS quartil
FROM pedidos;
```

- `ROW_NUMBER` — 1,2,3,... único (desempata arbitrariamente).
- `RANK` — empates compartilham posição e **pulam** a seguinte (1,1,3).
- `DENSE_RANK` — empates compartilham e **não pulam** (1,1,2).
- `NTILE(n)` — divide em n baldes (quartis, decis).

### Padrão "top-N por grupo" (o mais útil)

```sql
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY uf ORDER BY valor DESC) AS rn
    FROM pedidos
)
SELECT * FROM ranked WHERE rn <= 3;    -- 3 maiores pedidos por UF
```

### Deduplicação (manter 1 por chave)

```sql
WITH d AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY email ORDER BY atualizado_em DESC) AS rn
    FROM clientes
)
SELECT * FROM d WHERE rn = 1;          -- registro mais recente por e-mail
```

Padrão onipresente em [ETL](../../09-etl-elt/09-deduplication/README.md) e
[CDC](../../09-etl-elt/06-cdc/README.md).

## Funções de deslocamento (comparar com vizinhos)

```sql
SELECT mes, receita,
  LAG(receita)  OVER (ORDER BY mes) AS mes_anterior,
  LEAD(receita) OVER (ORDER BY mes) AS mes_seguinte,
  receita - LAG(receita) OVER (ORDER BY mes) AS variacao
FROM receita_mensal;
```

`LAG`/`LEAD` acessam a linha anterior/seguinte — base de crescimento MoM, diffs,
detecção de mudanças.

## Running totals e frames

```sql
SELECT dia, valor,
  SUM(valor) OVER (ORDER BY dia
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS acumulado,
  AVG(valor) OVER (ORDER BY dia
                   ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS media_movel_7d
FROM vendas_diarias;
```

Frames:

- `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — do início até a linha atual
  (*running total*).
- `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` — janela móvel de 7 linhas.
- `RANGE` vs `ROWS`: `ROWS` conta linhas físicas; `RANGE` agrupa valores iguais do
  `ORDER BY` (atenção à diferença).

`FIRST_VALUE`/`LAST_VALUE`/`NTH_VALUE` pegam valores de posições da janela.

## WINDOW nomeada (reuso)

```sql
SELECT id,
  SUM(valor) OVER w,
  AVG(valor) OVER w
FROM pedidos
WINDOW w AS (PARTITION BY uf ORDER BY criado_em);
```

## Onde a window roda (ordem lógica)

Window functions são avaliadas **depois** de `WHERE`/`GROUP BY`/`HAVING` e **antes**
de `ORDER BY` final. Por isso você **não pode** filtrar por uma window no `WHERE` —
envolva em CTE/subquery e filtre fora (como no padrão top-N acima).

## Erros comuns

- Tentar filtrar `WHERE row_number = 1` (inválido) — precisa de CTE/subquery.
- Esquecer `ORDER BY` dentro do `OVER` em funções que dependem de ordem.
- Confundir `RANK` (pula) com `DENSE_RANK` (não pula) com `ROW_NUMBER` (único).
- `LAST_VALUE` sem frame adequado retorna a linha atual, não o fim da janela.
- Esperar que window colapse linhas (ela não colapsa).

## Boas práticas

- Use `ROW_NUMBER` + CTE para top-N e deduplicação.
- Defina frames explicitamente em acumulados/médias móveis.
- Nomeie janelas repetidas com `WINDOW`.
- Prefira window a self-joins para comparações entre linhas (mais rápido e claro).

## Relação com outros conceitos

- Complementa [agregação/GROUP BY](../02-aggregation-grouping/README.md).
- Essencial em [dedupe/CDC](../../09-etl-elt/09-deduplication/README.md) e
  [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md).
- Base do [SQL analítico](../13-analytical-sql/README.md).

## Exercícios

1. Liste os 3 maiores pedidos por UF (top-N por grupo).
2. Deduplique clientes mantendo o registro mais recente por e-mail.
3. Calcule a variação percentual de receita mês a mês com `LAG`.
4. Calcule *running total* e média móvel de 7 dias das vendas diárias.

## Referências

- Documentação do PostgreSQL — "Window Functions".
- Winand, M. — capítulo sobre window functions (modern-sql.com).
