# RDD e DataFrame

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## O que é

As duas principais abstrações de dados do [Spark](../05-apache-spark/README.md):

- **RDD (Resilient Distributed Dataset)** — a abstração **original** e de baixo nível: uma coleção
  distribuída e imutável de objetos, particionada entre nós. Flexível, mas **sem** otimizador nem
  schema.
- **DataFrame** — abstração de **alto nível**, tabular (linhas/colunas com schema), **otimizada** pelo
  [Catalyst](../09-catalyst-tungsten/README.md). É o que você deve usar na prática.

(Há também o **Dataset**, tipado, relevante em Scala/Java; em [PySpark](../07-pyspark/README.md) você
usa DataFrame.)

## RDD: a fundação

```python
rdd = sc.parallelize([1, 2, 3, 4])
rdd.map(lambda x: x * 2).filter(lambda x: x > 4).collect()   # [6, 8]
```

Propriedades-chave do RDD:

- **Resilient** — tolerante a falhas via **lineage**: o RDD "lembra" como foi derivado (a sequência de
  transformações a partir da fonte). Se uma partição é perdida, o Spark a **recomputa** a partir da
  lineage, sem recomeçar tudo. É assim que o Spark tolera falhas (ver
  [fault tolerance](../../10-data-pipelines/05-fault-tolerance/README.md)).
- **Distributed** — particionado entre nós.
- **Immutable** — transformações criam novos RDDs (não mutam).
- **Lazy** — transformations constroem o plano; actions executam.

Limitações: opera sobre objetos Python/JVM opacos → **sem schema, sem otimizador** (Catalyst não
enxerga dentro de uma função lambda). Você é responsável por toda a eficiência.

## DataFrame: alto nível e otimizado

```python
df = spark.read.parquet("vendas.parquet")
df.filter("valor > 100").groupBy("uf").sum("valor")
```

Vantagens sobre o RDD:

- **Schema** — colunas tipadas; o Spark sabe a estrutura.
- **Catalyst** — o [otimizador](../09-catalyst-tungsten/README.md) reescreve o plano (pushdown,
  reordenar filtros, escolher joins).
- **Tungsten** — execução eficiente em memória binária, sem overhead de objetos Python/JVM.
- **APIs ergonômicas** — [SQL](../06-spark-sql/README.md) e DataFrame.

Como o Spark "entende" as operações de DataFrame (não são lambdas opacas), ele pode **otimizá-las** —
daí serem muito mais rápidas que RDDs equivalentes, inclusive em Python (a lógica roda na JVM
otimizada, não no Python).

## RDD vs DataFrame

| Aspecto | RDD | DataFrame |
| --- | --- | --- |
| Nível | baixo | alto |
| Schema | não | sim |
| Otimizador (Catalyst) | **não** | **sim** |
| Execução (Tungsten) | objetos | binária eficiente |
| Performance (PySpark) | menor | **muito maior** |
| Quando usar | controle fino, dados não-tabulares | **quase sempre** |

> **Regra:** use **DataFrame/SQL** por padrão. O RDD só quando você precisa de algo que a API alta não
> expressa (manipulação de baixo nível, tipos de dado não tabulares, controle total do
> particionamento).

## Lineage e DAG (como a resiliência funciona)

Cada DataFrame/RDD guarda sua **lineage** — o grafo de como foi construído a partir da fonte. O Spark
usa isso para:

- **Recuperação** — recomputar partições perdidas (tolerância a falhas sem replicar dados).
- **Otimização** — o Catalyst analisa o grafo lógico antes de executar.

Ver a lineage/plano com `df.explain()`.

## Conversão entre eles

```python
rdd = df.rdd                 # DataFrame → RDD (perde otimização)
df = rdd.toDF(["col1", ...]) # RDD → DataFrame (precisa de schema)
```

Evite ir para RDD e voltar sem necessidade (perde as otimizações no caminho).

## Erros comuns

- Usar RDD por hábito/"parece mais poderoso" → perde Catalyst/Tungsten (muito mais lento).
- Misturar RDD e DataFrame desnecessariamente (quebra a otimização).
- Achar que DataFrame em Python é lento como código Python puro (não é — roda na JVM otimizada).
- `collect()` de RDD/DataFrame grande no driver (OOM).

## Boas práticas

- **DataFrame/SQL** por padrão; RDD só em casos específicos.
- Deixe o Catalyst otimizar (use funções nativas, não lambdas opacas).
- Entenda lineage/plano via `explain()`.
- Minimize conversões RDD↔DataFrame.

## Relação com outros conceitos

- [Spark](../05-apache-spark/README.md), [Spark SQL](../06-spark-sql/README.md),
  [PySpark](../07-pyspark/README.md), [Catalyst/Tungsten](../09-catalyst-tungsten/README.md).
- Lineage ⇄ [fault tolerance](../../10-data-pipelines/05-fault-tolerance/README.md).

## Exercícios

1. Escreva a mesma lógica (filtrar + agregar) em RDD e em DataFrame; compare a clareza e explique por
   que o DataFrame é mais rápido.
2. Explique como a lineage permite ao Spark recuperar uma partição perdida.
3. Dê um caso em que o RDD ainda faz sentido e outro em que o DataFrame é claramente melhor.
4. Rode `explain()` num DataFrame e identifique a lineage/plano.

## Referências

- Zaharia et al. "Resilient Distributed Datasets" (NSDI 2012).
- Chambers & Zaharia, *Spark: The Definitive Guide*.
- Documentação do Spark — RDD Programming Guide, DataFrame API.
