# pandas

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

## O que é

**pandas** é a biblioteca de manipulação de dados tabulares em memória mais usada em
Python. Seus objetos centrais são o **Series** (uma coluna) e o **DataFrame** (uma
tabela). É a ferramenta certa para dados que **cabem na memória** (até alguns GB,
dependendo da máquina).

## Quando usar / quando NÃO usar

- **Use** para exploração, dados pequenos/médios, protótipos, transformações em
  memória, testes.
- **Evite** para dados que não cabem na RAM (vai estourar) — aí use
  [polars lazy](../12-polars/README.md), chunks, ou
  [Spark](../../16-distributed-processing/README.md). Também evite reinventar em
  pandas o que o [SQL](../../05-sql/README.md) faz melhor no banco.

## Criar e ler/escrever

```python
import pandas as pd

df = pd.read_csv("vendas.csv", dtype={"id": "int64"}, parse_dates=["data"])
df = pd.read_parquet("vendas.parquet")           # preferível (colunar, tipado)
df = pd.read_json("eventos.jsonl", lines=True)
df = pd.read_sql("select * from pedidos", conn)

df.to_parquet("out.parquet", index=False)         # prefira Parquet a CSV
```

> Prefira **Parquet** a CSV para I/O: preserva tipos, comprime e lê só as colunas
> necessárias (ver [formatos](../../08-data-formats/04-parquet/README.md)).

## Inspeção

```python
df.head(); df.tail(); df.sample(5)
df.shape; df.columns; df.dtypes
df.info(); df.describe()
df.isnull().sum()                 # nulos por coluna
df["categoria"].value_counts()    # frequência
df.memory_usage(deep=True)        # memória por coluna
```

## Seleção e filtragem

```python
df["valor"]                       # uma coluna (Series)
df[["id", "valor"]]               # várias colunas
df.loc[df["valor"] > 100, ["id", "valor"]]      # por rótulo + condição
df.iloc[0:5]                      # por posição
df.query("valor > 100 and uf == 'SP'")           # filtro legível
```

Use `.loc`/`.iloc` para evitar ambiguidade. Cuidado com o `SettingWithCopyWarning`
(ver erros comuns).

## Transformações essenciais

```python
df = df.assign(total=df["preco"] * df["qtd"])     # nova coluna (encadeável)
df = df.rename(columns={"valor": "amount"})
df = df.dropna(subset=["id"])                      # remove nulos
df = df.drop_duplicates(subset=["id"], keep="last")
df = df.fillna({"uf": "N/A"})
df["data"] = pd.to_datetime(df["data"], utc=True)
df["cat"] = df["categoria"].astype("category")     # economiza memória
```

## Agregação (group by)

```python
(df.groupby("uf", as_index=False)
   .agg(total=("amount", "sum"),
        pedidos=("id", "nunique"),
        ticket=("amount", "mean")))
```

Equivale ao `GROUP BY` do [SQL](../../05-sql/02-aggregation-grouping/README.md) —
`agg` com dict/tuplas nomeia as saídas.

## Joins / merge

```python
pd.merge(pedidos, clientes, on="cliente_id", how="left")
# how: inner | left | right | outer
df.merge(dim, left_on="prod_id", right_on="id", how="inner")
```

Equivale aos [JOINs de SQL](../../05-sql/03-joins/README.md). Cuidado com joins que
**multiplicam linhas** (chave não única) — verifique a cardinalidade.

## Datas, janelas e séries temporais

```python
df = df.set_index("data").sort_index()
df["media_7d"] = df["amount"].rolling("7D").mean()      # janela móvel
mensal = df["amount"].resample("MS").sum()               # reamostra por mês
```

## Encadeamento (method chaining) — legibilidade

```python
resultado = (
    df
    .query("amount > 0")
    .assign(email=lambda d: d["email"].str.strip().str.lower())
    .groupby("uf", as_index=False)
    .agg(total=("amount", "sum"))
    .sort_values("total", ascending=False)
)
```

Encadear deixa o fluxo claro e evita variáveis intermediárias — mantém a lógica
**pura** e testável (ver [organização](../../03-git-software-engineering/07-project-organization/README.md)).

## Memória e performance

- **Vetorize**; evite `iterrows()`/`apply(axis=1)` (ver
  [performance](../10-performance-profiling/README.md)).
- Leia só colunas necessárias (`usecols` no CSV; colunas no Parquet).
- Use `category` para baixa cardinalidade; downcast de inteiros.
- Para arquivos grandes, `read_csv(chunksize=...)` processa em pedaços.
- **PyArrow backend** (pandas 2.x): `dtype_backend="pyarrow"` melhora memória e
  strings — ver [PyArrow](../13-pyarrow/README.md).

## Erros comuns

- Carregar um CSV maior que a RAM → OOM (use polars/chunks/Spark).
- `SettingWithCopyWarning` por encadear indexações; prefira `.loc`/`.assign`.
- Joins que multiplicam linhas por chave não única.
- Comparar/mexer em datas naive com fusos misturados.
- `apply(axis=1)` em dados grandes (lento).

## Boas práticas

- Parquet para I/O; tipos corretos; `category` onde couber.
- Method chaining + funções puras de transformação.
- Valide shape/nulos/duplicatas (conecte a [data quality](../../12-data-quality/README.md)).
- Se doer de memória/velocidade, migre para [polars](../12-polars/README.md).

## Relação com outros conceitos

- Alternativas: [polars](../12-polars/README.md), [PyArrow](../13-pyarrow/README.md),
  [Spark](../../16-distributed-processing/README.md).
- Operações espelham [SQL](../../05-sql/README.md).

## Exercícios

1. Leia um Parquet, limpe (nulos/duplicatas), crie uma coluna derivada e agregue por
   grupo, tudo em um *method chain*.
2. Faça um `merge` left entre fatos e uma dimensão e verifique que não multiplicou
   linhas.
3. Reduza a memória de um DataFrame com `category`/downcast e meça o ganho.
4. Calcule uma média móvel de 7 dias de uma série temporal.

## Referências

- Documentação do pandas (pandas.pydata.org) — User Guide.
- McKinney, W. *Python for Data Analysis*, 3ª ed. O'Reilly.
