# Typing (type hints)

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

## O que é

**Type hints** anotam os tipos esperados de variáveis, argumentos e retornos.
Python continua dinâmico em runtime, mas as anotações permitem que ferramentas
(como `mypy`) verifiquem consistência **antes** de rodar, e documentam o código.

```python
def media(valores: list[float]) -> float:
    return sum(valores) / len(valores)
```

## Por que importa em DE

Dados têm *shapes* e tipos que é fácil confundir: uma coluna é `str` ou `int`? um
campo é opcional? uma função retorna um DataFrame ou um caminho? Tipos:

- **Pegam bugs cedo** (passar `None` onde se espera `str`).
- **Documentam contratos** de funções — essencial em pipelines com muitos passos.
- **Melhoram o editor** (autocomplete, navegação).

## Sintaxe essencial

```python
from typing import Optional, Any
from collections.abc import Iterable, Iterator, Callable

nome: str = "felipe"
idades: list[int] = [20, 30]
mapa: dict[str, int] = {"a": 1}
par: tuple[str, int] = ("a", 1)
opcional: str | None = None          # Python 3.10+: união com |
qualquer: Any = ...                   # desliga a checagem (use com parcimônia)

def processa(
    linhas: Iterable[dict[str, Any]],
    *,
    chave: str,
) -> Iterator[dict[str, Any]]:
    ...
```

Notas:

- Desde 3.9/3.10, use `list`/`dict`/`tuple` minúsculos e `X | None` em vez de
  `List`, `Dict`, `Optional[X]`.
- `Iterable`/`Iterator` vêm de `collections.abc`.
- `X | None` é o idioma para "opcional".

## TypedDict, dataclass e Protocol (úteis para dados)

### dataclass — registros tipados

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Pedido:
    id: int
    valor: float
    cliente: str | None = None
```

Ótimo para representar linhas/registros de forma explícita e imutável. Ver
[stdlib/dataclasses](../05-stdlib-for-de/README.md).

### TypedDict — dicts com formato conhecido (ex.: JSON)

```python
from typing import TypedDict

class EventoJSON(TypedDict):
    id: str
    ts: int
    type: str
```

Descreve o formato de um registro JSON sem criar uma classe — o `mypy` valida os
acessos a chaves.

### Protocol — "duck typing" tipado

```python
from typing import Protocol

class SuportaRead(Protocol):
    def read(self) -> bytes: ...
```

Permite tipar "qualquer coisa que tenha `.read()`" — flexível para fontes de dados.

## mypy — verificando os tipos

```bash
pip install mypy
mypy src/
```

```python
def soma(xs: list[int]) -> int:
    return sum(xs)

soma(["a"])   # mypy: error — list[str] não é list[int]
```

Configuração em `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
disallow_untyped_defs = true   # exige anotar funções (ligue gradualmente)
```

## Validação em runtime: Pydantic

Type hints **não** validam dados em runtime. Para validar entradas externas (JSON de
API, configs), use **Pydantic**, que usa as anotações para validar/converter:

```python
from pydantic import BaseModel

class Config(BaseModel):
    db_url: str
    batch_size: int = 1000

cfg = Config(db_url="postgres://...", batch_size="500")  # converte "500"->500
```

Combinação comum em DE: *type hints* para o `mypy` (estático) + Pydantic para
validar dados de fronteira (runtime). Ver [data contracts](../../29-data-contracts/README.md).

## Tipagem gradual

Você não precisa tipar tudo de uma vez. Comece pelas **funções públicas** e
*interfaces* entre módulos; aprofunde conforme o projeto amadurece. `Any` é uma
válvula de escape — use consciente.

## Erros comuns

- Achar que type hints validam dados em runtime (não validam — use Pydantic).
- Abusar de `Any`, anulando o benefício.
- Anotar tipos errados que divergem do comportamento real (pior que não anotar).
- Esquecer `| None` em campos realmente opcionais.

## Boas práticas

- Tipagem gradual, começando por fronteiras de módulo.
- `mypy` no [CI](../../23-cicd-dataops/README.md).
- `dataclass`/`TypedDict` para registros; Pydantic para validação de entrada.

## Relação com outros conceitos

- Habilita [lint/mypy](../../03-git-software-engineering/06-linting-formatting/README.md).
- Conecta a [data contracts](../../29-data-contracts/README.md) e
  [data quality](../../12-data-quality/03-schema-validation/README.md).

## Exercícios

1. Anote uma função de transformação que recebe `list[dict]` e retorna `list[dict]`
   filtrado; rode o `mypy`.
2. Modele um registro de pedido com `dataclass(frozen=True)` e um evento JSON com
   `TypedDict`.
3. Crie um `BaseModel` Pydantic para validar a configuração de um pipeline e teste
   com uma entrada inválida.
4. Explique por que `mypy` aprova um código que, mesmo assim, pode falhar com dados
   reais — e como o Pydantic fecha essa lacuna.

## Referências

- Documentação de `typing` (docs.python.org) e `mypy`.
- Documentação do Pydantic (docs.pydantic.dev).
- PEP 484, 585, 604, 589 (TypedDict).
