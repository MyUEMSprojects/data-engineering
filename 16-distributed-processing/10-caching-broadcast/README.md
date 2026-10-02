# Caching e broadcast

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

Duas técnicas de otimização do [Spark](../05-apache-spark/README.md) que atacam dois custos
diferentes: **caching** evita **recomputar** o mesmo dado; **broadcast** evita **shuffle** em joins com
tabelas pequenas.

## Caching (persistência de resultados intermediários)

### O problema

Spark é [lazy](../05-apache-spark/README.md): cada **action** recomputa o DataFrame **desde a fonte**
(seguindo a [lineage](../08-rdd-dataframe/README.md)). Se você usa o mesmo DataFrame intermediário
várias vezes (ex.: um resultado caro consumido por várias saídas, ou um loop iterativo de ML), ele é
recomputado a cada uso — desperdício.

### A solução

`cache()`/`persist()` mantêm o DataFrame em memória (e/ou disco) após a primeira computação, para reuso
rápido:

```python
df_caro = df.filter(...).join(...).groupBy(...).agg(...)
df_caro.cache()            # marca para persistir (lazy: materializa na 1ª action)
df_caro.count()            # força a materialização
df_caro.write...(saida1)   # usa o cache
df_caro.write...(saida2)   # usa o cache (não recomputa)
df_caro.unpersist()        # libera quando não precisar mais
```

Níveis de `persist` (StorageLevel): `MEMORY_ONLY`, `MEMORY_AND_DISK` (spill p/ disco se não couber),
etc. `cache()` = `MEMORY_AND_DISK` para DataFrames.

### Quando (não) cachear

- **Cacheie** quando um DataFrame é **reutilizado várias vezes** e é **caro** de computar.
- **NÃO cacheie** se é usado uma vez só (não há o que reusar — só gasta memória), ou se é tão grande
  que ocupar memória prejudica o resto do job. Cache em excesso **atrapalha** (pressão de memória,
  eviction, menos memória para shuffle/execução).

> Cache não é "mais rápido por padrão". Use com intenção, e **unpersist** quando terminar.

## Broadcast (evitar shuffle em joins)

### O problema

Juntar duas tabelas por padrão exige [shuffle](../03-partitioning-shuffle/README.md) de ambas (caro).
Mas se uma é **pequena**, isso é desnecessário.

### A solução: broadcast join

Replicar a tabela **pequena** para **todos os executors**; cada um junta sua partição da tabela grande
com a cópia local — **sem embaralhar a grande**:

```python
from pyspark.sql import functions as F
fato.join(F.broadcast(dim_pequena), on="cliente_id", how="left")   # força broadcast
```

O Spark **faz broadcast automaticamente** quando estima que a tabela cabe no limite
`spark.sql.autoBroadcastJoinThreshold` (padrão ~10 MB). Para tabelas um pouco maiores que você sabe
caberem, use `F.broadcast(...)` explicitamente.

```text
Sort-merge join: shuffle de A (grande) + shuffle de B (grande)   → caro
Broadcast join:  B (pequena) replicada; A não embaralha           → rápido ✅
```

É por isso que juntar [dimensões](../../07-data-modeling/08-dimension-tables/README.md) pequenas com um
[fato](../../07-data-modeling/07-fact-tables/README.md) grande num
[star schema](../../07-data-modeling/05-star-schema/README.md) é eficiente.

### Cuidados com broadcast

- A tabela broadcast precisa **caber na memória** de cada executor **e** do driver (que a coleta
  primeiro). Broadcast de algo grande demais → OOM no driver.
- Equivale ao `DISTSTYLE ALL` do [Redshift](../../13-data-warehouse/07-redshift/README.md).
- O **AQE** pode converter um join para broadcast em runtime ao descobrir que um lado é pequeno (ver
  [Catalyst/AQE](../09-catalyst-tungsten/README.md)).

## Broadcast variables (RDD / lookup)

Além do broadcast join, há **broadcast variables** para disponibilizar um dado pequeno (um dicionário
de lookup) a todas as tasks sem reenviá-lo a cada uma — útil na API [RDD](../08-rdd-dataframe/README.md)
e em UDFs que precisam de um mapa de referência.

## Erros comuns

- Cachear DataFrames usados uma vez só (desperdício de memória).
- Esquecer `unpersist` (memória presa o job todo).
- Cache gigante que sufoca a memória de execução/shuffle.
- Broadcast de tabela grande demais → OOM no driver.
- Não usar broadcast quando um lado é pequeno (shuffle desnecessário).

## Boas práticas

- Cacheie só o que é **reutilizado e caro**; `unpersist` ao terminar; dimensione a memória.
- Deixe o Spark fazer broadcast automático; force `F.broadcast` para tabelas pequenas um pouco acima do
  limite.
- Ligue o AQE (converte joins para broadcast quando descobre tamanhos reais).
- Verifique no `explain()` se o join é `BroadcastHashJoin`.

## Relação com outros conceitos

- [Shuffle](../03-partitioning-shuffle/README.md),
  [distributed joins/skew](../04-distributed-joins-skew/README.md),
  [Catalyst/AQE](../09-catalyst-tungsten/README.md), [tuning](../11-performance-tuning/README.md).
- Star schema: [dimensões pequenas](../../07-data-modeling/08-dimension-tables/README.md).

## Exercícios

1. Explique por que uma action recomputa o DataFrame desde a fonte e como o cache evita isso.
2. Dê um caso em que cachear ajuda e outro em que atrapalha.
3. Force um broadcast join de uma dimensão pequena com um fato grande e confirme no `explain()`
   (`BroadcastHashJoin`).
4. Explique o risco de broadcast de uma tabela grande demais.

## Referências

- Chambers & Zaharia, *Spark: The Definitive Guide* — caching e joins.
- Documentação do Spark — persistence, broadcast join, AQE.
