# Índices

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

Um **índice** é uma estrutura de dados auxiliar que acelera a busca de linhas por
determinadas colunas — como o índice remissivo de um livro, que evita ler página por
página. Sem índice, o banco faz *full table scan* (lê tudo); com índice, vai direto
às linhas relevantes.

## Por que importa (e o trade-off)

Índices são a principal alavanca de performance de leitura em bancos OLTP e muito úteis
em analytics. Mas **não são grátis**:

- Ocupam espaço em disco.
- **Toda escrita** (`INSERT`/`UPDATE`/`DELETE`) precisa atualizar os índices → escritas
  mais lentas.
- Índices demais degradam escrita e confundem o planejador.

Logo: índice é um **trade-off leitura × escrita × espaço**. Crie com intenção.

## B-tree: o índice padrão

O índice *B-tree* (árvore balanceada) é o default e serve à maioria dos casos:
igualdade (`=`), faixas (`<`, `>`, `BETWEEN`), ordenação (`ORDER BY`) e `LIKE 'abc%'`
(prefixo).

```sql
CREATE INDEX idx_pedidos_cliente ON pedidos (cliente_id);
CREATE INDEX idx_pedidos_data ON pedidos (criado_em);
```

Agora `WHERE cliente_id = 42` e `WHERE criado_em >= '2024-01-01'` podem usar o índice
em vez de varrer a tabela.

## Índices compostos (multi-coluna) e a regra do prefixo

```sql
CREATE INDEX idx_pedidos_uf_data ON pedidos (uf, criado_em);
```

A **ordem das colunas importa**. Esse índice serve a:

- `WHERE uf = 'SP'`
- `WHERE uf = 'SP' AND criado_em > '2024-01-01'`

Mas **não** serve bem a `WHERE criado_em > '...'` sozinho (a coluna líder é `uf`).
Regra: coloque primeiro as colunas usadas em **igualdade**, depois as de **faixa**.

## Índices únicos, parciais e de expressão

```sql
CREATE UNIQUE INDEX uq_clientes_email ON clientes (email);     -- garante unicidade
CREATE INDEX idx_pedidos_abertos ON pedidos (criado_em)
  WHERE status = 'aberto';                                     -- parcial (só subconjunto)
CREATE INDEX idx_clientes_lower_email ON clientes (LOWER(email));  -- de expressão
```

- **Único** — impõe unicidade (base de PK/UNIQUE — ver [constraints](../09-constraints/README.md)).
- **Parcial** — indexa só as linhas que interessam (menor, mais rápido) — ótimo para
  filtros recorrentes.
- **De expressão** — permite usar índice com `WHERE LOWER(email) = ...`.

## Covering index e index-only scan

Se o índice **contém todas as colunas** da consulta, o banco responde sem tocar na
tabela (*index-only scan*):

```sql
CREATE INDEX idx_cov ON pedidos (cliente_id) INCLUDE (valor);  -- Postgres
-- SELECT valor FROM pedidos WHERE cliente_id = 42;  -> index-only
```

## Outros tipos (Postgres)

| Tipo | Para quê |
| --- | --- |
| **B-tree** | padrão: igualdade, faixa, ordenação |
| **Hash** | só igualdade (`=`); nicho |
| **GIN** | busca em `jsonb`, arrays, full-text |
| **GiST/SP-GiST** | dados geométricos/espaciais, ranges |
| **BRIN** | tabelas enormes e naturalmente ordenadas (ex.: por data) — índice minúsculo |

`BRIN` é especialmente útil em DE: em tabelas gigantes ordenadas por tempo, um índice
BRIN em `criado_em` ocupa quase nada e acelera filtros por faixa de data.

## Como saber se o índice é usado

Use [`EXPLAIN ANALYZE`](../10-query-planning-explain/README.md): procure por `Index
Scan`/`Index Only Scan` (bom) vs `Seq Scan` (varredura total). O planejador só usa o
índice se achar que vale a pena (seletividade).

```sql
EXPLAIN ANALYZE SELECT * FROM pedidos WHERE cliente_id = 42;
```

## Quando o índice NÃO ajuda (ou atrapalha)

- Coluna de **baixa seletividade** (ex.: `status` com 2 valores em 50/50) — varrer pode
  ser mais rápido.
- Funções/transformações na coluna sem índice de expressão: `WHERE LOWER(email)=...`
  não usa índice em `email`.
- `LIKE '%abc'` (curinga à esquerda) — B-tree não ajuda (use trigram/GIN).
- Tabelas pequenas — *seq scan* é trivial.
- Em [warehouses colunares](../../13-data-warehouse/README.md) (BigQuery/Snowflake) o
  conceito muda: não há índices B-tree tradicionais; a performance vem de
  **particionamento, clustering e armazenamento colunar**.

## Manutenção

- Índices **fragmentam/incham** com o tempo; `REINDEX` quando necessário.
- Rode `ANALYZE` para manter estatísticas atualizadas (o planejador depende delas).
- `CREATE INDEX CONCURRENTLY` cria sem travar escritas (produção).
- Remova índices **não usados** (consulte `pg_stat_user_indexes`).

## Erros comuns

- Indexar tudo "por garantia" → escritas lentas, espaço desperdiçado.
- Ordem errada em índice composto (coluna de faixa antes da de igualdade).
- Esperar índice em coluna envolvida por função.
- Esquecer `ANALYZE` → planejador escolhe mal.
- Tratar warehouse colunar como OLTP (criar "índices" que não existem lá).

## Boas práticas

- Indexe colunas de `JOIN`, `WHERE` e `ORDER BY` frequentes e seletivas.
- Prefira índices compostos alinhados às consultas reais.
- Use parciais/covering para casos quentes.
- Meça com `EXPLAIN`; remova índices ociosos.

## Relação com outros conceitos

- Diagnóstico via [query planning/EXPLAIN](../10-query-planning-explain/README.md).
- Aplicados em [otimização](../11-optimization/README.md).
- Base física de [PK/UNIQUE](../09-constraints/README.md).
- Em analytics: [partitioning/clustering](../../13-data-warehouse/03-partitioning-clustering/README.md).

## Exercícios

1. Crie um índice que acelere `WHERE uf = ? AND criado_em BETWEEN ? AND ?` e confirme
   com `EXPLAIN ANALYZE`.
2. Mostre, com um exemplo, por que `WHERE LOWER(email) = ...` não usa índice em `email`
   e corrija com índice de expressão.
3. Crie um índice parcial para pedidos com `status = 'aberto'` e compare o tamanho.
4. Explique por que índices B-tree não existem da mesma forma em um warehouse colunar.

## Referências

- Winand, M. *SQL Performance Explained* (use-the-index-luke.com) — a melhor fonte.
- Documentação do PostgreSQL — "Indexes".
