# Otimização de queries

> 🔵 Core · Parte de [05 — SQL](../README.md)

## A mentalidade

Otimizar SQL é, quase sempre, **reduzir o volume de dados que o banco processa e
move**. Antes de qualquer truque, use [`EXPLAIN ANALYZE`](../10-query-planning-explain/README.md)
para achar o gargalo real — otimizar por achismo desperdiça tempo e pode piorar.

```text
Meça (EXPLAIN) → entenda o gargalo → aplique UMA mudança → remeça → repita.
```

## As grandes alavancas (por impacto)

### 1. Leia menos linhas (filtre cedo e com índice)

- Filtre no `WHERE` o mais cedo possível; garanta que o filtro use
  [índice](../07-indexes/README.md) (evite `Seq Scan` indevido).
- Evite funções sobre a coluna filtrada (`WHERE date(criado_em)=...` não usa índice;
  use `WHERE criado_em >= ... AND < ...`).
- Em warehouse: filtre por **coluna de partição** para *partition pruning*.

### 2. Leia menos colunas

- `SELECT col1, col2` em vez de `SELECT *` — crucial em
  [armazenamento colunar](../../08-data-formats/08-row-vs-columnar/README.md): lê só as
  colunas pedidas. Também habilita *index-only scan*.

### 3. Junte de forma eficiente

- Índice na coluna de `JOIN`.
- Reduza as tabelas **antes** do join (filtre/agregue em CTEs).
- Cuidado com *fan-out* (joins 1:N que inflam linhas — ver
  [joins](../03-joins/README.md)).

### 4. Agregue de forma barata

- Filtre antes de `GROUP BY`; evite `COUNT(DISTINCT)` em altíssima cardinalidade (use
  aproximação quando aceitável).
- Pré-agregue com [materialized views](../06-views-materialized-views/README.md) ou
  tabelas [incrementais](../../28-dbt/08-incremental-models/README.md) para consultas
  recorrentes.

## Padrões específicos

### Paginação: keyset em vez de OFFSET

`OFFSET 100000` faz o banco ler e descartar 100 mil linhas. Use **keyset**:

```sql
-- em vez de LIMIT 20 OFFSET 100000
SELECT * FROM pedidos
WHERE id > :ultimo_id        -- "seek" a partir do último visto
ORDER BY id
LIMIT 20;
```

### EXISTS em vez de IN (e NOT EXISTS em vez de NOT IN)

Mais seguro com `NULL` e frequentemente tão/mais eficiente (ver
[subqueries](../04-subqueries-ctes/README.md)).

### Top-N por grupo com window + filtro

Em vez de subqueries correlacionadas caras, use
[`ROW_NUMBER()`](../05-window-functions/README.md) e filtre o rank numa CTE.

### Evite N+1 no app

Não faça uma query por linha num loop na aplicação; faça **uma** query com `JOIN`/`IN`.

### Não traga para o cliente o que o banco faz melhor

Agregar/juntar milhões de linhas no [pandas](../../04-python-for-data-engineering/11-pandas/README.md)
é mais lento e custoso que fazer no SQL. **Empurre a computação para onde o dado está.**

## Ajustes do servidor (Postgres)

- `work_mem` baixo → `Sort`/`Hash` "derramam" para disco (`external merge Disk`).
  Aumente para queries analíticas pesadas (por sessão).
- `VACUUM`/`autovacuum` — recupera espaço e atualiza visibilidade; tabelas "inchadas"
  ficam lentas.
- `ANALYZE` — estatísticas atualizadas = planos melhores.

## Otimização em warehouses (modelo diferente)

Aqui o custo e a velocidade vêm de **quanto dado é lido/movido**, não de índices
B-tree:

- **Particionamento** (por data) — lê só as partições do filtro.
- **Clustering/sort keys** — co-localiza dados correlatos para *pruning*.
- **Evitar SELECT *** — colunar cobra por coluna/bytes lidos (BigQuery cobra por bytes
  processados!).
- **Materializações incrementais** ([dbt](../../28-dbt/08-incremental-models/README.md))
  — reprocessar só o novo.
- **Reduzir shuffle** em [Spark](../../16-distributed-processing/11-performance-tuning/README.md)
  (broadcast joins, repartition consciente).

## Anti-padrões (SQL smells)

- `SELECT *` em produção.
- Função na coluna do `WHERE`/`JOIN` (mata o índice).
- `OFFSET` grande para paginar.
- `DISTINCT` para "consertar" um join que multiplica (conserte o join).
- `OR` que impede índice (às vezes `UNION ALL` de dois filtros indexáveis é melhor).
- Subqueries correlacionadas caras onde uma window resolveria.
- Cast implícito de tipos na comparação (impede índice).

## Processo completo

```text
1. Reproduza a lentidão e meça (EXPLAIN ANALYZE, BUFFERS).
2. Localize o nó mais caro / mais linhas removidas.
3. Reduza linhas (filtro+índice) ou colunas (projeção).
4. Melhore o join/agregação (índice, pré-agregação, ordem).
5. Considere pré-computar (MV/tabela incremental) se é recorrente.
6. Remeça; confirme o ganho e que o resultado continua correto (teste!).
```

## Erros comuns

- Otimizar sem `EXPLAIN`.
- Adicionar índices demais (piora escrita; ver [índices](../07-indexes/README.md)).
- Resolver fan-out com `DISTINCT` em vez de corrigir a granularidade.
- Trazer dados demais para a aplicação.
- Esquecer `ANALYZE`/`VACUUM`.

## Boas práticas

- Meça, mude uma coisa, remeça.
- Filtre/projete cedo; indexe o que a query real usa.
- Pré-compute o que é consultado com frequência.
- Em warehouse, minimize bytes lidos (partição/cluster/colunas).
- Valide que a otimização não mudou o resultado (testes de dados).

## Relação com outros conceitos

- Diagnóstico: [EXPLAIN](../10-query-planning-explain/README.md);
  ferramentas: [índices](../07-indexes/README.md),
  [MVs](../06-views-materialized-views/README.md).
- Em escala: [tuning de Spark](../../16-distributed-processing/11-performance-tuning/README.md),
  [partitioning do warehouse](../../13-data-warehouse/03-partitioning-clustering/README.md).

## Exercícios

1. Otimize uma query com `WHERE date(criado_em) = ...` reescrevendo-a para usar índice
   por faixa.
2. Troque `OFFSET` grande por keyset pagination e compare os tempos.
3. Encontre um `DISTINCT` que esconde um fan-out e corrija a causa.
4. Numa query de warehouse, reduza os bytes processados com filtro de partição e
   seleção de colunas.

## Referências

- Winand, M. *SQL Performance Explained* (use-the-index-luke.com).
- Documentação do PostgreSQL — "Performance Tips".
- Documentação de otimização de custo do BigQuery.
