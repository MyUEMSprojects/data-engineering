# 04 — Python para Data Engineering

> 🔵 Nível 2 — Core · Pré: [03 — Git & SWE](../03-git-software-engineering/README.md) ·
> Próximo: [05 — SQL](../05-sql/README.md)

Python é a *lingua franca* da Engenharia de Dados: scripts de ingestão, DAGs de
orquestração, transformações, testes, *glue code* e bibliotecas de dados
(pandas/polars/PyArrow). Este módulo **não** é um curso genérico de Python — foca
no que o Data Engineer realmente usa para mover e transformar dados de forma
robusta e eficiente.

## Filosofia deste módulo

Você não precisa ser engenheiro de software de aplicações web para ser DE, mas
precisa escrever código **confiável, testável e eficiente em memória/tempo**. Os
tópicos priorizam exatamente isso: tipos, erros/logging, *generators* (streaming
de dados que não cabem na RAM), concorrência, performance e as bibliotecas de
dados.

## Tópicos

| # | Tópico | Foco em DE |
| --- | --- | --- |
| 01 | [Essenciais da linguagem](01-language-essentials/README.md) | Tipos, funções, módulos, estruturas de dados |
| 02 | [Ambientes e packaging](02-environments-and-packaging/README.md) | venv, uv/pip, pyproject, reprodutibilidade |
| 03 | [Typing](03-typing/README.md) | Type hints, mypy, contratos de função |
| 04 | [Erros e logging](04-errors-and-logging/README.md) | Exceptions, logging estruturado |
| 05 | [Stdlib para DE](05-stdlib-for-de/README.md) | pathlib, argparse, dataclasses, datetime, json |
| 06 | [Iterators, generators e context managers](06-iterators-generators-context-managers/README.md) | Processar dados grandes sem estourar memória |
| 07 | [Concorrência](07-concurrency/README.md) | threading, multiprocessing, async, GIL |
| 08 | [HTTP clients](08-http-clients/README.md) | requests/httpx, paginação, retries |
| 09 | [Testes em Python](09-testing-python/README.md) | pytest aplicado a dados, mocks, fixtures |
| 10 | [Performance e profiling](10-performance-profiling/README.md) | Medir antes de otimizar; memória |
| 11 | [pandas](11-pandas/README.md) | Manipulação tabular em memória |
| 12 | [polars](12-polars/README.md) | DataFrames rápidos, lazy, out-of-core |
| 13 | [PyArrow](13-pyarrow/README.md) | Arrow, Parquet, interoperabilidade colunar |

## Dependências internas

```text
Essenciais ─► Ambientes/packaging ─► Typing ─► Erros & logging ─► Stdlib
     │
     ▼
Iterators/generators ─► Concorrência ─► HTTP clients
     │
     ▼
Performance/profiling ─► pandas ─► polars ─► PyArrow
```

## Checkpoint

- [ ] Montar um ambiente isolado e reprodutível (venv + lockfile + pyproject).
- [ ] Escrever funções tipadas, com tratamento de erro e logging adequados.
- [ ] Processar um arquivo que não cabe na RAM usando *generators*.
- [ ] Explicar o GIL e escolher entre threading, multiprocessing e async.
- [ ] Consumir uma API paginada com retries/backoff robustos.
- [ ] Medir e reduzir o uso de memória de um script com pandas/polars.
- [ ] Ler/escrever Parquet e explicar por que PyArrow é o "motor" por baixo.

## Referências do módulo

- *Fluent Python*, Luciano Ramalho, 2ª ed. O'Reilly, 2022.
- *Effective Python*, Brett Slatkin, 2ª ed.
- Documentação oficial de Python, pandas, Polars e Apache Arrow.
