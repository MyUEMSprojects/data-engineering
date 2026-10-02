# Performance tuning (Spark)

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## A mentalidade

Otimizar Spark é, quase sempre, **reduzir dados lidos e dados movidos (shuffle)** e **balancear o
trabalho** entre executors. Como em qualquer otimização: **meça primeiro** (Spark UI / `explain()`),
ache o gargalo real, mude uma coisa, remeça. Este tópico reúne as alavancas; muitas já apareceram nos
tópicos anteriores.

## Onde medir: Spark UI e explain

- **Spark UI** — jobs → stages → tasks: durações, shuffle read/write, spill, skew (task "fora da
  curva"), GC. É a fonte da verdade.
- **`df.explain(True)`** — o plano físico: pushdown, tipo de join, `Exchange` (shuffles).

## As alavancas (por impacto)

### 1. Ler menos (I/O)

- **Parquet + partição** — filtre por coluna de partição (partition pruning) e selecione colunas
  (projection pruning). Evite CSV e `SELECT *` (ver [Parquet](../../08-data-formats/04-parquet/README.md),
  [Catalyst pushdown](../09-catalyst-tungsten/README.md)).
- **Predicate pushdown** — filtre cedo; o Catalyst empurra para a leitura.

### 2. Reduzir shuffle (rede/disco)

A maior alavanca distribuída (ver [shuffle](../03-partitioning-shuffle/README.md)):

- Filtre/projete/**pré-agregue antes** de joins e groupBy.
- **Broadcast** tabelas pequenas (ver [broadcast](../10-caching-broadcast/README.md)).
- Ajuste `spark.sql.shuffle.partitions` ao volume (padrão 200 pode ser demais/pouco); **AQE** coalesce
  automaticamente.
- Evite `repartition` desnecessário; `coalesce` para reduzir partições sem shuffle completo.

### 3. Tratar skew (balanceamento)

[Skew](../04-distributed-joins-skew/README.md) faz um nó virar gargalo. **Ligue o AQE**
(`skewJoin`), trate NULLs na chave, aplique salting. Sintoma na UI: uma task muito mais longa que as
demais.

### 4. Dimensionar partições

- Alvo ~128 MB por partição; nem minúsculas ([small files](../../14-data-lake/06-small-files-compaction/README.md)),
  nem gigantes (OOM/pouco paralelismo).
- `spark.sql.files.maxPartitionBytes` (leitura) e `shuffle.partitions` (pós-shuffle); AQE ajuda.

### 5. Caching com intenção

Cacheie o que é **reutilizado e caro**; `unpersist` depois (ver
[caching](../10-caching-broadcast/README.md)). Cache em excesso **prejudica**.

### 6. Evitar UDFs Python

Use funções nativas (`F`); se precisar de Python, **pandas UDFs** (vetorizadas via Arrow). UDFs linha a
linha cegam o [Catalyst/Tungsten](../09-catalyst-tungsten/README.md) e serializam Python↔JVM (ver
[PySpark](../07-pyspark/README.md)).

## Recursos: executors, cores, memória

- **Executors** × **cores por executor** × **memória por executor** definem o paralelismo e a
  capacidade. Muitos cores por executor compartilham memória (risco de OOM/spill); poucos
  desperdiçam.
- **Memória**: dividida entre execução (shuffle/sort/join) e storage (cache). Pressão de memória →
  **spill** para disco (lento) ou **OOM**.
- Regra prática comum: executors "médios" (ex.: ~4–5 cores, memória proporcional) costumam equilibrar
  melhor que "monstros" ou "minúsculos" — ajuste medindo.

## Spill e OOM (sintomas e causas)

- **Spill** (na UI: "spill memory/disk") — a operação não coube na memória e foi para o disco. Reduza o
  volume por task (mais partições, filtrar antes) ou aumente a memória.
- **OOM no executor** — partição grande demais (skew), broadcast grande, ou memória insuficiente.
- **OOM no driver** — `collect()`/`toPandas()` de dados grandes, ou broadcast grande (o driver coleta
  antes de distribuir).

## AQE: ligue e confie (com verificação)

O [Adaptive Query Execution](../09-catalyst-tungsten/README.md) (Spark 3+) resolve automaticamente
muito do que acima: coalesce de partições, skew join, troca para broadcast. **Mantenha ligado** — mas
ainda verifique o plano/UI.

## Formato e layout de saída

- Escreva **Parquet** particionado por data; controle o nº de arquivos (evite
  [small files](../../14-data-lake/06-small-files-compaction/README.md)); compacte quando necessário.
- Em [lakehouse](../../15-lakehouse/README.md), use `OPTIMIZE`/Z-order para data skipping.

## Checklist de tuning

```text
[ ] Lê Parquet particionado? Filtra/projeta cedo (pushdown)?
[ ] Minimiza shuffle? (filtra/pré-agrega antes; broadcast de pequenas)
[ ] AQE ligado? (coalesce + skew join)
[ ] Partições dimensionadas (~128 MB)? Sem small files na saída?
[ ] Sem UDF Python onde função nativa serve?
[ ] Cache só do reutilizado/caro (com unpersist)?
[ ] Sem collect/toPandas de dados grandes?
[ ] Executors/cores/memória adequados? Sem spill/OOM na UI?
```

## Erros comuns

- Otimizar sem olhar a Spark UI/`explain()`.
- Shuffle desnecessário (não filtra antes, não usa broadcast).
- Ignorar skew/spill; `collect()` grande.
- `shuffle.partitions=200` fixo para qualquer volume; AQE desligado.
- UDFs Python; cache indiscriminado.

## Boas práticas

- Meça → mude uma coisa → remeça.
- Reduza leitura (Parquet/partição/colunas) e shuffle (broadcast/pré-agregar/AQE).
- Dimensione partições e recursos; evite spill/OOM e small files.
- Funções nativas; cache intencional.

## Relação com outros conceitos

- [Shuffle](../03-partitioning-shuffle/README.md),
  [joins/skew](../04-distributed-joins-skew/README.md),
  [caching/broadcast](../10-caching-broadcast/README.md),
  [Catalyst/AQE](../09-catalyst-tungsten/README.md), [PySpark](../07-pyspark/README.md).
- [Performance geral](../../04-python-for-data-engineering/10-performance-profiling/README.md),
  [query optimization do warehouse](../../13-data-warehouse/04-query-optimization/README.md).

## Exercícios

1. Dado um job lento, descreva o roteiro de diagnóstico (UI → gargalo → mudança → remeça).
2. Reduza o shuffle de um pipeline filtrando/pré-agregando antes do join; compare no `explain()`.
3. Identifique skew e spill na Spark UI e proponha correções.
4. Explique como dimensionar partições e por que 200 fixo pode ser ruim.

## Referências

- Chambers & Zaharia, *Spark: The Definitive Guide* — tuning.
- Documentação do Spark — Tuning Guide, AQE, Spark UI.
- Karau, H.; Warren, R. *High Performance Spark*.
