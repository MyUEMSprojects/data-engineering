# PySpark

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## O que é

**PySpark** é a API Python do [Spark](../05-apache-spark/README.md). Permite escrever jobs Spark em
Python usando [DataFrames](../08-rdd-dataframe/README.md) e [Spark SQL](../06-spark-sql/README.md). É a
forma mais comum de Data Engineers usarem Spark (por conta da fluência em
[Python](../../04-python-for-data-engineering/README.md)).

## Como funciona (e uma pegadinha importante)

O código Python roda no **driver**, mas as operações sobre DataFrame são **planos** que executam na
JVM dos executors (via Catalyst). Ou seja: você escreve Python, mas a computação pesada roda em
Scala/JVM otimizada — **desde que você use a API de DataFrame/SQL** (não loops Python sobre os dados).

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("vendas").getOrCreate()

df = spark.read.parquet("s3://.../vendas")
out = (
    df.filter(F.col("status") == "pago")
      .withColumn("receita", F.col("preco") * F.col("qtd"))
      .groupBy("uf")
      .agg(F.sum("receita").alias("total"),
           F.countDistinct("cliente_id").alias("clientes"))
      .orderBy(F.desc("total"))
)
out.write.mode("overwrite").partitionBy("uf").parquet("s3://.../out")
```

## A API de DataFrame (essencial)

```python
df.select("id", "valor")                       # projeção
df.filter(F.col("valor") > 100)                # filtro (ou df.where)
df.withColumn("nova", F.col("a") + F.col("b")) # coluna derivada
df.groupBy("uf").agg(F.sum("valor"))           # agregação
df.join(dim, on="cliente_id", how="left")      # join
df.withColumn("rn", F.row_number().over(Window.partitionBy("uf").orderBy(F.desc("valor"))))  # window
df.dropDuplicates(["id"])                       # dedupe
```

- `F` (`pyspark.sql.functions`) tem as funções nativas (otimizadas) — **prefira-as**.
- `Window` para [window functions](../../05-sql/05-window-functions/README.md).
- A API espelha o SQL e o [pandas](../../04-python-for-data-engineering/11-pandas/README.md)/
  [polars](../../04-python-for-data-engineering/12-polars/README.md), com a diferença de ser
  distribuída e lazy.

## UDFs: o maior erro de performance

Uma **UDF Python** força o Spark a serializar cada linha da JVM para o Python, executar, e serializar
de volta — lento e sem as otimizações do [Tungsten](../09-catalyst-tungsten/README.md).

```python
# LENTO: UDF Python (serialização linha a linha)
@F.udf("double")
def dobro(x): return x * 2
df.withColumn("d", dobro("valor"))

# RÁPIDO: função nativa
df.withColumn("d", F.col("valor") * 2)
```

**Regra:** use funções nativas de `F`. Se realmente precisar de lógica Python, use **pandas UDFs**
(vetorizadas, via [Arrow](../../04-python-for-data-engineering/13-pyarrow/README.md) — processam lotes,
muito mais rápidas que UDFs linha a linha):

```python
@F.pandas_udf("double")
def normaliza(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()
```

## collect/toPandas: cuidado com o driver

```python
df.collect()        # traz TODAS as linhas para o driver → OOM se grande!
df.toPandas()       # idem (converte para pandas no driver)
df.show(20)         # OK: só amostra
df.write...         # OK: escreve distribuído, sem passar pelo driver
```

Use `collect`/`toPandas` só em resultados **pequenos** (agregados finais). Para gravar, use `write`
(distribuído).

## Pandas API on Spark (ex-Koalas)

O Spark oferece `pyspark.pandas` — uma API **igual à do pandas** que roda distribuída no Spark. Útil
para migrar código pandas para escala sem reescrever tudo (com ressalvas de performance). Alternativa
ao DataFrame nativo quando a familiaridade com pandas pesa.

## Estrutura de um job PySpark

```python
def transform(df):                 # lógica PURA (DataFrame -> DataFrame), testável
    return df.filter(...).groupBy(...).agg(...)

def main():
    spark = SparkSession.builder.getOrCreate()
    src = spark.read.parquet(INPUT)
    transform(src).write.mode("overwrite").parquet(OUTPUT)

if __name__ == "__main__":
    main()
```

Separe a **transformação pura** (testável com `spark` local — ver
[pipeline testing](../../10-data-pipelines/07-pipeline-testing/README.md)) do I/O, como em qualquer
código de dados (ver [organização](../../03-git-software-engineering/07-project-organization/README.md)).

## Rodando

```bash
spark-submit --master local[*] job.py          # local
spark-submit --master k8s://... --conf ... job.py   # Kubernetes
```

Ou em notebooks/Databricks/EMR/Dataproc.

## Erros comuns

- UDF Python onde função nativa serviria (lento).
- `collect()`/`toPandas()` de dados grandes → OOM no driver.
- Loops Python iterando sobre linhas do DataFrame (anula o paralelismo).
- Não separar transformação de I/O (não testável).
- Esquecer que é lazy (nada roda até uma action).

## Boas práticas

- API DataFrame/SQL + funções nativas (`F`); pandas UDF quando precisar de Python.
- `write` para gravar (distribuído); `collect`/`toPandas` só para resultados pequenos.
- Transformações puras e testáveis; filtre/projete cedo.
- Entenda lazy/actions; use a Spark UI (ver [tuning](../11-performance-tuning/README.md)).

## Relação com outros conceitos

- [Spark](../05-apache-spark/README.md), [Spark SQL](../06-spark-sql/README.md),
  [DataFrame](../08-rdd-dataframe/README.md), [Tungsten/Arrow](../09-catalyst-tungsten/README.md).
- [Python/pandas/polars](../../04-python-for-data-engineering/README.md),
  [testes](../../10-data-pipelines/07-pipeline-testing/README.md).

## Exercícios

1. Escreva um job PySpark que lê Parquet, agrega por grupo com `F` e grava particionado.
2. Substitua uma UDF Python por função nativa e por uma pandas UDF; compare.
3. Mostre por que `toPandas()` de um DataFrame grande falha e o que usar no lugar.
4. Refatore um job separando a transformação pura do I/O e escreva um teste para ela.

## Referências

- Documentação do PySpark (spark.apache.org/docs/latest/api/python).
- Chambers & Zaharia, *Spark: The Definitive Guide*.
