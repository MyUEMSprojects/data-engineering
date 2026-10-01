# Essenciais da linguagem (para DE)

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

Revisão dos fundamentos de Python **pela ótica de dados**. Se você já programa,
use como checklist; o foco é o que mais aparece em pipelines.

## Tipos e estruturas de dados

| Estrutura | Quando usar em DE |
| --- | --- |
| `list` | sequência ordenada mutável (coletar linhas, lotes) |
| `tuple` | registro imutável, chaves compostas |
| `dict` | mapeamento chave→valor (linha JSON, lookup, contagem) |
| `set` | unicidade, deduplicação, testes de pertencimento rápidos |
| `str`/`bytes` | texto vs dados binários (atenção a *encoding*!) |

```python
# contagem e deduplicação são onipresentes em DE
from collections import Counter, defaultdict
Counter(["a", "a", "b"])            # Counter({'a': 2, 'b': 1})
vistos = set()                       # dedupe por chave
```

### Mutabilidade e aliasing (uma pegadinha clássica)

```python
a = [1, 2, 3]
b = a            # b aponta para a MESMA lista
b.append(4)      # a também muda!
c = a.copy()     # cópia rasa (shallow)
```

Em dados, cópias acidentais vs referências compartilhadas causam bugs sutis.
Entenda *shallow* vs *deep copy* (`copy.deepcopy`).

## Funções

```python
def normalize(nome: str, *, maiusc: bool = False) -> str:
    out = nome.strip()
    return out.upper() if maiusc else out.lower()
```

- **Argumentos keyword-only** (após `*`) tornam chamadas claras — útil em funções
  com muitos parâmetros de configuração.
- **Nunca** use objeto mutável como default (`def f(x=[])`) — ele é compartilhado
  entre chamadas. Use `None` e crie dentro.

```python
def coletar(itens: list | None = None) -> list:
    itens = itens if itens is not None else []
    ...
```

## Comprehensions e expressões

```python
quadrados = [x*x for x in nums if x > 0]        # list comprehension
por_id = {r["id"]: r for r in registros}         # dict comprehension
unicos = {r["email"] for r in registros}         # set comprehension
gen = (parse(line) for line in arquivo)          # GENERATOR (lazy) — ver tópico 06
```

Comprehensions são idiomáticas e rápidas; o `generator` (parênteses) é crucial
para dados grandes (não materializa tudo na memória).

## Módulos e pacotes

```python
# estrutura: src/meu_pipeline/{__init__.py, transform.py}
from meu_pipeline.transform import clean      # import absoluto (preferir)
```

- Um **módulo** é um arquivo `.py`; um **pacote** é um diretório com código.
- Prefira **imports absolutos**; evite `from x import *`.
- Ver [organização de projetos](../../03-git-software-engineering/07-project-organization/README.md).

## Fatiamento (slicing) e desempacotamento

```python
linhas[1:]          # pula cabeçalho
linhas[-10:]        # últimas 10
primeiro, *resto = valores
chave, valor = par
```

## Strings, encoding e datas (cuidados de DE)

- **Encoding:** sempre especifique `encoding="utf-8"` ao abrir arquivos; dados
  reais vêm com acentuação e *encodings* variados (latin-1, UTF-8 com BOM).
- **f-strings** para formatar: `f"{total:,.2f}"`.
- **Datas:** fuso horário é fonte nº 1 de bugs — prefira *timezone-aware*
  (`datetime.now(tz=UTC)`), padronize em UTC. Ver [stdlib/datetime](../05-stdlib-for-de/README.md).

## Verdade, None e comparações

```python
if valor is None: ...        # compare None com `is`, não `==`
if not lista: ...            # lista vazia é "falsy"
```

Cuidado: `0`, `""`, `[]`, `{}`, `None` são todos *falsy* — distinga "ausente"
(`None`) de "zero/vazio" ao tratar dados.

## Erros comuns

- Default mutável em função.
- Confundir referência com cópia ao transformar dados.
- Esquecer `encoding` ao ler/escrever arquivos.
- Usar `==` para comparar com `None`.
- Materializar listas gigantes quando um *generator* bastaria.

## Boas práticas

- Nomes descritivos; funções pequenas e com uma responsabilidade.
- Prefira estruturas da stdlib (`collections`) a reinventar.
- Código *pythonic*: comprehensions, desempacotamento, context managers.

## Relação com outros conceitos

- Base para todos os outros tópicos do módulo.
- Aplica-se em [ETL](../../09-etl-elt/README.md) e [pipelines](../../10-data-pipelines/README.md).

## Exercícios

1. Dada uma lista de dicts (registros), gere um dict indexado por `id` e um set de
   e-mails únicos.
2. Escreva uma função com argumento *keyword-only* `strict: bool` que muda o
   comportamento de limpeza.
3. Demonstre o bug do default mutável e corrija-o.
4. Leia um CSV com acentuação em UTF-8 e em latin-1; explique o que acontece se
   errar o encoding.

## Referências

- Ramalho, L. *Fluent Python*, 2ª ed. — caps. 1–3, 7.
- Documentação oficial (docs.python.org), módulo `collections`.
