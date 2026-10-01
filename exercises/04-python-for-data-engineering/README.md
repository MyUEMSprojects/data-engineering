# Exercícios — Módulo 04: Python para Engenharia de Dados

Teoria em [04-python-for-data-engineering](../../04-python-for-data-engineering/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Implementação — Ler CSV grande sem estourar memória

Escreva um gerador `read_rows(path)` que lê um CSV de 5 GB **linha a linha** e outro `batched(it, n)` que agrupa em lotes de `n`. Por que isso importa?

<details><summary>Gabarito</summary>

```python
import csv
from itertools import islice

def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)

def batched(it, n):
    it = iter(it)
    while batch := list(islice(it, n)):
        yield batch
```

Memória **constante** (um lote por vez). (Em Python ≥ 3.12 existe `itertools.batched`.) Ver [iteradores e geradores](../../04-python-for-data-engineering/06-iterators-generators-context-managers/README.md).
</details>

## 2. 🟢 Debugging — O default mutável

```python
def add_event(event, events=[]):
    events.append(event)
    return events
print(add_event(1)); print(add_event(2))
```

O que imprime e por quê? Corrija.

<details><summary>Gabarito</summary>

Imprime `[1]` e depois `[1, 2]`: o default é avaliado **uma vez**, na definição da função, e compartilhado. Correção: `def add_event(event, events=None): events = [] if events is None else events`.
</details>

## 3. 🔵 Implementação — Retry com backoff

Implemente um decorador `retry(times, base_delay)` com **backoff exponencial e jitter** que só repete exceções **transitórias** (ex.: `TimeoutError`, `ConnectionError`) e repropaga as demais.

<details><summary>Gabarito</summary>

```python
import functools, random, time

def retry(times=3, base_delay=0.5, transient=(TimeoutError, ConnectionError)):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            for attempt in range(1, times + 1):
                try:
                    return fn(*a, **k)
                except transient:
                    if attempt == times:
                        raise
                    time.sleep(base_delay * 2 ** (attempt - 1) * random.uniform(0.5, 1.5))
        return wrapper
    return deco
```

O **jitter** evita que vários clientes tentem de novo ao mesmo tempo (*thundering herd*). Falha **permanente** (ex.: `ValueError`) não deve repetir — ver [falhas](../../09-etl-elt/11-handling-failures/README.md).
</details>

## 4. 🔵 Implementação — Tipagem e validação

Modele um pedido com `dataclass` (ou Pydantic) validando: `amount >= 0`, `status` em um conjunto, `order_date` ISO. Retorne **todos** os erros de uma vez, não só o primeiro.

<details><summary>Gabarito</summary>

```python
from dataclasses import dataclass
from datetime import date

STATUSES = {"created", "paid", "shipped", "canceled"}

@dataclass(frozen=True)
class Order:
    order_id: str
    amount: float
    status: str
    order_date: date

def parse_order(d: dict) -> tuple[Order | None, list[str]]:
    errors = []
    if not d.get("order_id"): errors.append("missing:order_id")
    try: amount = float(d.get("amount"))
    except (TypeError, ValueError): amount = None; errors.append("bad:amount")
    else:
        if amount < 0: errors.append("negative:amount")
    if d.get("status") not in STATUSES: errors.append("unknown:status")
    try: od = date.fromisoformat(d.get("order_date", ""))
    except ValueError: od = None; errors.append("bad:order_date")
    return (None, errors) if errors else (Order(d["order_id"], amount, d["status"], od), [])
```

Acumular erros dá **diagnóstico completo** por linha (como a quarentena do [Projeto 01](../../projects/01-basic-etl/README.md)). Para dinheiro, prefira `Decimal`.
</details>

## 5. 🟣 Implementação — Concorrência: I/O × CPU

Você precisa (a) baixar 2.000 URLs de uma API e (b) calcular um hash pesado de 2.000 arquivos locais. Escolha `threading`, `asyncio` ou `multiprocessing` para cada caso e explique o papel do GIL.

<details><summary>Gabarito</summary>

(a) **I/O-bound** → `asyncio` (ou `ThreadPoolExecutor`): o GIL é liberado durante a espera de rede. Limite a concorrência (semáforo) e respeite *rate limits*.
(b) **CPU-bound** → `multiprocessing`/`ProcessPoolExecutor`: o **GIL** impede paralelismo real de threads em código Python puro (hashlib libera o GIL em blocos grandes, mas não conte com isso). Medir antes de decidir.
Ver [concorrência](../../04-python-for-data-engineering/07-concurrency/README.md).
</details>

## 6. 🟣 Arquitetura — pandas, Polars ou PyArrow?

Um job lê 40 GB de Parquet, filtra, agrega e escreve. A máquina tem 16 GB de RAM. Qual ferramenta e **por quê**? O que muda se os dados passarem de 400 GB?

<details><summary>Gabarito</summary>

Com 40 GB > RAM: pandas (tudo em memória) **falha**. **Polars** (modo *lazy*/streaming) ou **DuckDB** processam por partes e fazem *predicate/projection pushdown* no Parquet. PyArrow Datasets também filtram sem carregar tudo.
Acima de ~400 GB (ou necessidade de paralelismo em várias máquinas): engine **distribuída** (Spark/Trino). Critério: tamanho × RAM × tempo de execução × custo operacional. Ver [pandas](../../04-python-for-data-engineering/11-pandas/README.md), [Polars](../../04-python-for-data-engineering/12-polars/README.md), [PyArrow](../../04-python-for-data-engineering/13-pyarrow/README.md) e o [Projeto 06](../../projects/06-spark/README.md).
</details>
