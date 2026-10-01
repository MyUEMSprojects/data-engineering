# SQL analítico

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

Reúne os padrões e recursos de SQL voltados a **analytics** — além do CRUD básico:
agregações multi-nível, pivot/unpivot, séries temporais, coortes, funis. É o SQL que o
Data Engineer e o Analytics Engineer escrevem no dia a dia sobre o
[warehouse](../../13-data-warehouse/README.md).

Pré-requisitos: [agregação](../02-aggregation-grouping/README.md),
[joins](../03-joins/README.md), [CTEs](../04-subqueries-ctes/README.md) e
[window functions](../05-window-functions/README.md).

## GROUPING SETS, ROLLUP e CUBE

Calculam **vários níveis de agregação de uma vez** (subtotais e totais) sem `UNION`.

```sql
SELECT uf, categoria, SUM(valor) AS receita
FROM pedidos
GROUP BY GROUPING SETS ((uf, categoria), (uf), ());
-- ((uf,categoria)) = detalhe; (uf) = subtotal por UF; () = total geral
```

- `ROLLUP(a, b)` — hierárquico: `(a,b)`, `(a)`, `()`.
- `CUBE(a, b)` — todas as combinações: `(a,b)`, `(a)`, `(b)`, `()`.
- `GROUPING(col)` — indica (0/1) se a coluna foi agregada naquela linha (para rotular
  "Total").

Úteis para relatórios com subtotais sem rodar a query N vezes.

## Pivot (linhas → colunas)

SQL padrão não tem `PIVOT`; o idioma portável é **agregação condicional**:

```sql
SELECT
  uf,
  SUM(valor) FILTER (WHERE mes = 1) AS jan,
  SUM(valor) FILTER (WHERE mes = 2) AS fev,
  SUM(valor) FILTER (WHERE mes = 3) AS mar
FROM pedidos
GROUP BY uf;
```

(`SUM(CASE WHEN ... THEN valor END)` é a versão sem `FILTER`.) Alguns bancos têm
`PIVOT` nativo (SQL Server, Snowflake, BigQuery `PIVOT`).

## Unpivot (colunas → linhas)

Normalizar colunas de métricas em pares (chave, valor):

```sql
SELECT uf, 'jan' AS mes, jan AS valor FROM resumo
UNION ALL SELECT uf, 'fev', fev FROM resumo
UNION ALL SELECT uf, 'mar', mar FROM resumo;
-- ou LATERAL/UNNEST, dependendo do banco
```

## Séries temporais e lacunas

Preencher dias sem venda com zero (crucial para médias móveis corretas): gere a
grade de datas e faça `LEFT JOIN`.

```sql
WITH dias AS (
    SELECT generate_series(DATE '2024-01-01', DATE '2024-01-31', '1 day')::date AS dia
)
SELECT d.dia, COALESCE(SUM(p.valor), 0) AS receita
FROM dias d
LEFT JOIN pedidos p ON p.criado_em::date = d.dia
GROUP BY d.dia
ORDER BY d.dia;
```

Crescimento período-a-período com [LAG](../05-window-functions/README.md):

```sql
SELECT mes, receita,
  receita - LAG(receita) OVER (ORDER BY mes) AS variacao,
  ROUND(100.0 * (receita / NULLIF(LAG(receita) OVER (ORDER BY mes), 0) - 1), 1) AS pct
FROM receita_mensal;
```

## Análise de coorte (cohort)

Agrupar usuários pelo mês de aquisição e medir retenção ao longo do tempo:

```sql
WITH primeira_compra AS (
    SELECT cliente_id, DATE_TRUNC('month', MIN(criado_em)) AS coorte
    FROM pedidos GROUP BY cliente_id
),
atividade AS (
    SELECT p.cliente_id, pc.coorte,
           DATE_TRUNC('month', p.criado_em) AS mes_atividade
    FROM pedidos p JOIN primeira_compra pc ON pc.cliente_id = p.cliente_id
)
SELECT coorte,
       (EXTRACT(YEAR FROM mes_atividade) - EXTRACT(YEAR FROM coorte)) * 12
        + (EXTRACT(MONTH FROM mes_atividade) - EXTRACT(MONTH FROM coorte)) AS mes_offset,
       COUNT(DISTINCT cliente_id) AS ativos
FROM atividade
GROUP BY coorte, mes_offset
ORDER BY coorte, mes_offset;
```

## Funil (funnel)

Contar quantos avançaram por cada etapa (ex.: visitou → carrinho → compra):

```sql
SELECT
  COUNT(*) FILTER (WHERE etapa = 'visita')  AS visitas,
  COUNT(*) FILTER (WHERE etapa = 'carrinho') AS carrinhos,
  COUNT(*) FILTER (WHERE etapa = 'compra')   AS compras
FROM eventos;   -- com event time e ordenação por sessão para funis sequenciais
```

## Deduplicação e "última versão" (muito comum em DE)

Padrão `ROW_NUMBER` para pegar o registro mais recente por chave (ver
[dedupe](../../09-etl-elt/09-deduplication/README.md) e
[SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md)):

```sql
WITH r AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) AS rn
  FROM staging_clientes
)
SELECT * FROM r WHERE rn = 1;
```

## Percentis e distribuição

```sql
SELECT
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor) AS mediana,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY valor) AS p95,
  AVG(valor), STDDEV(valor)
FROM pedidos;
```

## Recursos úteis adicionais

- `DISTINCT ON` (Postgres) — pega a primeira linha por grupo diretamente.
- `LATERAL` / `UNNEST` — expandir arrays/JSON em linhas.
- `jsonb` — consultar JSON semiestruturado dentro do SQL.
- `QUALIFY` (Snowflake/BigQuery) — filtra por window function sem CTE externa.

## Erros comuns

- Médias móveis/tendências erradas por **não preencher lacunas** de datas.
- Dividir por zero em variações percentuais (use `NULLIF(denominador, 0)`).
- Pivot *hardcoded* quebrando quando surge uma nova categoria.
- `COUNT(DISTINCT)` caríssimo em alta cardinalidade (considere aproximação).
- Confundir granularidade ao montar funis/coortes (defina a chave de evento/sessão).

## Boas práticas

- Monte análises em **CTEs nomeadas** (estilo dbt) — legível e testável.
- Trate nulos/zeros explicitamente (`COALESCE`, `NULLIF`).
- Prefira window functions a self-joins para comparações temporais.
- Materialize análises recorrentes ([MV](../06-views-materialized-views/README.md)/
  [dbt incremental](../../28-dbt/08-incremental-models/README.md)).

## Relação com outros conceitos

- Roda sobre modelos [dimensionais](../../07-data-modeling/04-dimensional-modeling/README.md)
  no [warehouse](../../13-data-warehouse/README.md).
- Implementado como modelos [dbt](../../28-dbt/README.md).
- Base de métricas para [BI](../../README.md) e
  [features de ML](../../31-data-engineering-and-ml/02-feature-engineering-pipelines/README.md).

## Exercícios

1. Gere um relatório de receita por UF e categoria com subtotais por UF e total geral
   (`GROUPING SETS`).
2. Pivote vendas mensais (meses como colunas) com agregação condicional.
3. Monte uma análise de coorte mensal de retenção de clientes.
4. Calcule o crescimento percentual MoM tratando divisão por zero e meses sem venda.

## Referências

- Documentação do PostgreSQL — "GROUPING SETS", "Window Functions", `PERCENTILE_CONT`.
- Kimball, R. *The Data Warehouse Toolkit* (padrões analíticos).
- Documentação de `PIVOT`/`QUALIFY` de Snowflake/BigQuery.
