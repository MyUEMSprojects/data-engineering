# Query optimization (no warehouse)

> 🔵 Analytics Platforms · Parte de [13 — Data Warehouse](../README.md)

## O que é

Tornar consultas de warehouse **rápidas e baratas**. O princípio é o mesmo do
[SQL/otimização](../../05-sql/11-optimization/README.md) — processar menos dados — mas o modelo é
diferente: não há índices B-tree; o que manda é **quantos bytes são lidos** e **quanto dado é
movido entre nós** (shuffle). Em warehouses com cobrança por consumo, otimizar é literalmente
reduzir a fatura.

## A métrica que importa: bytes lidos e dados movidos

```text
Custo/tempo ≈ bytes lidos (storage→compute) + dados movidos entre nós (shuffle)
```

Toda otimização de warehouse se resume a reduzir esses dois.

## As alavancas (por impacto)

### 1. Ler menos colunas

Nunca `SELECT *`; selecione só o necessário (colunar cobra por coluna — ver
[columnar](../02-columnar-storage/README.md)).

### 2. Ler menos linhas (partition pruning + cluster)

Filtre pela coluna de [partição/cluster](../03-partitioning-clustering/README.md) para ler só os
blocos relevantes. Evite funções sobre a coluna de partição (quebram o pruning).

```sql
-- bom: lê 1 partição
WHERE dt = '2024-01-15'
-- ruim: impede pruning
WHERE DATE(event_ts) = '2024-01-15'
```

### 3. Reduzir shuffle em joins e agregações

Joins e `GROUP BY` podem exigir **mover dados entre nós** (shuffle — caro). Reduza:

- Filtre/agregue **antes** do join (menos linhas para mover).
- Junte pela chave que o warehouse co-localiza (distribution key no
  [Redshift](../07-redshift/README.md)); deixe tabelas pequenas serem *broadcast*.
- Evite joins desnecessários; pré-junte em marts (ver [modelagem](../../07-data-modeling/README.md)).

### 4. Evitar fan-out e `COUNT(DISTINCT)` caro

Joins 1:N que inflam linhas ([fan-out](../../05-sql/03-joins/README.md)); `COUNT(DISTINCT)` em
alta cardinalidade (use `APPROX_COUNT_DISTINCT`/HLL quando aproximação servir).

### 5. Pré-computar o recorrente

Para consultas frequentes/caras, materialize: [materialized views](../../05-sql/06-views-materialized-views/README.md),
tabelas agregadas, ou modelos [dbt incrementais](../../28-dbt/08-incremental-models/README.md).
Trocar recomputar por ler pré-computado é a maior economia em dashboards.

## Lendo o plano/perfil de execução

Cada warehouse tem sua ferramenta (ver [EXPLAIN geral](../../05-sql/10-query-planning-explain/README.md)):

- **BigQuery** — *execution details* + **bytes processed/billed** (o número que vira custo);
  *dry run* estima bytes sem rodar.
- **Snowflake** — *Query Profile* (operadores, **spilling** para disco/memória, *partition
  pruning*, bytes scanned).
- **Redshift** — `EXPLAIN` + *system tables* (svl/stl) mostrando shuffle (`DS_DIST_*`), sort,
  disk-based steps.

Procure: muitos bytes lidos (falta pruning/colunas), **spilling** (memória insuficiente),
**shuffle** alto (`DS_DIST_INNER`/broadcast no Redshift), e desbalanceamento (skew).

## Spilling e skew

- **Spilling** — quando a operação (sort/hash/join) não cabe na memória e "derrama" para disco →
  lento. Reduza o volume processado ou aumente o compute.
- **[Skew](../../16-distributed-processing/04-distributed-joins-skew/README.md)** — uma chave com
  muito mais dados sobrecarrega um nó. Revise a distribuição/chave.

## Otimizar custo (cloud)

- **Por bytes** (BigQuery) — particione/clusterize, selecione colunas, use *dry run* para estimar,
  e considere *materialized views* para consultas repetidas.
- **Por compute-time** (Snowflake/Redshift) — dimensione o cluster/warehouse ao certo, **suspenda
  quando ocioso** (auto-suspend), separe cargas por cluster, e use caching de resultados.
- **Result cache** — repetir a mesma query pode ser grátis/instantâneo (cache) — aproveite.

Ver [cost management](../../19-cloud/08-cost-management/README.md).

## Erros comuns

- `SELECT *` e falta de partição (lê/custa demais).
- Função na coluna de partição (quebra pruning).
- Joins sem filtrar antes → shuffle enorme.
- `COUNT(DISTINCT)` em bilhões sem necessidade de exatidão.
- Compute ligado ocioso; não usar materializações para dashboards recorrentes.
- Ignorar o perfil/bytes da query (otimizar no escuro).

## Boas práticas

- Selecione colunas; filtre por partição/cluster; agregue/filtre antes de juntar.
- Pré-compute o recorrente (MV/dbt incremental).
- Leia o perfil: ataque bytes lidos, spilling e shuffle.
- Dimensione/suspenda compute; use result cache; estime custo (dry run).

## Relação com outros conceitos

- [SQL/otimização](../../05-sql/11-optimization/README.md),
  [columnar](../02-columnar-storage/README.md),
  [partitioning/clustering](../03-partitioning-clustering/README.md).
- [Cost](../../19-cloud/08-cost-management/README.md),
  [shuffle/skew](../../16-distributed-processing/04-distributed-joins-skew/README.md),
  [MVs](../../05-sql/06-views-materialized-views/README.md).

## Exercícios

1. Reduza os bytes processados de uma query no BigQuery (dry run antes/depois) selecionando
   colunas e filtrando por partição.
2. Identifique *spilling* no Query Profile do Snowflake e proponha uma correção.
3. Reescreva um join caro agregando a tabela grande antes de juntar.
4. Decida entre materializar uma agregação (MV/dbt) vs recomputar, com base na frequência de uso.

## Referências

- Documentação de otimização/custo de BigQuery, Snowflake (Query Profile) e Redshift.
- Winand, M. *SQL Performance Explained* (princípios gerais).
