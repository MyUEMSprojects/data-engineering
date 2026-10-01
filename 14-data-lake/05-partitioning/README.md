# Partitioning (no data lake)

> 🔵 Analytics Platforms · Parte de [14 — Data Lake](../README.md)

## O que é

Particionar um data lake é organizar os arquivos em **diretórios por valor de coluna** (geralmente
data), de modo que consultas que filtram por essa coluna leiam **apenas os diretórios relevantes**
(*partition pruning*). É a principal técnica de performance e custo em lakes — o equivalente ao
[particionamento de warehouse](../../13-data-warehouse/03-partitioning-clustering/README.md), mas
sobre arquivos em [object storage](../02-object-storage/README.md).

## Hive-style partitioning

O padrão de fato: `coluna=valor` no caminho dos arquivos.

```text
lake/vendas/
├── dt=2024-01-01/
│   ├── uf=SP/part-0.parquet
│   └── uf=RJ/part-0.parquet
├── dt=2024-01-02/
│   └── ...
```

Engines ([Spark](../../16-distributed-processing/README.md),
[polars](../../04-python-for-data-engineering/12-polars/README.md),
[PyArrow datasets](../../04-python-for-data-engineering/13-pyarrow/README.md), Trino) **entendem**
esse padrão: `dt` e `uf` viram colunas, e um filtro `WHERE dt='2024-01-01'` lê só aquele diretório.

```python
import pyarrow.dataset as ds
d = ds.dataset("s3://bucket/lake/vendas/", partitioning="hive")
d.to_table(filter=ds.field("dt") == "2024-01-01")   # partition pruning
```

## Por que importa

- **Partition pruning** — ler só os arquivos necessários (menos I/O, menos requests, menos custo —
  crucial em object storage, onde listar/ler custa).
- **Overwrite/retenção por partição** — reprocessar ou descartar um período é operar um diretório
  (ver [loading](../../09-etl-elt/04-loading/README.md),
  [idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Paralelismo** — engines processam partições em paralelo.

## Escolhendo a chave de partição

- **Por data** é quase sempre a melhor escolha primária (filtros temporais são os mais comuns, e
  habilita retenção/incremental — ver
  [incremental](../../09-etl-elt/05-full-vs-incremental/README.md)).
- Uma **segunda** chave (ex.: `uf`, `pais`) só se tiver **cardinalidade moderada** e for filtrada
  com frequência.
- A chave deve: **casar com os filtros** das queries e **distribuir** os dados razoavelmente (ver
  [particionamento/sharding](../../06-databases/06-partitioning-sharding/README.md)).

## O perigo: over-partitioning → small files

Particionar por uma coluna de **alta cardinalidade** (ex.: `cliente_id`, ou `dt` + `hora` + `uf`)
cria **milhares de partições minúsculas**, cada uma com arquivos pequenos → o
[small files problem](../06-small-files-compaction/README.md): listas lentas, muitas requests,
overhead de metadados, e performance pior que **sem** particionar.

```text
BOM:    dt=2024-01-01/  (365 partições/ano, arquivos de ~100-500 MB)
RUIM:   dt=2024-01-01/hora=14/uf=SP/cliente=12345/  (milhões de partições minúsculas)
```

Regra: particione o suficiente para pruning, **não** a ponto de fragmentar. Granularidade
**diária** é o equilíbrio usual; evite particionar por chaves de alta cardinalidade.

## Partition pruning depende do filtro

O pruning só ocorre se você **filtrar pela coluna de partição diretamente**. Aplicar função
(`WHERE DATE(event_ts)='...'` quando a partição é `dt`) ou filtrar por coluna não particionada lê
tudo (ver [query optimization](../../13-data-warehouse/04-query-optimization/README.md)).

## Partitioning vs clustering/Z-ordering

Particionar divide em diretórios; dentro deles, **ordenar/clusterizar** os dados (Z-order no
[Delta](../../15-lakehouse/04-delta-lake/README.md), sort no [Iceberg](../../15-lakehouse/05-apache-iceberg/README.md))
melhora o *data skipping* por arquivo para colunas secundárias — sem criar mais partições. Em
lakehouses, isso costuma ser preferível a over-partitionar.

## Erros comuns

- **Over-partitioning** (alta cardinalidade) → small files, performance pior.
- Não particionar tabelas grandes → toda query varre tudo.
- Filtrar por coluna não particionada (sem pruning).
- Função sobre a coluna de partição no filtro (quebra pruning).
- Partições desbalanceadas ([skew](../../16-distributed-processing/04-distributed-joins-skew/README.md)).

## Boas práticas

- Particione por **data** (granularidade diária típica); segunda chave só se moderada e filtrada.
- Mire arquivos de tamanho saudável (~128 MB–1 GB) por partição.
- Filtre pela coluna de partição diretamente.
- Para colunas secundárias, prefira clustering/Z-order a mais partições.
- Monitore o nº de arquivos/partição (evite small files).

## Relação com outros conceitos

- [Object storage](../02-object-storage/README.md),
  [small files/compaction](../06-small-files-compaction/README.md),
  [Parquet](../../08-data-formats/04-parquet/README.md).
- Similar ao [warehouse partitioning](../../13-data-warehouse/03-partitioning-clustering/README.md);
  Z-order no [lakehouse](../../15-lakehouse/README.md).

## Exercícios

1. Organize um lake de vendas particionado por `dt` e mostre o pruning num filtro de data.
2. Explique por que particionar por `cliente_id` causaria small files.
3. Mostre por que `WHERE DATE(event_ts)='...'` pode não usar o pruning da partição `dt`.
4. Compare adicionar uma segunda partição vs usar clustering/Z-order para uma coluna secundária.

## Referências

- Documentação de partitioning do Spark, Hive, PyArrow datasets.
- Delta Lake / Iceberg — partitioning e Z-ordering.
