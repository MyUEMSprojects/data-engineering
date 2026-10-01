# Iterators, generators e context managers

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

Estes três recursos são **centrais** em Data Engineering porque resolvem o problema
nº 1 de processar dados: **não carregar tudo na memória** e **gerenciar recursos
(arquivos/conexões) com segurança**.

## Iterators e o protocolo de iteração

Um **iterable** é algo que se pode percorrer (`for x in ...`); um **iterator**
produz os itens um a um e lembra onde parou. `for` usa `__iter__`/`__next__` por
baixo.

```python
it = iter([1, 2, 3])
next(it)      # 1
next(it)      # 2
```

A ideia-chave: você pode iterar sobre fontes **enormes ou infinitas** sem
materializá-las — se produzir os itens sob demanda.

## Generators — o coração do processamento de dados grandes

Um **generator** é uma função que usa `yield`: ela produz valores preguiçosamente
(*lazy*), um por vez, mantendo o estado entre chamadas. Não constrói a lista toda na
memória.

```python
def ler_linhas(path):
    with open(path, encoding="utf-8") as f:
        for linha in f:
            yield linha.rstrip("\n")     # entrega uma linha por vez
```

Comparação crucial:

```python
# RUIM: carrega o arquivo INTEIRO na memória (pode estourar a RAM)
linhas = open("huge.csv").readlines()

# BOM: processa linha a linha, memória ~constante
for linha in ler_linhas("huge.csv"):
    processar(linha)
```

### Pipelines de generators (composição lazy)

Encadeie generators como filtros Unix — cada estágio consome o anterior sob
demanda, sem materializar nada no meio:

```python
def parse(linhas):
    for l in linhas:
        yield json.loads(l)

def somente_compras(eventos):
    for e in eventos:
        if e["type"] == "purchase":
            yield e

def em_lotes(it, n):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) == n:
            yield buf; buf = []
    if buf:
        yield buf

linhas  = ler_linhas("eventos.jsonl")
compras = somente_compras(parse(linhas))
for lote in em_lotes(compras, 1000):      # grava de 1000 em 1000
    carregar(lote)
```

Esse padrão processa um arquivo de 100 GB com memória de alguns MB. É o idioma de
ETL *out-of-memory* em Python puro.

### generator expressions

```python
total = sum(r["valor"] for r in parse(ler_linhas("vendas.jsonl")))
```

Parênteses em vez de colchetes = *lazy*. Prefira quando só for consumir uma vez.

### Cuidado: generators se esgotam

Um generator só pode ser percorrido **uma vez**. Se precisar reutilizar, recrie-o
ou materialize (`list(...)`) — ciente do custo de memória.

## yield from e geradores delegados

```python
def todos_arquivos(dir):
    for p in Path(dir).glob("*.jsonl"):
        yield from ler_linhas(p)     # delega a iteração a outro generator
```

## Context managers — gerenciar recursos com segurança

O `with` garante que recursos (arquivos, conexões, locks) sejam **liberados** mesmo
se ocorrer um erro — evita vazamento de arquivos/conexões, um problema real em
pipelines longos.

```python
with open("dados.csv", encoding="utf-8") as f:   # fecha sozinho ao sair
    processar(f)
# aqui o arquivo JÁ está fechado, mesmo que processar() tenha falhado
```

### Criando o seu (contextlib)

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(nome):
    t0 = time.perf_counter()
    try:
        yield
    finally:
        print(f"{nome}: {time.perf_counter() - t0:.2f}s")

with timer("ingestao"):
    rodar_etl()
```

Padrão comum em DE: context manager para abrir/fechar conexão de banco, transação,
ou arquivo temporário (garante *cleanup*).

```python
@contextmanager
def conexao(dsn):
    conn = connect(dsn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()      # desfaz em caso de erro
        raise
    finally:
        conn.close()         # sempre fecha
```

### Múltiplos recursos

```python
with open("in.csv") as fin, open("out.csv", "w") as fout:
    ...
```

## Erros comuns

- `readlines()`/`read()` em arquivos grandes → estouro de memória.
- Tentar reutilizar um generator já consumido.
- Abrir arquivos/conexões sem `with` → vazamento de recursos.
- Materializar (`list()`) um generator grande sem necessidade.

## Boas práticas

- *Stream* por padrão: generators para qualquer fonte potencialmente grande.
- Processe em **lotes** (balanço entre memória e número de operações de I/O).
- `with` para todo recurso que precisa ser fechado.
- Mantenha cada estágio do pipeline pequeno e componível.

## Relação com outros conceitos

- Base de ETL eficiente ([transformação](../../09-etl-elt/03-transformation/README.md)).
- Alternativa quando os dados **não** cabem em [pandas](../11-pandas/README.md) na
  memória (ou use [polars lazy](../12-polars/README.md)).
- Context managers garantem [idempotência/segurança](../../09-etl-elt/07-idempotency-retries/README.md).

## Exercícios

1. Escreva um pipeline de generators que lê um JSONL enorme, filtra por um campo e
   grava em lotes de 1000 — medindo que a memória fica constante.
2. Transforme uma função que retorna uma lista gigante em um generator e compare o
   uso de memória.
3. Crie um context manager `transacao(conn)` que faz commit no sucesso e rollback
   no erro.
4. Explique por que o segundo `for` sobre o mesmo generator não produz nada.

## Referências

- Ramalho, L. *Fluent Python*, 2ª ed. — caps. 17 (iterators/generators) e 18
  (context managers).
- Documentação de `contextlib` e `itertools`.
- Slatkin, B. *Effective Python* — itens sobre generators.
