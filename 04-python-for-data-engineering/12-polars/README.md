# polars

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

## O que é

**Polars** é uma biblioteca de DataFrames escrita em **Rust**, construída sobre
[Apache Arrow](../13-pyarrow/README.md). É muito mais rápida e eficiente em memória
que o pandas, usa **todos os núcleos** por padrão e oferece uma **API lazy** que
otimiza a consulta inteira antes de executar — inclusive processando dados que **não
cabem na RAM** (*streaming/out-of-core*).

## Por que importa para DE

- **Multi-core nativo** — paraleliza sem você gerenciar threads (sem a limitação do
  [GIL](../07-concurrency/README.md), pois executa em Rust).
- **Lazy + query optimizer** — faz *predicate/projection pushdown* (lê só o que
  precisa), *reordena* operações e evita materializações intermediárias.
- **Eficiência de memória** — baseado em Arrow colunar; processa arquivos maiores que
  a RAM no modo streaming.
- É frequentemente a escolha certa para o "meio-termo" entre pandas (não cabe) e
  Spark (overkill para um servidor só).

## Eager vs Lazy (o conceito central)

```python
import polars as pl

# EAGER: executa na hora (parecido com pandas)
df = pl.read_parquet("vendas.parquet")
out = df.filter(pl.col("valor") > 100).group_by("uf").agg(pl.col("valor").sum())

# LAZY: constrói um PLANO; só executa no .collect(), já otimizado
out = (
    pl.scan_parquet("vendas.parquet")          # scan_* = lazy (não lê ainda)
      .filter(pl.col("valor") > 100)            # vira predicate pushdown
      .group_by("uf")
      .agg(pl.col("valor").sum().alias("total"))
      .collect()                                 # executa o plano otimizado
)
```

No modo lazy, o Polars **empurra o filtro para a leitura** e lê só as colunas usadas
— ganho enorme em arquivos grandes. Use `scan_*` + `collect()` para pipelines; para
exploração interativa, `read_*` (eager) é conveniente.

Ver o plano:

```python
query.explain()                 # mostra o plano otimizado
query.collect(streaming=True)   # modo streaming para dados > RAM
```

## Expressions — a API que paraleliza

A força do Polars são as **expressions** (`pl.col(...)`), composições declarativas que
o motor paraleliza e otimiza:

```python
df.select(
    pl.col("valor").sum().alias("total"),
    (pl.col("preco") * pl.col("qtd")).alias("receita"),
    pl.col("email").str.strip_chars().str.to_lowercase(),
    pl.col("data").dt.year().alias("ano"),
)

df.with_columns(
    (pl.col("valor") / pl.col("valor").sum().over("uf")).alias("share_uf")  # window
)
```

`over(...)` são [window functions](../../05-sql/05-window-functions/README.md) sem
colapsar linhas.

## Operações essenciais

```python
df.filter((pl.col("uf") == "SP") & (pl.col("valor") > 0))
df.group_by("uf").agg(
    pl.col("valor").sum().alias("total"),
    pl.col("id").n_unique().alias("pedidos"),
)
df.join(dim, on="cliente_id", how="left")        # inner|left|outer|semi|anti|cross
df.sort("valor", descending=True)
df.unique(subset=["id"], keep="last")            # dedupe
df.drop_nulls(subset=["id"])
```

## I/O

```python
pl.scan_parquet("dados/*.parquet")        # lê múltiplos arquivos (glob), lazy
pl.read_csv("x.csv"); pl.scan_csv("x.csv")
pl.read_database(query="select ...", connection=conn)
df.write_parquet("out.parquet")
df.sink_parquet("out.parquet")            # grava lazy em streaming (sem materializar)
```

## polars vs pandas (resumo)

| Aspecto | pandas | polars |
| --- | --- | --- |
| Motor | C/Python (single-core) | Rust (multi-core) |
| Memória | mais pesado | mais enxuto (Arrow) |
| Lazy/otimizador | não | sim (query plan) |
| > RAM | não (chunks manuais) | sim (streaming) |
| Maturidade/ecossistema | enorme | crescendo rápido |
| API | índice, `apply` | expressions, sem índice |

Não é "um substitui o outro" universalmente: pandas tem ecossistema maior; polars
vence em performance/escala. Ambos trocam dados via Arrow quase sem custo.

## Interoperabilidade

```python
df_pl = pl.from_pandas(df_pd)
df_pd = df_pl.to_pandas()
arrow_table = df_pl.to_arrow()            # zero-copy via Arrow
```

## Erros comuns

- Usar `read_*` (eager) quando `scan_*` + `collect()` (lazy) seria muito mais
  eficiente.
- Trazer hábitos de índice do pandas (polars não tem índice).
- Não aproveitar `over()`/expressions e cair em loops.
- Esquecer `streaming=True` para dados maiores que a RAM.

## Boas práticas

- Prefira **lazy** (`scan_* → ... → collect`) em pipelines; deixe o otimizador
  trabalhar.
- Componha com **expressions**; evite converter para pandas no meio sem motivo.
- Use Parquet + glob para ler partições.
- Meça: muitas vezes polars resolve o que exigiria Spark.

## Relação com outros conceitos

- Construído sobre [PyArrow/Arrow](../13-pyarrow/README.md).
- Alternativa a [pandas](../11-pandas/README.md) e, em menor escala, a
  [Spark](../../16-distributed-processing/README.md).
- Lazy/pushdown conecta a [Parquet](../../08-data-formats/04-parquet/README.md).

## Exercícios

1. Reescreva um pipeline pandas em polars **lazy** e compare tempo/memória.
2. Use `scan_parquet` com `filter` e inspecione o plano com `explain()` (veja o
   pushdown).
3. Calcule um *share* por grupo com `over()` sem colapsar as linhas.
4. Processe um arquivo maior que a RAM com `collect(streaming=True)`/`sink_parquet`.

## Referências

- Documentação do Polars (docs.pola.rs) — User Guide e API.
- Apache Arrow (arrow.apache.org).
