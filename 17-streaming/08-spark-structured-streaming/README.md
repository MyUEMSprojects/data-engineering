# Spark Structured Streaming

> 🟣 Distributed Systems · Parte de [17 — Streaming](../README.md)

## O que é

**Structured Streaming** é a engine de streaming do [Spark](../../16-distributed-processing/05-apache-spark/README.md).
Trata um stream como uma **tabela ilimitada** que cresce continuamente: você escreve a mesma API
[DataFrame/SQL](../../16-distributed-processing/06-spark-sql/README.md) do batch, e o Spark a executa
incrementalmente. Por padrão usa **micro-batch** (latência ~segundos); há modo de processamento
contínuo experimental de menor latência.

## Por que usar

- **Código unificado** batch/streaming (mesmas APIs, mesmo [Catalyst](../../16-distributed-processing/09-catalyst-tungsten/README.md)).
- Integra-se ao ecossistema Spark: [lakehouse](../../15-lakehouse/README.md) (Delta/Iceberg),
  [Kafka](../../18-message-brokers/README.md), MLlib.
- [Exactly-once](../04-delivery-semantics/README.md) com checkpoint + sinks idempotentes/transacionais.
- Ótimo quando você já usa Spark/Databricks e latência de segundos basta.

## Modelo

```text
Fonte (Kafka/arquivos) ─► "tabela de entrada ilimitada" ─► query (DataFrame/SQL) ─► tabela de resultado ─► sink
   a cada trigger: processa o novo incremento e atualiza o resultado
```

## Exemplo (PySpark)

```python
from pyspark.sql import functions as F

raw = (spark.readStream.format("kafka")
       .option("kafka.bootstrap.servers", "broker:9092")
       .option("subscribe", "pedidos").load())

pedidos = (raw.select(F.from_json(F.col("value").cast("string"), schema).alias("p"))
              .select("p.*"))

agg = (pedidos
       .withWatermark("event_ts", "10 minutes")                  # tolera 10 min de atraso
       .groupBy(F.window("event_ts", "5 minutes"), "uf")
       .agg(F.sum("valor").alias("receita")))

(agg.writeStream
    .outputMode("update")
    .format("delta")
    .option("checkpointLocation", "s3://bucket/chk/receita")     # estado + offsets
    .trigger(processingTime="30 seconds")
    .start("s3://bucket/lake/receita_5min"))
```

## Conceitos-chave

- **Output modes** — `append` (só linhas finalizadas), `update` (linhas alteradas), `complete` (tabela
  inteira; só para agregações pequenas).
- **Triggers** — `processingTime` (intervalo), `availableNow` (processa o backlog e para — ótimo para
  "streaming como batch incremental"), `continuous`.
- **Watermark** — `withWatermark` define o atraso tolerado e permite limpar estado antigo (ver
  [janelas](../03-time-and-windows/README.md)).
- **Checkpoint** (`checkpointLocation`) — offsets + estado; **obrigatório** em produção (ver
  [stateful](../05-stateful-processing/README.md)).
- **foreachBatch** — aplica lógica batch arbitrária a cada micro-batch (ex.: `MERGE` em tabela Delta
  para upsert idempotente).

```python
def upsert(batch_df, batch_id):
    DeltaTable.forName(spark, "vendas").alias("t") \
        .merge(batch_df.alias("s"), "t.id = s.id") \
        .whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

stream.writeStream.foreachBatch(upsert).option("checkpointLocation", chk).start()
```

## Trade-offs

- **Latência de segundos**, não ms (para ms use [Flink](../07-flink/README.md)/[Kafka Streams](../06-kafka-streams/README.md)).
- Menos flexível para lógica de estado/tempo complexa que o Flink.
- Muitos micro-batches pequenos geram [small files](../../14-data-lake/06-small-files-compaction/README.md)
  no lake (compacte / ajuste trigger).
- Mudar a query pode invalidar o checkpoint.

## Quando usar / não usar

- **Use** se já está no Spark/Databricks, aceita latência de segundos e quer reaproveitar código/skills
  batch e escrever em lakehouse.
- **Evite** para latência de milissegundos ou lógica stateful/CEP sofisticada.

## Erros comuns

- Sem `checkpointLocation` (perde progresso/duplica no restart).
- Sem watermark em agregações com janela (estado cresce sem limite).
- `complete` mode em agregação grande.
- Sink não-idempotente (duplicatas em retry).
- Ignorar small files gerados por triggers muito frequentes.

## Boas práticas

- Checkpoint em storage durável por query; watermark em agregações com estado.
- `foreachBatch` + `MERGE` para upserts idempotentes em lakehouse.
- `trigger(availableNow=True)` para pipelines incrementais baratos e agendáveis.
- Monitore input rate, processing time e batch duration (Spark UI/StreamingQueryListener).

## Relação com outros conceitos

- [Spark](../../16-distributed-processing/05-apache-spark/README.md), [PySpark](../../16-distributed-processing/07-pyspark/README.md),
  [janelas](../03-time-and-windows/README.md), [delivery semantics](../04-delivery-semantics/README.md).
- [Lakehouse](../../15-lakehouse/README.md), [Kafka](../../18-message-brokers/README.md);
  usado no [Projeto 08](../../projects/08-streaming/README.md).

## Exercícios

1. Leia de Kafka, agregue por janela de 5 min com watermark e grave em Delta com checkpoint.
2. Diferencie output modes `append`, `update` e `complete`.
3. Implemente um upsert idempotente com `foreachBatch` + `MERGE`.
4. Explique `availableNow` e quando é melhor que um stream contínuo.

## Referências

- Documentação do Spark Structured Streaming Programming Guide.
- Chambers & Zaharia, *Spark: The Definitive Guide* — streaming.
