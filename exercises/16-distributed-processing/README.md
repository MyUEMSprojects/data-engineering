# Exercícios — Módulo 16: Processamento distribuído

Teoria em [16-distributed-processing](../../16-distributed-processing/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Transformações estreitas × largas

Classifique em Spark: `filter`, `groupBy().agg`, `select`, `join` (duas tabelas grandes), `withColumn`, `distinct`. Qual causa **shuffle**?

<details><summary>Gabarito</summary>

**Estreitas** (sem shuffle): `filter`, `select`, `withColumn`. **Largas** (shuffle): `groupBy().agg`, `join` (sort-merge), `distinct`. O shuffle redistribui dados pela rede e disco — é, em geral, o custo dominante. Ver [partições e shuffle](../../16-distributed-processing/03-partitioning-shuffle/README.md).
</details>

## 2. 🟢 Conceitual — Lazy evaluation

O que acontece quando você escreve `df.filter(...).select(...)` sem nenhuma **ação**? Dê três exemplos de ação.

<details><summary>Gabarito</summary>

Nada é executado: o Spark só constrói o **plano lógico**. A execução começa em uma **ação** (`count`, `collect`, `show`, `write`). Isso permite ao Catalyst **otimizar o plano inteiro** (pushdown, reordenação). Ver [Catalyst/Tungsten](../../16-distributed-processing/09-catalyst-tungsten/README.md).
</details>

## 3. 🔵 Implementação — Broadcast join

Uma tabela de fatos (2 bilhões de linhas) junta com uma dimensão de 50 mil linhas. Escreva o join otimizado em PySpark e explique o que muda no plano.

<details><summary>Gabarito</summary>

```python
from pyspark.sql import functions as F
out = facts.join(F.broadcast(dim), "product_id")
```
O plano troca `SortMergeJoin` (shuffle dos **dois** lados) por `BroadcastHashJoin`: a dimensão é enviada a cada executor e o lado grande **não sofre shuffle**. Limite: a dimensão precisa caber na memória do executor (`autoBroadcastJoinThreshold`). Medido no [Projeto 06](../../projects/06-spark/README.md) (E2).
</details>

## 4. 🔵 Debugging — Uma tarefa de 40 minutos

Um job tem 199 tarefas de 20 s e **uma de 40 min**. O que é, como diagnosticar e duas formas de resolver?

<details><summary>Gabarito</summary>

**Data skew**: uma chave concentra muitas linhas. Diagnóstico: Spark UI → *Stages* → distribuição de duração/bytes por tarefa; contagem por chave. Soluções: **AQE skew join** (divide partições grandes), **salting** (espalhar a chave quente) ou tratar a chave quente separadamente (broadcast). Reproduzido no [Projeto 06](../../projects/06-spark/README.md) (E3: 9,8× a mediana → 2,6×). Ver [joins e skew](../../16-distributed-processing/04-distributed-joins-skew/README.md).
</details>

## 5. 🟣 Implementação — Salting

Implemente o join com **salting** de uma chave quente `user_id = 0` (balde = 16) entre `events` (grande) e `users`.

<details><summary>Gabarito</summary>

```python
from pyspark.sql import functions as F
B = 16
is_hot = F.col("user_id") == 0
ev = events.withColumn("salt", F.when(is_hot, F.floor(F.rand() * B).cast("int")).otherwise(0))
us = users.withColumn("salt", F.explode(F.when(is_hot, F.sequence(F.lit(0), F.lit(B - 1))).otherwise(F.array(F.lit(0)))))
out = ev.join(us, ["user_id", "salt"], "left").drop("salt")
```
Só a chave quente é replicada B× no lado pequeno. Código completo e testado (equivalência com o join comum) em [`transforms.py`](../../projects/06-spark/src/sparkjobs/transforms.py).
</details>

## 6. 🟣 Arquitetura — Dimensionar o cluster

Um job processa 2 TB (Parquet) por dia em 1 h. Como estimar nº de executores, memória e partições? Que sinais indicam *spill* e subdimensionamento?

<details><summary>Gabarito</summary>

Alvo de **128–256 MB por partição** ⇒ 2 TB ≈ 8–16 mil partições. Paralelismo = executores × cores; tempo ≈ (partições × tempo por tarefa) / cores. Memória: partição + estado de shuffle/joins deve caber (~2–4 GB por core como ponto de partida). Sinais de problema: **spill** em disco (UI), GC alto, *shuffle read* enorme em poucas tarefas (skew), tarefas muito curtas (partições demais). Ajuste iterando com a UI. Ver [tuning](../../16-distributed-processing/11-performance-tuning/README.md).
</details>
