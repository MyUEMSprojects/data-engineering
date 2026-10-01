# Spark SQL

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## O que é

**Spark SQL** é o módulo do [Spark](../05-apache-spark/README.md) para processar dados estruturados
com **SQL** (ou com a API [DataFrame](../08-rdd-dataframe/README.md), que é equivalente por baixo).
Você escreve SQL/DataFrame; o [Catalyst](../09-catalyst-tungsten/README.md) otimiza e executa de forma
distribuída. É a forma recomendada de usar Spark para a maioria dos casos de DE.

## Por que usar Spark SQL

- **Familiar** — quem sabe [SQL](../../05-sql/README.md) já é produtivo em escala distribuída.
- **Otimizado** — SQL e DataFrame passam pelo **mesmo otimizador** (Catalyst); não há penalidade por
  usar SQL em vez da API.
- **Unificado** — a mesma engine lê [lake/lakehouse](../../15-lakehouse/README.md),
  [warehouse](../../13-data-warehouse/README.md), [Kafka](../../18-message-brokers/README.md),
  [Parquet](../../08-data-formats/04-parquet/README.md), JDBC.
- **Interoperável** — misture SQL e DataFrame livremente.

## Duas formas, mesma engine

```python
# via API DataFrame
df = spark.read.parquet("s3://.../vendas")
(df.filter("status = 'pago'")
   .groupBy("uf").agg(F.sum("valor").alias("receita"))
   .orderBy(F.desc("receita")))

# via SQL (idêntico por baixo)
df.createOrReplaceTempView("vendas")
spark.sql("""
    select uf, sum(valor) as receita
    from vendas where status = 'pago'
    group by uf order by receita desc
""")
```

Ambas geram o mesmo plano otimizado. Escolha pela legibilidade do caso.

## Lendo e escrevendo

```python
spark.read.parquet("s3://.../vendas")
spark.read.format("delta").load("...")              # lakehouse
spark.read.option("header", True).csv("...")
spark.read.format("jdbc").options(url=..., dbtable=...).load()   # banco

df.write.mode("overwrite").partitionBy("dt").parquet("s3://.../out")   # particionado
df.write.format("delta").mode("append").saveAsTable("db.vendas")
```

Prefira [Parquet](../../08-data-formats/04-parquet/README.md)/[lakehouse](../../15-lakehouse/README.md)
e **particione por data** na escrita (ver [partitioning](../../14-data-lake/05-partitioning/README.md)).

## Catalog e tabelas

Spark SQL tem um **catálogo** (metastore — ver [metadata](../../14-data-lake/07-metadata/README.md))
com tabelas e views:

- **Temp views** — existem só na sessão (`createOrReplaceTempView`).
- **Managed/external tables** — persistentes no metastore (Hive/Glue/Unity Catalog).
- Com [lakehouse](../../15-lakehouse/README.md), as tabelas são Delta/Iceberg (ACID, time travel).

## Recursos de SQL analítico

Spark SQL suporta o SQL analítico que você já conhece (ver
[SQL analítico](../../05-sql/13-analytical-sql/README.md)):
[window functions](../../05-sql/05-window-functions/README.md), CTEs, `GROUPING SETS`, funções de
data, arrays/structs (dados aninhados), UDFs. A maior parte do seu conhecimento de SQL transfere
direto.

## Performance (pontos específicos)

- **Predicate/projection pushdown** — filtrar e selecionar colunas empurra para a leitura do
  Parquet/fonte (menos I/O) — ver [Parquet](../../08-data-formats/04-parquet/README.md).
- **Partition pruning** — filtrar pela coluna de partição lê só os diretórios certos.
- **AQE** — otimização adaptativa em runtime (coalesce de partições, skew join) — mantenha ligado.
- **Broadcast join** — automático para tabelas pequenas (configurável) — ver
  [broadcast](../10-caching-broadcast/README.md).
- Minimize [shuffle](../03-partitioning-shuffle/README.md) (filtre/pré-agregue antes).
- `df.explain()` mostra o plano (procure `Exchange`/`Scan` com pushdown).

## UDFs: use com parcimônia

Funções nativas do Spark SQL são otimizadas ([Tungsten](../09-catalyst-tungsten/README.md), código
gerado). **UDFs Python** quebram essas otimizações e são lentas (serialização Python↔JVM). Prefira
funções nativas; se precisar de UDF, considere **pandas UDFs** (vetorizadas, via Arrow). Ver
[PySpark](../07-pyspark/README.md).

## Erros comuns

- `collect()`/`toPandas()` de resultados grandes para o driver (OOM).
- UDF Python onde uma função nativa resolveria (lento).
- Não particionar na escrita / `SELECT *` (lê demais).
- Ignorar o `explain()`/Spark UI ao otimizar.
- Esquecer que SQL e DataFrame têm a mesma performance (debater "qual é mais rápido").

## Boas práticas

- Use SQL/DataFrame (não RDD); funções nativas em vez de UDFs Python.
- Leia Parquet/lakehouse, filtre/projete cedo (pushdown), particione na escrita.
- Mantenha AQE ligado; leia o `explain()`.
- Agregue/filtre antes de joins; aproveite broadcast.

## Relação com outros conceitos

- [Spark](../05-apache-spark/README.md), [DataFrame](../08-rdd-dataframe/README.md),
  [Catalyst](../09-catalyst-tungsten/README.md), [PySpark](../07-pyspark/README.md).
- [SQL](../../05-sql/README.md), [Parquet](../../08-data-formats/04-parquet/README.md),
  [lakehouse](../../15-lakehouse/README.md).

## Exercícios

1. Escreva a mesma agregação em SQL e em DataFrame e compare o `explain()` (devem ser iguais).
2. Leia um Parquet particionado, filtre por partição e confirme o pruning no plano.
3. Substitua uma UDF Python por uma função nativa e meça a diferença.
4. Escreva um resultado particionado por data em formato Delta/Parquet.

## Referências

- Documentação do Spark SQL (spark.apache.org/sql).
- Chambers & Zaharia, *Spark: The Definitive Guide*.
