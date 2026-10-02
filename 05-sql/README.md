# 05 — SQL

> 🔵 Nível 2 — Core · Pré: [04 — Python para DE](../04-python-for-data-engineering/README.md) ·
> Próximo: [06 — Databases](../06-databases/README.md)

SQL é **a** linguagem da Engenharia de Dados. Transformações no
[warehouse](../13-data-warehouse/README.md), modelos [dbt](../28-dbt/README.md),
consultas analíticas, validações de qualidade — tudo passa por SQL. Este é o módulo
mais importante do nível Core: um DE que escreve SQL excelente resolve a maioria dos
problemas sem precisar de ferramentas pesadas.

## Filosofia deste módulo

SQL é **declarativo**: você descreve *o que* quer, e o banco decide *como* obter
(ver [query planning](10-query-planning-explain/README.md)). Dominar SQL é dominar
tanto a sintaxe quanto o **modelo de execução** — saber por que uma query é lenta e
como torná-la rápida. Por isso incluímos planejamento, índices e otimização, não só
`SELECT`.

> Os exemplos usam PostgreSQL como dialeto de referência (o mais próximo do padrão);
> diferenças relevantes de warehouses (BigQuery/Snowflake) são apontadas quando
> importam.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [SELECT e filtragem](01-select-filtering/README.md) | SELECT, WHERE, ORDER BY, LIMIT, NULL |
| 02 | [Agregação e GROUP BY](02-aggregation-grouping/README.md) | Funções de agregação, GROUP BY, HAVING |
| 03 | [JOINs](03-joins/README.md) | inner/left/right/full, semi/anti, self-join |
| 04 | [Subqueries e CTEs](04-subqueries-ctes/README.md) | Subconsultas, CTEs, recursão |
| 05 | [Window functions](05-window-functions/README.md) | OVER, PARTITION BY, ranking, running totals |
| 06 | [Views e materialized views](06-views-materialized-views/README.md) | Abstração e pré-computação |
| 07 | [Índices](07-indexes/README.md) | B-tree, hash, uso e custo |
| 08 | [Transações e isolamento](08-transactions-isolation/README.md) | ACID, isolation levels, locks |
| 09 | [Constraints](09-constraints/README.md) | PK, FK, unique, check, not null |
| 10 | [Query planning e EXPLAIN](10-query-planning-explain/README.md) | Ler planos de execução |
| 11 | [Otimização](11-optimization/README.md) | Tornar queries rápidas |
| 12 | [Procedures e functions](12-procedures-functions/README.md) | Lógica no banco, UDFs |
| 13 | [SQL analítico](13-analytical-sql/README.md) | GROUPING SETS, pivot, padrões de analytics |

## Dependências internas

```text
SELECT/filtragem ─► Agregação ─► JOINs ─► Subqueries/CTEs ─► Window functions ─► SQL analítico
                                                   │
Constraints ─► Transações/isolamento              │
                                                   ▼
Índices ─► Query planning/EXPLAIN ─► Otimização   Views/materialized views
```

## Checkpoint

- [ ] Escrever SELECTs com filtros, ordenação e tratamento correto de NULL.
- [ ] Agregar com GROUP BY/HAVING e entender a diferença de WHERE vs HAVING.
- [ ] Usar todos os tipos de JOIN e reconhecer joins que multiplicam linhas.
- [ ] Reescrever subqueries como CTEs e usar CTE recursiva.
- [ ] Resolver "top-N por grupo", *running total* e deduplicação com window functions.
- [ ] Explicar ACID e os *isolation levels* e seus fenômenos.
- [ ] Ler um `EXPLAIN ANALYZE` e identificar *seq scan*, *nested loop* e gargalos.
- [ ] Decidir quando (não) criar um índice e otimizar uma query lenta.

## Referências do módulo

- *SQL Performance Explained*, Markus Winand (use-the-index-luke.com).
- Documentação do PostgreSQL (postgresql.org/docs) — a melhor referência de SQL.
- *Fundamentals of Data Engineering* — cap. de queries e modelagem.
- Kimball, R. *The Data Warehouse Toolkit* (SQL analítico/dimensional).
