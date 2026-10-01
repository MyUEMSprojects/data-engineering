# Query planning e EXPLAIN

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

SQL é **declarativo**: você diz *o que* quer, não *como* obter. O **query planner**
(otimizador) decide o plano de execução — quais índices usar, em que ordem juntar
tabelas, qual algoritmo de join. `EXPLAIN` revela esse plano, e `EXPLAIN ANALYZE` o
executa e mostra os tempos reais. Ler planos é **a** habilidade para
[otimizar](../11-optimization/README.md).

## Como o planejador decide

O otimizador é **baseado em custo**: estima o custo de vários planos possíveis usando
**estatísticas** sobre as tabelas (nº de linhas, distribuição de valores,
cardinalidade) e escolhe o mais barato. Por isso estatísticas atualizadas (`ANALYZE`)
são cruciais — estimativas ruins → planos ruins.

```sql
ANALYZE pedidos;     -- atualiza estatísticas (feito também pelo autovacuum)
```

## EXPLAIN vs EXPLAIN ANALYZE

```sql
EXPLAIN SELECT * FROM pedidos WHERE cliente_id = 42;             -- só o plano estimado
EXPLAIN ANALYZE SELECT * FROM pedidos WHERE cliente_id = 42;     -- executa e mede
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;              -- + uso de buffers/IO
```

> `EXPLAIN ANALYZE` **executa** a query (cuidado com `UPDATE/DELETE` — rode dentro de
> uma transação com `ROLLBACK` se não quiser efeitos).

## Lendo um plano

O plano é uma **árvore**: lê-se de dentro para fora (os nós mais indentados rodam
primeiro). Exemplo:

```text
Nested Loop  (cost=0.43..16.48 rows=1 width=36) (actual time=0.03..0.05 rows=1 loops=1)
  ->  Index Scan using idx_pedidos_cliente on pedidos  (actual rows=1 loops=1)
        Index Cond: (cliente_id = 42)
  ->  Index Scan using clientes_pkey on clientes  (actual rows=1 loops=1)
        Index Cond: (id = pedidos.cliente_id)
Planning Time: 0.2 ms
Execution Time: 0.1 ms
```

O que olhar:

- **`cost=start..total`** — custo estimado (unidade arbitrária). Compare planos.
- **`rows`** estimado vs **`actual rows`** — se forem muito diferentes, as
  **estatísticas estão ruins** (rode `ANALYZE`) → provável causa de plano errado.
- **`loops`** — quantas vezes o nó rodou (num nested loop pode ser muitas).
- **`actual time`** — tempo real por nó.
- **`Execution Time`** — total.

## Nós de plano comuns (e o que significam)

### Acesso a dados

| Nó | Significado | Bom/ruim |
| --- | --- | --- |
| **Seq Scan** | varre a tabela inteira | ruim em tabela grande com filtro seletivo; ok em tabela pequena |
| **Index Scan** | usa índice e busca linhas na tabela | bom para poucas linhas |
| **Index Only Scan** | responde só pelo índice | ótimo |
| **Bitmap Index/Heap Scan** | combina índice + leitura em lote | bom para seletividade média |

### Joins

| Nó | Quando é escolhido |
| --- | --- |
| **Nested Loop** | um lado pequeno / com índice na condição |
| **Hash Join** | grandes volumes sem ordenação (constrói hash do menor) |
| **Merge Join** | ambos já ordenados pela chave |

### Outros

`Sort`, `Aggregate`/`HashAggregate`, `GroupAggregate`, `Gather` (paralelismo),
`Limit`, `Materialize`.

## Sinais de problema (red flags)

- **`Seq Scan`** em tabela grande com `WHERE` seletivo → falta índice (ver
  [índices](../07-indexes/README.md)).
- **`rows` estimado ≫/≪ `actual`** → estatísticas desatualizadas → `ANALYZE`.
- **Nested Loop com muitos `loops`** sobre tabela grande → join ineficiente.
- **`Sort`** grande com `Sort Method: external merge Disk` → ordenação estourou a
  memória (`work_mem` baixo).
- **Filtro aplicado tarde** (`Rows Removed by Filter` enorme) → traga o filtro para o
  índice/antes.

## Fluxo de diagnóstico

```text
1. Rode EXPLAIN ANALYZE na query lenta.
2. Ache o nó mais caro (maior actual time / rows removidas).
3. Estimado vs real muito diferente? → ANALYZE e repita.
4. Seq scan indevido? → crie/ajuste índice.
5. Join caro? → índice na condição, reduza linhas antes, reavalie a ordem.
6. Repita; meça o ganho.
```

## Warehouses colunares

Em BigQuery/Snowflake/Redshift o modelo é diferente (sem B-tree; execução
distribuída). Eles têm suas próprias ferramentas:

- **BigQuery** — *query plan/execution details*, *bytes processed* (custo = dados
  lidos → particionar/clusterizar reduz custo).
- **Snowflake** — *Query Profile* (operadores, spilling, partition pruning).
- **Spark** — `df.explain()` mostra o plano do [Catalyst](../../16-distributed-processing/09-catalyst-tungsten/README.md).

A mentalidade é a mesma: leia o plano, ache o gargalo, reduza dados movidos/lidos.

## Erros comuns

- Otimizar sem olhar o plano (achismo).
- Esquecer que `EXPLAIN ANALYZE` executa a query.
- Ignorar a divergência estimado × real (sintoma de estatística ruim).
- Criar índice sem confirmar no plano que ele passou a ser usado.

## Boas práticas

- Mantenha estatísticas atualizadas (`ANALYZE`/autovacuum).
- Leia o plano de dentro para fora; foque no nó mais caro.
- Compare planos antes/depois de uma mudança.
- Em warehouse, minimize **bytes lidos** (partição/cluster/colunas).

## Relação com outros conceitos

- Insumo direto da [otimização](../11-optimization/README.md).
- Depende de [índices](../07-indexes/README.md) e de como os
  [joins](../03-joins/README.md) são executados.
- Em escala: [Catalyst/Tungsten](../../16-distributed-processing/09-catalyst-tungsten/README.md).

## Exercícios

1. Rode `EXPLAIN ANALYZE` numa query com `WHERE` seletivo sem índice, identifique o
   `Seq Scan`, crie o índice e confirme a mudança do plano.
2. Force estatísticas desatualizadas, observe a divergência estimado×real e corrija com
   `ANALYZE`.
3. Compare o plano de um join entre tabela grande e pequena com e sem índice na
   condição.
4. No seu warehouse favorito, descubra quantos bytes uma query lê e reduza isso com um
   filtro de partição.

## Referências

- Documentação do PostgreSQL — "Using EXPLAIN", "Planner/Optimizer".
- Winand, M. *SQL Performance Explained*.
- Documentação de Query Profile (Snowflake) / query plan (BigQuery).
