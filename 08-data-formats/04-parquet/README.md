# Parquet

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

**Apache Parquet** é um formato de arquivo **colunar**, binário, comprimido e com schema,
projetado para **analytics**. É o formato padrão de *data lakes*, *lakehouses* e da maior
parte do processamento analítico moderno ([Spark](../../16-distributed-processing/README.md),
[warehouses](../../13-data-warehouse/README.md), [polars](../../04-python-for-data-engineering/12-polars/README.md),
DuckDB). Se você aprender **um** formato a fundo, aprenda este.

## Por que existe / que problema resolve

Formatos de texto ([CSV](../01-csv/README.md)/[JSON](../02-json-jsonl/README.md)) são
lentos e caros para analytics: sem tipos, sem compressão eficiente, e **orientados a
linha** (para somar uma coluna, leem tudo). Parquet resolve guardando os dados **por
coluna** ([columnar](../08-row-vs-columnar/README.md)), com compressão forte, estatísticas
e schema embutido.

## Como funciona (estrutura interna)

```text
Arquivo Parquet
├── Row Group 1            (bloco de N linhas)
│   ├── Column Chunk: id      (todos os ids do grupo, juntos)
│   │   └── Pages (+ estatísticas: min, max, count, nulls)
│   ├── Column Chunk: valor
│   └── Column Chunk: uf
├── Row Group 2 ...
└── Footer (schema + metadados + localização dos row groups/estatísticas)
```

- **Row groups** — o arquivo é dividido em grupos de linhas; dentro de cada grupo, os
  dados são organizados **por coluna** (*column chunks*).
- **Estatísticas por chunk/page** (min, max, nulls) no footer → permitem **pular** blocos
  que não interessam (*predicate pushdown* / *data skipping*).
- **Schema no footer** — autoexplicativo e tipado.
- **Encodings** — *dictionary encoding* (ótimo para baixa cardinalidade), *run-length*,
  *delta* → compressão muito eficiente.

## As superpotências do Parquet

### 1. Column pruning (projeção)

Lê **só as colunas** que a query pede. `SELECT valor` não toca as outras colunas — menos
I/O, menos custo (em BigQuery/Athena você paga por bytes lidos!).

### 2. Predicate pushdown (data skipping)

Usando as estatísticas (min/max por row group), pula blocos inteiros que não satisfazem o
filtro. `WHERE valor > 1000` ignora row groups cujo `max(valor) <= 1000`.

### 3. Compressão superior

Valores semelhantes ficam juntos (mesma coluna) → comprime muito melhor que formatos de
linha. Codecs: snappy (padrão, rápido), gzip, zstd (ver
[compressão](../09-compression/README.md)).

### 4. Schema + tipos ricos

Tipos nativos (int, float, decimal, timestamp, boolean, binary) e **estruturas aninhadas**
(listas, structs/maps) via o modelo *Dremel* (repetition/definition levels).

## Lendo/escrevendo

```python
import pandas as pd
df.to_parquet("vendas.parquet", compression="zstd", index=False)
df = pd.read_parquet("vendas.parquet", columns=["id", "valor"])   # só 2 colunas!

import polars as pl
pl.scan_parquet("lake/vendas/*.parquet").filter(pl.col("valor") > 1000).collect()

import pyarrow.parquet as pq
pq.read_table("vendas.parquet", columns=["id"], filters=[("uf", "=", "SP")])
```

Ver [PyArrow](../../04-python-for-data-engineering/13-pyarrow/README.md) (a engine por
trás da maioria dos leitores Parquet).

## Particionamento (Hive-style)

Em lakes, Parquet é organizado em diretórios particionados — o valor da partição vira um
"filtro grátis" (*partition pruning*):

```text
lake/vendas/dt=2024-01-01/uf=SP/part-0.parquet
lake/vendas/dt=2024-01-01/uf=RJ/part-0.parquet
```

Uma query `WHERE dt='2024-01-01' AND uf='SP'` lê **só aquele diretório**. Ver
[partitioning no lake](../../14-data-lake/05-partitioning/README.md).

## Trade-offs e limitações

- **Write-once, read-many** — Parquet é imutável; atualizar/deletar linhas exige reescrever
  arquivos. Para mutações/ACID sobre Parquet, use [lakehouse](../../15-lakehouse/README.md)
  (Delta/Iceberg/Hudi) por cima.
- **Não é para OLTP** nem para escrita linha a linha (é colunar, batch).
- **Small files problem** — muitos arquivos Parquet minúsculos degradam performance
  (overhead de footer/abertura) → precisa de [compaction](../../14-data-lake/06-small-files-compaction/README.md).
- **Row group size** importa — muito pequeno perde eficiência; muito grande pesa na
  memória. (~128 MB–1 GB é comum.)

## Parquet vs ORC vs Avro

| | Parquet | [ORC](../06-orc/README.md) | [Avro](../05-avro/README.md) |
| --- | --- | --- | --- |
| Layout | colunar | colunar | linha |
| Uso | analytics (padrão) | analytics (Hive) | streaming/serialização |
| Ecossistema | universal | Hive/Hadoop | Kafka |

## Erros comuns

- Usar CSV/JSON onde Parquet seria muito mais barato/rápido.
- Não aproveitar `columns=`/`filters=` (ler tudo e descartar depois).
- Over-partitioning → *small files*.
- Esperar atualizar linhas in-place (precisa de lakehouse).
- Row groups mal dimensionados.

## Boas práticas

- Parquet nas camadas refinadas do lake/warehouse; particione por data/chave relevante.
- Explore column pruning + predicate pushdown (selecione colunas, filtre por partição).
- Compressão zstd/snappy conforme o trade-off; dimensione row groups.
- Compacte small files; use lakehouse para ACID/updates.

## Relação com outros conceitos

- Conceito base: [row vs columnar](../08-row-vs-columnar/README.md).
- Engine: [PyArrow/Arrow](../../04-python-for-data-engineering/13-pyarrow/README.md).
- Usado em [data lake](../../14-data-lake/README.md),
  [lakehouse](../../15-lakehouse/README.md), [Spark](../../16-distributed-processing/README.md).

## Exercícios

1. Converta um CSV grande em Parquet e compare: tamanho em disco e tempo de somar uma
   coluna.
2. Leia só 2 colunas com filtro e confirme (via tempo/bytes) o pruning.
3. Grave um dataset particionado por data e mostre o *partition pruning* numa leitura.
4. Explique por que atualizar uma linha num Parquet exige reescrever o arquivo e como o
   lakehouse contorna isso.

## Referências

- Documentação do Apache Parquet (parquet.apache.org).
- Melnik et al. "Dremel" (modelo de dados aninhados).
- Apache Arrow / PyArrow docs.
