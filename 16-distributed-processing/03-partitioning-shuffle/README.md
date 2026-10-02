# Partitioning e shuffle

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## O que é

- **Partitioning** (no processamento) — como os dados são divididos entre nós/tasks, definindo o
  paralelismo.
- **Shuffle** — a redistribuição de dados **entre nós** necessária quando uma operação precisa juntar
  dados de partições diferentes (agregar por chave, juntar tabelas, ordenar globalmente). **É a
  operação mais cara** do processamento distribuído.

Entender shuffle é a chave para escrever código Spark/distribuído eficiente.

## Partitioning

Os dados vivem em **partições**; cada task processa uma. O número de partições controla o paralelismo:

```text
poucas partições   → subutiliza o cluster (pouco paralelismo)
muitas partições   → overhead de agendamento (muitas tasks minúsculas)
partições desiguais → skew (um nó sobrecarregado — ver distributed joins/skew)
```

Operações que **mantêm** o particionamento (map, filter) são locais e baratas; operações que
**exigem reparticionar por uma nova chave** (groupBy, join, sort) disparam **shuffle**.

## Shuffle: o que é e por que é caro

Quando você faz `GROUP BY uf`, os dados de cada `uf` podem estar espalhados por **todas** as
partições/nós. Para agregar, o sistema precisa **mover** todas as linhas da mesma `uf` para o mesmo
nó. Esse rearranjo global é o shuffle:

```text
antes (particionado por chegada):      depois (particionado por uf):
 nó1: SP,RJ,SP     ──┐              ──► nó A: SP,SP,SP,...
 nó2: RJ,SP,MG     ──┼─ SHUFFLE ──► ──► nó B: RJ,RJ,...
 nó3: MG,SP        ──┘              ──► nó C: MG,MG,...
```

Por que é caro:

- **Rede** — mover dados entre nós é ordens de grandeza mais lento que memória/disco local.
- **Disco** — os dados do shuffle são escritos/lidos em disco (shuffle files) entre as *stages*.
- **Serialização** — empacotar/desempacotar os dados.
- **Barreira (stage boundary)** — tudo precisa terminar o map antes do reduce começar (sincronização).

> Regra de ouro: **minimize o shuffle**. A maior parte do tuning de Spark é reduzir o volume e a
> frequência de shuffles.

## O que causa shuffle

Operações *wide* (que dependem de várias partições):

- `groupBy`/`reduceByKey`/agregações por chave
- `join` (exceto broadcast — ver [caching/broadcast](../10-caching-broadcast/README.md))
- `distinct`, `orderBy`/`sort` global
- `repartition`

Operações *narrow* (sem shuffle, locais): `map`, `filter`, `select`, `withColumn`, `union`.

## Stages e tasks (como o shuffle estrutura a execução)

O Spark divide um job em **stages** nas fronteiras de shuffle. Dentro de uma stage, as operações
narrow rodam em pipeline (sem mover dados); o shuffle separa uma stage da próxima.

```text
Stage 1 (map/filter) ──shuffle── Stage 2 (reduce/agg) ──shuffle── Stage 3 ...
```

Ver o plano com `df.explain()` mostra os `Exchange` (shuffles) — cada um é um custo.

## Reduzindo o custo do shuffle

- **Filtre/projete cedo** — menos dados para embaralhar (`filter`/`select` antes do join/groupBy).
- **Pré-agregue** (map-side combine) — `reduceByKey` em vez de `groupByKey`; o Spark SQL faz parcial
  automaticamente.
- **Broadcast join** — se uma tabela é pequena, replique-a a todos os nós e evite shuffle da grande
  (ver [broadcast](../10-caching-broadcast/README.md)).
- **Dimensione partições** — `spark.sql.shuffle.partitions` (padrão 200) adequado ao volume; AQE
  (Adaptive Query Execution) ajusta em runtime.
- **Co-particione** — se duas tabelas já estão particionadas pela mesma chave de join, o shuffle pode
  ser evitado (bucketing).
- **Evite `repartition` desnecessário**; use `coalesce` para reduzir partições sem shuffle completo.

## Número de partições (dimensionar)

- Alvo comum: partições de ~128 MB (alinhado a blocos/HDFS/arquivos).
- `spark.sql.shuffle.partitions` controla o nº de partições pós-shuffle — padrão 200 pode ser demais
  (small files) ou pouco (skew) conforme o volume. **AQE** (Spark 3+) coalesce partições pequenas
  automaticamente.

## Erros comuns

- `groupByKey` quando `reduceByKey`/agg pré-combinável serviria (embaralha tudo).
- Join sem broadcast de tabela pequena (shuffle enorme desnecessário).
- `repartition` por reflexo (shuffle caro); confundir com `coalesce`.
- Não filtrar/projetar antes de operações wide.
- `spark.sql.shuffle.partitions` inadequado (200 fixo para qualquer volume).

## Boas práticas

- Pense em *narrow vs wide*: minimize operações wide e o volume que elas movem.
- Filtre/projete/pré-agregue antes do shuffle; broadcast tabelas pequenas.
- Ajuste o nº de partições (e deixe o AQE ajudar).
- Leia o `explain()` e cace os `Exchange`.

## Relação com outros conceitos

- Herança do [MapReduce](../02-mapreduce/README.md) (a fase shuffle/reduce).
- [Distributed joins/skew](../04-distributed-joins-skew/README.md),
  [broadcast](../10-caching-broadcast/README.md), [tuning](../11-performance-tuning/README.md).
- [Catalyst](../09-catalyst-tungsten/README.md) planeja os shuffles.

## Exercícios

1. Classifique como narrow ou wide: `filter`, `groupBy`, `select`, `join`, `orderBy`, `withColumn`.
2. Explique, passo a passo, o que acontece num `GROUP BY uf` distribuído e por que há shuffle.
3. Reescreva um pipeline para filtrar antes do join e reduzir o shuffle; compare no `explain()`.
4. Explique a diferença entre `repartition` e `coalesce` e quando usar cada.

## Referências

- Chambers & Zaharia, *Spark: The Definitive Guide* — shuffle e stages.
- Documentação do Spark — SQL performance, AQE.
- Kleppmann, M. *DDIA* — cap. 10.
