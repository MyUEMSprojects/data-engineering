# Testes

> 🟢 Foundations · Parte de [03 — Git & SWE](../README.md)

## O que é

Testar é escrever código que verifica, automaticamente, se o seu código faz o que
deveria. Em Data Engineering há **duas dimensões**:

1. **Testes de código** — a lógica dos seus pipelines/funções está correta?
2. **Testes de dados** — os dados que passam pelo pipeline atendem às expectativas
   (schema, unicidade, faixas, *freshness*)?

Este tópico foca nos testes de código (com `pytest`) e conecta aos testes de dados,
detalhados em [Data Quality](../../12-data-quality/README.md).

## Por que existe

- Pipelines mudam e dados mudam; testes são a rede que permite mudar **sem medo**.
- Bugs em dados são caros e silenciosos (um número errado num relatório pode passar
  despercebido por meses).
- Testes documentam o comportamento esperado.

## A pirâmide de testes

```text
        ╱ E2E ╲          poucos, lentos, caros (pipeline ponta a ponta)
      ╱─────────╲
     ╱ integração ╲      médios (código + DB/arquivo reais)
   ╱───────────────╲
  ╱     unitários    ╲   muitos, rápidos, baratos (funções isoladas)
```

- **Unitários** — testam uma função pura isoladamente (ex.: uma transformação de
  dados). Rápidos; devem ser a maioria.
- **Integração** — testam o código contra dependências reais (um PostgreSQL de
  teste, um arquivo Parquet).
- **End-to-end** — rodam o pipeline inteiro num ambiente controlado.

## pytest — o essencial

```python
# transform.py
def normalize_email(email: str) -> str:
    return email.strip().lower()

# test_transform.py
import pytest
from transform import normalize_email

def test_normalize_email_basic():
    assert normalize_email("  Felipe@Exemplo.COM ") == "felipe@exemplo.com"

@pytest.mark.parametrize("raw, expected", [
    ("A@B.com", "a@b.com"),
    ("  x@y.z", "x@y.z"),
])
def test_normalize_email_cases(raw, expected):
    assert normalize_email(raw) == expected

def test_raises_on_none():
    with pytest.raises(AttributeError):
        normalize_email(None)  # type: ignore[arg-type]
```

```bash
pytest               # roda tudo
pytest -q            # saída resumida
pytest -k email      # só testes cujo nome casa "email"
pytest --cov=.       # cobertura (pytest-cov)
```

### Fixtures — preparar o cenário

```python
import pytest
import pandas as pd

@pytest.fixture
def vendas_df():
    return pd.DataFrame({"produto": ["a", "a", "b"], "valor": [10, 10, 5]})

def test_dedupe(vendas_df):
    from transform import dedupe
    out = dedupe(vendas_df)
    assert len(out) == 2
```

Fixtures criam dados/recursos reutilizáveis (um DataFrame, uma conexão a um DB de
teste). `yield` permite *setup* e *teardown*.

## Padrão de teste: AAA

**Arrange** (prepara dados) → **Act** (executa) → **Assert** (verifica). Mantém os
testes legíveis.

## Testando pipelines de dados

Estratégias específicas de DE:

- **Teste a transformação como função pura.** Separe a lógica (transformar um
  DataFrame) do I/O (ler/escrever) — a lógica fica testável sem DB. Isto é
  *separation of concerns* na prática.
- **Dados de exemplo pequenos** (*fixtures*) com casos de borda: nulos,
  duplicatas, caracteres estranhos, fuso horário.
- **Integração com DB efêmero** — suba um PostgreSQL via
  [Docker](../../20-containers/README.md)/`testcontainers`, rode o pipeline, verifique
  o resultado.
- **Golden/snapshot tests** — compare a saída com um resultado esperado conhecido.
- **Idempotência** — rode o pipeline duas vezes e verifique que o resultado é o
  mesmo (ver [ETL](../../09-etl-elt/07-idempotency-retries/README.md)).

## Testes de dados (data tests) — distinção importante

Além de testar o **código**, você valida os **dados** em runtime: unicidade de
chaves, não-nulos, integridade referencial, distribuição, *freshness*. Isso é feito
com [dbt tests](../../28-dbt/README.md),
[Great Expectations](../../12-data-quality/05-great-expectations/README.md) ou
asserts no pipeline — ver [Data Quality](../../12-data-quality/README.md). Um
pipeline maduro tem **ambos**.

## Boas práticas

- Testes **rápidos e determinísticos** (sem depender de rede/hora real; "mocke" o
  tempo e serviços externos).
- Um comportamento por teste; nome descritivo (`test_dedupe_remove_duplicatas`).
- Rode testes no [CI](../../23-cicd-dataops/README.md) em todo PR.
- Teste **o que pode quebrar e importa**, não busque 100% de cobertura cega.
- TDD quando útil: escreva o teste antes para esclarecer o comportamento.

## Erros comuns

- Pipelines sem **nenhum** teste ("funcionou na minha máquina").
- Testes que dependem de dados de produção/rede → lentos e instáveis (*flaky*).
- Confundir testar código com testar dados (precisa dos dois).
- Lógica acoplada ao I/O, impossível de testar isoladamente.

## Relação com outros conceitos

- Testes de dados: [Data Quality](../../12-data-quality/README.md).
- Automação no [CI/CD](../../23-cicd-dataops/03-testing-build-deploy/README.md).
- Testes de Python: [04 — Python/testes](../../04-python-for-data-engineering/09-testing-python/README.md).

## Exercícios

1. Escreva uma função de limpeza de dados e cubra-a com testes parametrizados,
   incluindo nulos e duplicatas.
2. Refatore um script que lê um CSV, transforma e grava, separando a transformação
   (pura) do I/O; teste só a transformação.
3. Escreva um teste de idempotência: rodar a função duas vezes dá o mesmo
   resultado.
4. Suba um PostgreSQL de teste com Docker e escreva um teste de integração que
   insere e lê dados.

## Referências

- Documentação do `pytest` (docs.pytest.org).
- Beck, K. *Test-Driven Development by Example*.
- Percival, H. *Architecture Patterns with Python* (testes e arquitetura).
