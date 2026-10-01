# Performance e profiling

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

## A regra de ouro

**Meça antes de otimizar.** A intuição sobre onde está o gargalo quase sempre erra.
*Profiling* mostra onde o tempo e a memória realmente vão; só então você otimiza o
que importa (princípio: evite otimização prematura).

Em DE, os dois recursos críticos são **tempo** e **memória** — e memória costuma ser
o limite que derruba jobs (OOM).

## Medindo tempo

### Rápido e sujo

```python
import time
t0 = time.perf_counter()
rodar()
print(f"{time.perf_counter() - t0:.3f}s")
```

### Benchmark de trechos pequenos

```bash
python -m timeit -s "import x" "x.func()"
```

### Profiling de função (cProfile)

```bash
python -m cProfile -s cumtime meu_script.py
# ou salvar e visualizar:
python -m cProfile -o out.prof meu_script.py
# visualize com snakeviz: snakeviz out.prof
```

`cProfile` mostra quantas vezes cada função é chamada e quanto tempo acumulado —
aponta o gargalo real. Para profiling linha a linha, use `line_profiler`
(`@profile` + `kernprof`).

## Medindo memória

Memória é o calcanhar de Aquiles de pandas & cia.

```bash
python -m memory_profiler meu_script.py     # uso por linha (@profile)
mprof run script.py && mprof plot           # perfil ao longo do tempo
```

```python
import tracemalloc
tracemalloc.start()
rodar()
print(tracemalloc.get_traced_memory())      # (atual, pico) em bytes
```

Em pandas: `df.memory_usage(deep=True)` mostra memória por coluna (atenção a
`object`/strings).

## As grandes alavancas de performance em DE

Ordenadas por impacto típico:

### 1. Processar menos dados

- **Filtre cedo** (*predicate pushdown*): leia só as linhas/colunas necessárias.
- **Leia só as colunas usadas** — trivial em [Parquet](../13-pyarrow/README.md)
  (colunar), impossível de forma eficiente em CSV.
- **Particione** e leia só as partições relevantes (ver [data lake](../../14-data-lake/05-partitioning/README.md)).

### 2. Escolher a ferramenta certa

```text
cabe na memória e é pequeno/médio?   → pandas (ou polars)
grande, mas cabe num servidor?       → polars (multi-core, lazy, out-of-core)
não cabe / distribuído?              → Spark
só transformação SQL no warehouse?   → faça no SQL/dbt (não traga para Python)
```

Muitas vezes a melhor otimização é **não trazer os dados para Python** — empurre a
transformação para o banco/warehouse (ver [SQL](../../05-sql/README.md)).

### 3. Vetorizar (não iterar linha a linha)

Em pandas/polars/numpy, operações vetorizadas rodam em C e são ordens de grandeza
mais rápidas que loops Python.

```python
# LENTO: itera linha a linha
df["total"] = [p * q for p, q in zip(df["preco"], df["qtd"])]
df.apply(..., axis=1)                 # também lento

# RÁPIDO: vetorizado
df["total"] = df["preco"] * df["qtd"]
```

Evite `iterrows()`/`apply(axis=1)` em DataFrames grandes.

### 4. Tipos eficientes

- Use `category` para colunas de baixa cardinalidade em pandas; tipos nativos
  corretos (int32 em vez de int64 quando couber).
- Formatos colunares comprimidos ([Parquet](../13-pyarrow/README.md)) economizam
  I/O e memória.

### 5. Streaming / lazy / chunks

Quando os dados não cabem: *generators* ([tópico 06](../06-iterators-generators-context-managers/README.md)),
`pandas.read_csv(..., chunksize=...)`, ou [polars lazy](../12-polars/README.md)
(que otimiza e processa *out-of-core*).

### 6. Paralelismo (quando aplicável)

Ver [concorrência](../07-concurrency/README.md): threads/async para I/O, processos
para CPU, ou delegar a engines que já paralelizam.

## Complexidade algorítmica

Antes de micro-otimizar, cheque a complexidade: um `O(n²)` (ex.: buscar numa lista
dentro de um loop) explode com o volume. Use `set`/`dict` para lookups `O(1)`.

```python
# O(n*m): lento
for r in registros:
    if r["id"] in lista_de_ids:       # busca O(m) em lista
        ...
# O(n): rápido
ids = set(lista_de_ids)               # lookup O(1)
for r in registros:
    if r["id"] in ids:
        ...
```

## Processo de otimização (método)

```text
1. Defina a meta (tempo/memória aceitável) e meça o baseline.
2. Faça profiling → ache o gargalo real.
3. Otimize UMA coisa.
4. Meça de novo → confirme o ganho (e que não quebrou nada: rode os testes).
5. Repita se ainda não atingiu a meta; pare quando "bom o suficiente".
```

## Erros comuns

- Otimizar por achismo, sem profiling.
- `iterrows()`/`apply(axis=1)` em dados grandes.
- Carregar tudo na memória quando dava para filtrar/streamar.
- Trazer para Python o que o SQL/warehouse faria melhor.
- Buscas `O(n)` em lista dentro de loops.

## Boas práticas

- Meça → otimize → remeça; pare quando suficiente.
- Filtre/projete cedo; vetorize; use formatos colunares.
- Escolha a ferramenta pelo tamanho do dado.
- Guarde o baseline para comparar.

## Relação com outros conceitos

- Ferramentas: [pandas](../11-pandas/README.md), [polars](../12-polars/README.md),
  [PyArrow](../13-pyarrow/README.md), [Spark](../../16-distributed-processing/README.md).
- Formatos: [Parquet/colunar](../../08-data-formats/08-row-vs-columnar/README.md).

## Exercícios

1. Faça profiling de um script com `cProfile` e identifique a função mais custosa.
2. Reescreva um `apply(axis=1)` como operação vetorizada e meça o ganho.
3. Reduza o uso de memória de um DataFrame com tipos `category`/int32 e meça com
   `memory_usage(deep=True)`.
4. Troque uma busca `O(n²)` por `set` e compare os tempos em n grande.

## Referências

- Documentação de `cProfile`, `tracemalloc`, `timeit`.
- `line_profiler`, `memory_profiler`, `scalene`, `py-spy`.
- Gorelick, M.; Ozsvald, I. *High Performance Python*, 2ª ed.
