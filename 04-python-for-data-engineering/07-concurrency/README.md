# Concorrência (threading, multiprocessing, async)

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

## O que é e quando importa

Concorrência é executar várias tarefas "ao mesmo tempo". Em DE, aparece para
acelerar: baixar muitos arquivos/APIs em paralelo, processar partições em vários
núcleos, ingerir de várias fontes. Mas **a escolha errada não ajuda** — e em Python
depende de entender o GIL.

## O GIL (Global Interpreter Lock)

O CPython tem um *lock* global que permite apenas **uma thread executando bytecode
Python por vez**. Consequência prática:

- **Threads não aceleram código Python puro CPU-bound** (elas se revezam no GIL).
- **Threads aceleram I/O-bound**, porque o GIL é liberado durante a espera de I/O
  (rede, disco).
- Para paralelismo real de CPU, use **processos** (cada um com seu interpretador).

> Nota: Python 3.13 introduziu um modo experimental *free-threaded* (sem GIL), mas
> em 2026 ainda não é o padrão. Raciocine com o GIL presente.

## Classificando a tarefa: I/O-bound vs CPU-bound

| Tipo | Gargalo | Ferramenta ideal |
| --- | --- | --- |
| **I/O-bound** | esperar rede/disco (APIs, DB, arquivos) | **threads** ou **async** |
| **CPU-bound** | computação pesada (parse, cálculo) | **multiprocessing** |

A maior parte do trabalho de ingestão é I/O-bound; a de transformação pesada em
Python puro é CPU-bound (mas aí geralmente delega-se a pandas/polars/Spark, que
liberam o GIL em C).

## threading / ThreadPoolExecutor (I/O-bound)

```python
from concurrent.futures import ThreadPoolExecutor
import requests

def baixar(url: str) -> bytes:
    return requests.get(url, timeout=30).content

urls = [...]  # muitas URLs
with ThreadPoolExecutor(max_workers=16) as ex:
    resultados = list(ex.map(baixar, urls))   # baixa em paralelo
```

Ótimo para dezenas/centenas de chamadas de rede simultâneas. `max_workers` controla
o paralelismo (cuidado com limites/*rate limits* da API).

## multiprocessing / ProcessPoolExecutor (CPU-bound)

```python
from concurrent.futures import ProcessPoolExecutor

def processar_arquivo(path: str) -> int:
    # trabalho pesado de CPU em Python puro
    ...

with ProcessPoolExecutor(max_workers=8) as ex:
    totais = list(ex.map(processar_arquivo, arquivos))
```

Cada processo tem seu próprio Python → paralelismo real de CPU. Custo: *overhead*
de criar processos e **serializar** dados entre eles (via `pickle`) — evite passar
objetos gigantes.

## async / asyncio (I/O-bound em larga escala)

`async`/`await` permite milhares de operações de I/O concorrentes em uma única
thread, com baixo *overhead* — ideal para muitas chamadas de rede.

```python
import asyncio, httpx

async def baixar(client, url):
    r = await client.get(url, timeout=30)
    return r.content

async def main(urls):
    async with httpx.AsyncClient() as client:
        tarefas = [baixar(client, u) for u in urls]
        return await asyncio.gather(*tarefas)

resultados = asyncio.run(main(urls))
```

Requer bibliotecas assíncronas (`httpx`, `aiokafka`, `asyncpg`). Mais eficiente que
threads para altíssima concorrência de I/O, porém "contagia" o código (tudo vira
`async`). Ver [HTTP clients](../08-http-clients/README.md).

## Como escolher (árvore de decisão)

```text
A tarefa espera I/O (rede/disco)?
├── Sim → poucas/moderadas conexões?  → ThreadPoolExecutor (simples)
│         milhares de conexões?       → asyncio (eficiente)
└── Não (é CPU pesada em Python)?     → ProcessPoolExecutor
          └── ou delegue a pandas/polars/Spark (processam em C/Rust, fora do GIL)
```

## Cuidados com paralelismo em pipelines

- **Idempotência/ordem:** resultados chegam fora de ordem; não dependa da ordem de
  conclusão.
- **Rate limits:** limite `max_workers` e aplique *backoff* para não ser bloqueado.
- **Erros parciais:** trate falhas de itens individuais sem derrubar o lote inteiro.
- **Estado compartilhado:** evite; se preciso, use filas (`queue.Queue`) ou
  estruturas seguras. Em multiprocessing, use `Queue`/`Manager`.
- **Determinismo:** paralelismo pode tornar bugs intermitentes (*race conditions*).

## Alternativas de mais alto nível

Para paralelismo de **dados**, muitas vezes a resposta certa não é mexer com
threads/processos manualmente, e sim usar uma engine que já paraleliza:
[polars](../12-polars/README.md) (multi-core nativo),
[Dask](https://www.dask.org/), ou [Spark](../../16-distributed-processing/README.md)
(distribuído). Prefira-as para transformar grandes volumes.

## Erros comuns

- Usar threads para acelerar código CPU-bound (o GIL impede ganho).
- Ignorar *rate limits* ao paralelizar chamadas de API.
- Passar DataFrames gigantes entre processos (custo de serialização).
- Depender da ordem de conclusão das tarefas.

## Boas práticas

- Classifique a tarefa (I/O vs CPU) **antes** de escolher a ferramenta.
- Comece simples (`ThreadPoolExecutor`); vá para async/processos se medir
  necessidade.
- Delegue transformação pesada a engines colunares.
- Limite concorrência e trate erros por item.

## Relação com outros conceitos

- Aplicado em [HTTP clients](../08-http-clients/README.md) e
  [ingestão](../../09-etl-elt/02-ingestion-extraction/README.md).
- Escala para [processamento distribuído](../../16-distributed-processing/README.md).

## Exercícios

1. Baixe 100 URLs com `ThreadPoolExecutor` e meça o ganho vs sequencial.
2. Reescreva o mesmo com `asyncio` + `httpx` e compare.
3. Faça um cálculo CPU-bound em 8 arquivos com `ProcessPoolExecutor`; explique por
   que threads não ajudariam aqui.
4. Explique, com o GIL, por que threads aceleram I/O mas não CPU em Python.

## Referências

- Documentação de `concurrent.futures`, `asyncio`, `multiprocessing`.
- Ramalho, L. *Fluent Python*, 2ª ed. — caps. de concorrência.
- Beazley, D. — palestras sobre o GIL e concorrência.
