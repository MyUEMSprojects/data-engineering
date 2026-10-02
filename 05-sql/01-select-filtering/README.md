# SELECT e filtragem

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

`SELECT` é a instrução para **consultar** dados. Com `WHERE` (filtrar), `ORDER BY`
(ordenar) e `LIMIT` (limitar), forma a base de toda consulta. É também onde moram as
pegadinhas de **NULL**, que confundem muita gente.

## Anatomia e ordem lógica de execução

Você escreve nesta ordem:

```sql
SELECT   coluna1, coluna2, agg(col3)
FROM     tabela
WHERE    condicao            -- filtra linhas
GROUP BY coluna1, coluna2    -- agrupa
HAVING   condicao_de_grupo   -- filtra grupos
ORDER BY coluna1
LIMIT    100;
```

Mas o banco **executa** em outra ordem lógica — entender isso evita erros:

```text
FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT
```

Por isso você **não pode** usar um *alias* definido no `SELECT` dentro do `WHERE`
(o `WHERE` roda antes do `SELECT`), mas **pode** no `ORDER BY`.

## SELECT básico

```sql
SELECT * FROM clientes;                      -- todas as colunas (evite em produção)
SELECT id, nome, email FROM clientes;        -- colunas específicas (preferir)
SELECT nome AS cliente, criado_em AS desde   -- aliases
FROM clientes;
SELECT DISTINCT uf FROM clientes;            -- valores únicos
SELECT preco * qtd AS total FROM itens;      -- expressões
```

> Evite `SELECT *` em produção/pipelines: traz dados desnecessários (custo de I/O,
> especialmente em [colunar](../../08-data-formats/08-row-vs-columnar/README.md)) e
> quebra quando o schema muda.

## WHERE — filtrando linhas

```sql
SELECT * FROM pedidos
WHERE valor > 100
  AND uf = 'SP'
  AND status IN ('pago', 'enviado')
  AND criado_em >= DATE '2024-01-01'
  AND email LIKE '%@gmail.com'
  AND valor BETWEEN 50 AND 500;
```

Operadores: `= <> < > <= >=`, `AND/OR/NOT`, `IN`, `BETWEEN`, `LIKE`/`ILIKE`
(case-insensitive no Postgres), `~` (regex no Postgres).

## NULL — a maior fonte de erros em SQL

`NULL` significa "desconhecido/ausente", **não** zero nem string vazia. Qualquer
comparação com `NULL` resulta em `UNKNOWN` (nem verdadeiro nem falso):

```sql
WHERE coluna = NULL      -- ERRADO: nunca retorna linhas
WHERE coluna IS NULL     -- CERTO
WHERE coluna IS NOT NULL
```

Consequências práticas:

```sql
-- NULL em NOT IN é traiçoeiro: se a subquery tiver um NULL, o resultado "sume"
WHERE id NOT IN (SELECT cliente_id FROM bloqueados)   -- PERIGO se houver NULL
-- prefira NOT EXISTS (ver subqueries)

-- agregações IGNORAM NULL
SELECT COUNT(*), COUNT(email) FROM clientes;   -- COUNT(email) < COUNT(*) se há nulos

-- tratar NULL
SELECT COALESCE(telefone, 'sem telefone') FROM clientes;  -- 1º não-nulo
SELECT NULLIF(valor, 0) FROM x;                           -- vira NULL se = 0
```

Ordenação: `NULL` vai por último (`ASC`) por padrão no Postgres; controle com
`ORDER BY col NULLS FIRST/LAST`.

## ORDER BY e LIMIT

```sql
SELECT nome, valor FROM pedidos
ORDER BY valor DESC, nome ASC
LIMIT 10 OFFSET 20;          -- paginação (cuidado: OFFSET grande é lento)
```

Para paginar grandes volumes, prefira **keyset pagination** (`WHERE id > :ultimo
ORDER BY id LIMIT 100`) a `OFFSET` alto — ver [otimização](../11-optimization/README.md).

## CASE — lógica condicional

```sql
SELECT nome,
       CASE
         WHEN valor >= 1000 THEN 'alto'
         WHEN valor >= 100  THEN 'medio'
         ELSE 'baixo'
       END AS faixa
FROM pedidos;
```

`CASE` é fundamental para derivar categorias, *flags* e pivôs condicionais (ver
[SQL analítico](../13-analytical-sql/README.md)).

## Tipos, casts e datas

```sql
SELECT valor::numeric(12,2),                 -- cast (sintaxe Postgres)
       CAST(criado_em AS date),
       criado_em AT TIME ZONE 'America/Sao_Paulo'
FROM pedidos;
```

Cuidado com fuso horário (prefira `timestamptz`) e precisão numérica (use
`numeric`/`decimal` para dinheiro, não `float`).

## Erros comuns

- `= NULL` em vez de `IS NULL`.
- `NOT IN` com subquery que contém `NULL` → zero linhas inesperadas.
- `SELECT *` em pipelines.
- Esquecer que `COUNT(col)` ignora nulos (≠ `COUNT(*)`).
- `OFFSET` enorme para paginar (lento).
- Usar alias do `SELECT` no `WHERE`.

## Boas práticas

- Liste colunas explicitamente; nomeie com aliases claros.
- Trate `NULL` conscientemente (`COALESCE`, `IS [NOT] NULL`).
- Filtre o máximo no `WHERE` (menos dados nas etapas seguintes).
- Use `numeric` para dinheiro e `timestamptz` para datas.

## Relação com outros conceitos

- Base para [agregação](../02-aggregation-grouping/README.md),
  [joins](../03-joins/README.md) e todo o resto do módulo.
- Filtros eficientes dependem de [índices](../07-indexes/README.md) e
  [planejamento](../10-query-planning-explain/README.md).

## Exercícios

1. Liste os 10 pedidos de maior valor em SP com status pago, mostrando uma coluna
   `faixa` (alto/médio/baixo) via `CASE`.
2. Conte clientes totais e clientes com e-mail preenchido; explique a diferença.
3. Reescreva um `NOT IN` perigoso de forma segura.
4. Pagine resultados com keyset pagination em vez de `OFFSET`.

## Referências

- Documentação do PostgreSQL — "Queries".
- Winand, M. — seção sobre filtros e índices (use-the-index-luke.com).
