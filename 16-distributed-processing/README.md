# 16 — Distributed Data Processing

> 🟣 Nível 5 — Distributed Systems · Pré:
> [01/05 — Sistemas distribuídos](../01-foundations/05-distributed-systems-fundamentals/README.md),
> [04 — Python](../04-python-for-data-engineering/README.md) · Próximo:
> [17 — Streaming](../17-streaming/README.md)

Quando os dados **não cabem em uma máquina** (ou cabem, mas processar neles demoraria demais),
recorre-se ao **processamento distribuído**: dividir o trabalho entre muitos nós que processam em
paralelo. Este módulo cobre os **fundamentos** (MapReduce, shuffle, skew) e a ferramenta dominante:
**Apache Spark**.

## Por que importa

Spark é uma das tecnologias centrais de DE em escala. Mas antes de usá-lo bem, você precisa entender
*por que* operações como `JOIN` e `GROUP BY` são caras em sistemas distribuídos (**shuffle**) e como
o paralelismo realmente funciona — senão você escreve código Spark que "funciona" mas é lento e caro.

> Nota de pragmatismo: nem tudo precisa de Spark. Para dados que cabem num servidor,
> [polars](../04-python-for-data-engineering/12-polars/README.md)/DuckDB costumam ser mais simples e
> rápidos. Use Spark quando a escala **exigir** distribuição.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Fundamentos](01-fundamentals/README.md) | Paralelismo, data locality, modelo distribuído |
| 02 | [MapReduce](02-mapreduce/README.md) | O modelo que originou tudo |
| 03 | [Partitioning e shuffle](03-partitioning-shuffle/README.md) | A operação mais cara |
| 04 | [Distributed joins e skew](04-distributed-joins-skew/README.md) | Juntar dados entre nós |
| 05 | [Apache Spark](05-apache-spark/README.md) | Arquitetura e conceitos |
| 06 | [Spark SQL](06-spark-sql/README.md) | SQL sobre dados distribuídos |
| 07 | [PySpark](07-pyspark/README.md) | A API Python do Spark |
| 08 | [RDD e DataFrame](08-rdd-dataframe/README.md) | As abstrações de dados |
| 09 | [Catalyst e Tungsten](09-catalyst-tungsten/README.md) | O otimizador e a execução |
| 10 | [Caching e broadcast](10-caching-broadcast/README.md) | Reuso e joins eficientes |
| 11 | [Performance tuning](11-performance-tuning/README.md) | Spark rápido e barato |

## Dependências internas

```text
Fundamentos ─► MapReduce ─► Partitioning/shuffle ─► Distributed joins/skew
                                     │
                     Apache Spark ───┤
                       ├─ Spark SQL  │
                       ├─ PySpark    │
                       ├─ RDD/DataFrame
                       └─ Catalyst/Tungsten
                                     │
                     Caching/broadcast ─► Performance tuning
```

## Checkpoint

- [ ] Explicar paralelismo, particionamento e *data locality*.
- [ ] Descrever o modelo MapReduce (map → shuffle → reduce).
- [ ] Explicar por que *shuffle* é caro e o que o causa.
- [ ] Reconhecer e mitigar *data skew* em joins/agregações.
- [ ] Descrever a arquitetura do Spark (driver, executors, stages, tasks).
- [ ] Usar Spark SQL/PySpark/DataFrame e saber quando usar RDD.
- [ ] Explicar o papel do Catalyst (otimizador) e do Tungsten (execução).
- [ ] Usar cache e broadcast join; aplicar técnicas de tuning.

## Referências do módulo

- Chambers, B.; Zaharia, M. *Spark: The Definitive Guide*. O'Reilly, 2018.
- Dean, J.; Ghemawat, S. "MapReduce" (Google), 2004.
- Documentação oficial do Apache Spark.
- Kleppmann, M. *DDIA* — cap. 10 (batch processing).
