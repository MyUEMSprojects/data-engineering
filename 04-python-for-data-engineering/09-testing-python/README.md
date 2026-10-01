# Testes em Python (aplicados a dados)

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

Este tópico aprofunda o `pytest` com foco nas técnicas que você mais usa testando
código de dados. A visão conceitual (pirâmide, testes de dados vs código) está em
[03 — Testes](../../03-git-software-engineering/05-testing/README.md); aqui é a
prática em Python.

## Estrutura e descoberta

```text
tests/
├── conftest.py            # fixtures compartilhadas (auto-descobertas)
├── test_transform.py
└── fixtures/              # amostras pequenas de dados
```

`pytest` descobre `test_*.py` e funções `test_*`. Rode com `pytest -q`.

## Asserts e exceções

```python
def test_soma():
    assert soma([1, 2, 3]) == 6

import pytest
def test_erro():
    with pytest.raises(ValueError, match="id"):
        validar({"id": None})
```

## Parametrização (cobrir casos de borda)

Dados têm muitos casos de borda (nulos, vazios, duplicatas, acentos, fuso).
Parametrize:

```python
import pytest

@pytest.mark.parametrize("entrada, esperado", [
    ("  A@B.com ", "a@b.com"),
    ("x@y.z", "x@y.z"),
    ("", ""),
])
def test_normalize(entrada, esperado):
    assert normalize_email(entrada) == esperado
```

## Fixtures

```python
import pytest, pandas as pd

@pytest.fixture
def pedidos():
    return pd.DataFrame({"id": [1, 1, 2], "valor": [10, 10, 5]})

def test_dedupe(pedidos):
    out = dedupe(pedidos, key="id")
    assert out["id"].tolist() == [1, 2]
```

- `scope="session"/"module"` reutiliza a fixture (ex.: subir um DB uma vez).
- `tmp_path` (fixture embutida) dá um diretório temporário para testar I/O.

```python
def test_escreve_csv(tmp_path):
    out = tmp_path / "x.csv"
    escrever(out, [{"id": 1}])
    assert out.exists()
```

## Comparando DataFrames

Não compare DataFrames com `==`. Use os utilitários:

```python
import pandas as pd
from pandas.testing import assert_frame_equal

assert_frame_equal(resultado, esperado, check_dtype=True)

# polars
from polars.testing import assert_frame_equal as pl_assert
```

## Mocking (isolar dependências externas)

Teste sua lógica sem chamar APIs/bancos reais.

```python
from unittest.mock import patch

@patch("meu_pipeline.extract.requests.get")
def test_fetch(mock_get):
    mock_get.return_value.json.return_value = {"data": [{"id": 1}]}
    mock_get.return_value.raise_for_status.return_value = None
    assert fetch_orders() == [{"id": 1}]
```

Para HTTP, bibliotecas como `responses`/`respx` mockam chamadas de forma mais
declarativa. **Mocke nas fronteiras** (rede, relógio, filesystem), não a sua
própria lógica.

### Controlar o tempo

```python
from freezegun import freeze_time

@freeze_time("2024-01-01")
def test_particao_de_hoje():
    assert particao_atual() == "2024-01-01"
```

Testes que dependem de "hoje" ficam instáveis — congele o tempo.

## Testes de integração com banco efêmero

```python
import pytest, psycopg

@pytest.fixture(scope="session")
def db_url():
    # com testcontainers ou docker-compose, suba um Postgres de teste
    return "postgresql://test@localhost:5433/test"

def test_load(db_url):
    carregar(db_url, [{"id": 1, "valor": 9.9}])
    with psycopg.connect(db_url) as c:
        assert c.execute("select count(*) from pedidos").fetchone()[0] == 1
```

`testcontainers` sobe/derruba containers automaticamente nos testes — ótimo para
integração reprodutível.

## Teste de idempotência (padrão de DE)

```python
def test_idempotente(db_url):
    carregar(db_url, dados)
    carregar(db_url, dados)      # roda de novo
    assert contar(db_url) == len(set(ids))   # não duplicou
```

## Marcadores e organização

```python
@pytest.mark.slow
def test_pipeline_e2e(): ...
```

```bash
pytest -m "not slow"     # pula os lentos no dia a dia
```

## Cobertura (com critério)

```bash
pytest --cov=meu_pipeline --cov-report=term-missing
```

Cobertura ajuda a ver o não-testado, mas **100% não garante correção**. Foque no que
tem risco e importa.

## Erros comuns

- Testes que batem em rede/DB de produção → lentos e *flaky*.
- Comparar DataFrames com `==`.
- Depender de "hoje"/ordem/aleatoriedade sem controlar.
- Mockar a própria lógica (teste vira tautologia).
- Fixtures gigantes carregando dados reais.

## Boas práticas

- Isole I/O, teste lógica pura; mocke só as fronteiras.
- Parametrize casos de borda; use `tmp_path` para I/O.
- Congele tempo e semeie aleatoriedade (`random.seed`).
- Integração com containers efêmeros; rode tudo no [CI](../../23-cicd-dataops/README.md).

## Relação com outros conceitos

- Conceitos e testes de dados: [03 — Testes](../../03-git-software-engineering/05-testing/README.md),
  [Data Quality](../../12-data-quality/README.md).
- Mocka clientes de [HTTP](../08-http-clients/README.md).

## Exercícios

1. Parametrize o teste de uma função de limpeza cobrindo nulos, vazios e acentos.
2. Mocke uma chamada `requests.get` e teste a função de ingestão sem rede.
3. Use `tmp_path` para testar uma função que escreve Parquet.
4. Escreva um teste de idempotência para uma função de carga.

## Referências

- Documentação do `pytest`, `unittest.mock`, `pandas.testing`.
- `testcontainers-python`, `responses`/`respx`, `freezegun`.
