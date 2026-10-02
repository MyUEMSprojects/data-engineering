# PyArrow

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

## O que é

**Apache Arrow** é um **formato colunar em memória** padronizado e independente de
linguagem. **PyArrow** é a implementação Python. Arrow é o "tecido conjuntivo" do
ecossistema de dados moderno: pandas, Polars, DuckDB, Spark, DataFusion e os leitores
de [Parquet](../../08-data-formats/04-parquet/README.md) usam Arrow por baixo.

## Por que importa (o problema que resolve)

Antes do Arrow, cada ferramenta tinha seu próprio formato em memória — mover dados
entre elas exigia serializar/desserializar (lento e caro). Arrow define um layout
colunar **único**, permitindo:

- **Zero-copy / troca barata** entre ferramentas (pandas ↔ Polars ↔ Spark) sem
  conversão.
- **Eficiência colunar** (vetorização SIMD, boa compressão).
- **Leitura/escrita de Parquet** performática (PyArrow é a engine por trás de
  `read_parquet`/`to_parquet`).
- **IPC/Flight** para transportar dados entre processos/máquinas eficientemente.

Você raramente escreve "só PyArrow" para análise; mas entende-lo explica *por que*
pandas 2.x, Polars e Parquet são rápidos, e permite I/O e interoperabilidade de baixo
nível quando necessário.

## Conceitos centrais

```python
import pyarrow as pa

arr = pa.array([1, 2, None, 4])              # ChunkedArray/Array colunar
tabela = pa.table({"id": [1, 2], "valor": [9.9, 5.0]})   # pa.Table (colunas)
tabela.schema                                 # tipos por coluna
tabela.num_rows, tabela.column_names
```

- **Array** — uma coluna tipada (com suporte nativo a nulos via *bitmap*).
- **Table** — coleção de colunas (um "DataFrame" Arrow).
- **Schema** — tipos e metadados; base para [schema evolution](../../08-data-formats/10-schema-evolution/README.md).

## Parquet com PyArrow

```python
import pyarrow.parquet as pq
import pyarrow as pa

# escrever
pq.write_table(tabela, "vendas.parquet", compression="zstd")

# ler só algumas colunas e com filtro (predicate/projection pushdown)
t = pq.read_table(
    "vendas.parquet",
    columns=["id", "valor"],
    filters=[("uf", "=", "SP")],          # pushdown: pula row groups que não casam
)

# metadados sem ler os dados
meta = pq.read_metadata("vendas.parquet")
meta.num_rows, meta.row_group(0).column(0).statistics
```

Ler só as colunas e aplicar `filters` evita trazer dados desnecessários — a base da
performance analítica.

## Datasets particionados

```python
import pyarrow.dataset as ds

dataset = ds.dataset("lake/vendas/", format="parquet", partitioning="hive")
# lê "dt=2024-01-01/uf=SP/..." entendendo as partições como colunas
t = dataset.to_table(filter=(ds.field("dt") == "2024-01-01"))
```

`pyarrow.dataset` lê diretórios particionados (estilo Hive) com *partition pruning* —
exatamente o padrão de um [data lake](../../14-data-lake/05-partitioning/README.md).

## Interoperabilidade (o superpoder)

```python
import pandas as pd, polars as pl

df_pd = tabela.to_pandas()                 # Arrow -> pandas
tbl   = pa.Table.from_pandas(df_pd)        # pandas -> Arrow
df_pl = pl.from_arrow(tabela)              # Arrow -> Polars (zero-copy)
tbl2  = df_pl.to_arrow()                   # Polars -> Arrow
```

Como todos falam Arrow, mover dados entre eles é quase gratuito. É por isso que você
pode ler com PyArrow, transformar com Polars e entregar a pandas sem cópias caras.

## pandas com backend Arrow

```python
df = pd.read_parquet("x.parquet", dtype_backend="pyarrow")
```

Usa tipos Arrow dentro do pandas 2.x → melhor memória, strings eficientes e nulos
consistentes. Recomendado para dados com muito texto.

## Tipos e nulos

Arrow tem um sistema de tipos rico (int8..int64, float, string, timestamp com tz,
`list`, `struct`, `decimal`) e representa **nulos nativamente** (diferente do pandas
clássico, que usava `NaN`/`object`). Isso o torna ideal para preservar schema entre
sistemas e formatos.

## Arrow Flight (menção)

Protocolo de alta performance para transportar dados Arrow pela rede (muito mais
rápido que ODBC/JDBC para grandes volumes) — usado por sistemas que servem dados a
clientes analíticos.

## Quando você usa PyArrow diretamente

- Ler/escrever Parquet/Datasets com controle fino (colunas, filtros, compressão).
- Converter entre formatos/ferramentas preservando tipos.
- Trabalhar com schemas explicitamente (validação, evolução).
- I/O com object storage via `pyarrow.fs` (S3/GCS).

Para transformação do dia a dia, prefira [Polars](../12-polars/README.md)/
[pandas](../11-pandas/README.md) (que usam Arrow por baixo) — eles são a API
ergonômica sobre o Arrow.

## Erros comuns

- Reescrever manualmente em PyArrow o que Polars/pandas já fazem mais claro.
- Ignorar `columns=`/`filters=` ao ler Parquet (traz dados demais).
- Confundir Arrow (memória) com Parquet (arquivo em disco) — são complementares:
  Parquet é o formato em disco, Arrow o formato em memória.

## Boas práticas

- Parquet + compressão (`zstd`/`snappy`) para armazenamento.
- Leia só colunas/partições necessárias (pushdown).
- Use Arrow como ponte entre ferramentas (zero-copy).
- `dtype_backend="pyarrow"` no pandas para dados textuais.

## Relação com outros conceitos

- Formato em disco correspondente: [Parquet](../../08-data-formats/04-parquet/README.md),
  [row vs columnar](../../08-data-formats/08-row-vs-columnar/README.md).
- Base de [pandas](../11-pandas/README.md) e [polars](../12-polars/README.md).
- I/O de [data lake](../../14-data-lake/README.md) e
  [object storage](../../19-cloud/02-object-storage/README.md).

## Exercícios

1. Escreva uma `pa.Table` em Parquet com compressão zstd e releia só 2 colunas com
   um filtro.
2. Leia um diretório particionado (`dt=.../uf=...`) com `pyarrow.dataset` e aplique
   *partition pruning*.
3. Converta Arrow → Polars → Arrow → pandas e confirme que os tipos se preservam.
4. Explique a diferença entre Arrow (memória) e Parquet (disco) e por que são
   usados juntos.

## Referências

- Apache Arrow (arrow.apache.org) e PyArrow docs.
- Documentação do formato Parquet.
