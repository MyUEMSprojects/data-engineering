# Small files e compaction

> 🔵 Analytics Platforms · Parte de [14 — Data Lake](../README.md)

## O que é

O **small files problem** é a degradação de performance e custo causada por ter **muitos arquivos
pequenos** num data lake, em vez de poucos arquivos de tamanho adequado. **Compaction** é o
processo de **juntar** esses arquivos pequenos em arquivos maiores para resolver o problema.

## Por que arquivos pequenos são um problema

Em [object storage](../02-object-storage/README.md), **cada arquivo tem um custo fixo** de
abertura/listagem/leitura, independentemente do tamanho:

- **Overhead por arquivo** — abrir 1 milhão de arquivos de 1 KB é muito mais lento que 10 arquivos
  de 100 MB, mesmo com o mesmo volume total.
- **Listagem lenta** — listar um prefixo com milhões de objetos é caro/lento (object storage não é
  filesystem).
- **Custo de requests** — muitas operações `GET`/`LIST` (object storage cobra por request).
- **Metadados/planejamento** — engines ([Spark](../../16-distributed-processing/README.md),
  Trino) gastam tempo planejando sobre tantos arquivos; o *footer* de cada
  [Parquet](../../08-data-formats/04-parquet/README.md) precisa ser lido.
- **Compressão/encoding pior** — arquivos minúsculos não aproveitam bem a compressão colunar nem
  row groups adequados.

```text
1.000.000 arquivos de 1 KB  ≈ 1 GB, mas LENTÍSSIMO (overhead domina)
10 arquivos de 100 MB       ≈ 1 GB, RÁPIDO
```

## De onde vêm os small files

- **Streaming / micro-batches** — cada micro-lote escreve um arquivo pequeno (a causa nº 1).
- **Over-partitioning** — particionar por alta cardinalidade fragmenta em muitas partições
  minúsculas (ver [partitioning](../05-partitioning/README.md)).
- **Muitas tarefas de escrita** — cada partição/worker do Spark grava um arquivo (ex.: 200
  partições → 200 arquivos por carga).
- **Cargas frequentes** — ingerir de hora em hora cria muitos arquivos por dia.

## Tamanho de arquivo ideal

Mire arquivos de **~128 MB a 1 GB** (alinhado ao tamanho de bloco/row group e ao paralelismo das
engines). Pequeno demais = overhead; grande demais = menos paralelismo e picos de memória.

## Compaction (a solução)

Juntar arquivos pequenos em maiores, periodicamente:

### Manual / em batch

Ler os arquivos de uma partição e reescrevê-los consolidados (controlando o nº de arquivos de
saída):

```python
# Spark: reduz o nº de arquivos de saída de uma partição
(spark.read.parquet("s3://bucket/lake/vendas/dt=2024-01-15/")
      .repartition(4)                       # ou coalesce
      .write.mode("overwrite")
      .parquet("s3://bucket/lake/vendas/dt=2024-01-15/"))
```

(Cuidado: faça de forma [idempotente](../../09-etl-elt/07-idempotency-retries/README.md) e atômica
para não corromper leituras concorrentes — um motivo a mais para lakehouse.)

### Lakehouse: compaction gerenciado

[Lakehouses](../../15-lakehouse/README.md) resolvem isso de forma segura e integrada:

- **Delta Lake** — `OPTIMIZE` (bin-packing) + Z-ordering; *auto-compaction* / *optimize write*.
- **Iceberg** — `rewrite_data_files` (procedure de compaction).
- **Hudi** — compaction nativo (especialmente no modo MoR — Merge-on-Read).

Como têm transações, compactam **sem** quebrar leituras concorrentes (commit atômico) — a forma
recomendada.

## Prevenção (melhor que compactar depois)

- **Não over-partitionar** (evite chaves de alta cardinalidade).
- **Controlar o nº de arquivos de escrita** (`coalesce`/`repartition` no Spark; *target file size*).
- **Acumular em micro-batches maiores** no streaming (trade-off com latência).
- **Compaction agendada** como tarefa de manutenção no
  [orquestrador](../../11-orchestration/README.md).

## Erros comuns

- Streaming escrevendo milhares de arquivos minúsculos sem compaction.
- Over-partitioning criando o problema.
- Compactar de forma não-atômica e corromper leituras.
- Ignorar o problema até as queries ficarem lentas e caras.

## Boas práticas

- Mire arquivos de ~128 MB–1 GB; controle o nº de arquivos na escrita.
- Evite over-partitioning; prefira clustering/Z-order a mais partições.
- Agende compaction (lakehouse `OPTIMIZE`/`rewrite_data_files`).
- No streaming, equilibre latência vs tamanho de arquivo; compacte periodicamente.

## Relação com outros conceitos

- [Partitioning](../05-partitioning/README.md), [object storage](../02-object-storage/README.md),
  [Parquet/compressão](../../08-data-formats/04-parquet/README.md).
- [Lakehouse](../../15-lakehouse/README.md) (compaction gerenciado),
  [streaming](../../17-streaming/README.md), [Spark tuning](../../16-distributed-processing/11-performance-tuning/README.md).
- Análogo à *compaction* de [LSM-trees](../../06-databases/05-indexing/README.md).

## Exercícios

1. Explique, em termos de overhead, por que 1M de arquivos de 1 KB é pior que 10 de 100 MB.
2. Liste 3 causas comuns de small files e como preveni-las.
3. Compacte uma partição com Spark controlando o nº de arquivos de saída.
4. Descreva como o `OPTIMIZE` do Delta compacta sem quebrar leituras concorrentes.

## Referências

- Documentação de Delta Lake (`OPTIMIZE`), Iceberg (`rewrite_data_files`), Hudi (compaction).
- Guias de performance de Spark/Trino sobre small files.
