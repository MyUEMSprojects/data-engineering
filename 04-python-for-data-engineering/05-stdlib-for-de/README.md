# Stdlib para Data Engineering

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

A biblioteca padrão (*standard library*) resolve muita coisa sem dependências
externas. Este tópico reúne os módulos que mais aparecem em pipelines.

## pathlib — caminhos como objetos

Prefira `pathlib` a `os.path`: mais legível e seguro.

```python
from pathlib import Path

raw = Path("/data/raw")
arquivo = raw / "vendas" / "2024-01-01.csv"   # junta com /
arquivo.exists(); arquivo.suffix; arquivo.stem
arquivo.parent.mkdir(parents=True, exist_ok=True)   # cria dir pai (idempotente)
for p in raw.glob("**/*.parquet"):                   # busca recursiva
    print(p)
texto = arquivo.read_text(encoding="utf-8")
```

## datetime, timezone e zoneinfo — datas sem dor

Fuso horário é a fonte nº 1 de bugs em dados. Regra: **trabalhe em UTC**, converta
só na apresentação.

```python
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

agora = datetime.now(timezone.utc)                 # SEMPRE aware (com tz)
ontem = agora - timedelta(days=1)
sp = agora.astimezone(ZoneInfo("America/Sao_Paulo"))
agora.isoformat()                                   # "2024-01-01T12:00:00+00:00"
datetime.strptime("2024-01-01", "%Y-%m-%d")        # parse
```

- **Naive vs aware:** `datetime` sem tz é "naive" → ambíguo. Prefira *aware*.
- Para partições de data em lakes, use strings `YYYY-MM-DD` derivadas de UTC.

## json — ler/escrever JSON

```python
import json

obj = json.loads('{"a": 1}')            # str -> dict
s = json.dumps(obj, ensure_ascii=False) # dict -> str (mantém acentos)
with open("out.json", "w", encoding="utf-8") as f:
    json.dump(obj, f, ensure_ascii=False, indent=2)
```

Para **JSONL** (um objeto por linha — formato comum de ingestão), itere linha a
linha (ver [generators](../06-iterators-generators-context-managers/README.md)):

```python
with open("eventos.jsonl", encoding="utf-8") as f:
    for linha in f:
        evento = json.loads(linha)
```

> `default=str` em `json.dumps` ajuda a serializar `datetime`/`Decimal`.

## csv — CSV correto (com aspas e escapes)

Não faça *split* por vírgula na mão; use o módulo `csv`, que entende aspas e
quebras de linha dentro de campos.

```python
import csv

with open("vendas.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):     # cada linha vira dict por cabeçalho
        print(row["produto"])

with open("out.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "valor"])
    w.writeheader(); w.writerow({"id": 1, "valor": 9.9})
```

## dataclasses — registros estruturados

```python
from dataclasses import dataclass, field, asdict

@dataclass(frozen=True, slots=True)
class Pedido:
    id: int
    valor: float
    itens: list[str] = field(default_factory=list)

p = Pedido(1, 9.9)
asdict(p)                 # vira dict (útil p/ serializar)
```

`frozen=True` (imutável) e `slots=True` (menos memória) são úteis em DE.

## argparse — CLIs de pipeline

Pipelines costumam receber parâmetros (data, ambiente). `argparse` cria uma
interface de linha de comando robusta.

```python
import argparse

def main() -> None:
    p = argparse.ArgumentParser(description="Ingestão diária de vendas")
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--env", choices=["dev", "prod"], default="dev")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    run(date=args.date, env=args.env, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
```

```bash
python -m meu_pipeline.ingest --date 2024-01-01 --env prod
```

(Para CLIs mais ricas, `click`/`typer` são alternativas populares, mas `argparse`
não exige dependência.)

## collections, itertools e functools

```python
from collections import Counter, defaultdict, namedtuple
from itertools import islice, chain, groupby, batched   # batched: Python 3.12+
from functools import reduce, lru_cache, partial

Counter(emails)                      # contagem/frequência
list(batched(range(10), 3))          # lotes: [(0,1,2),(3,4,5),...]
list(islice(gen, 100))               # pega 100 de um generator (sem materializar)

@lru_cache(maxsize=256)
def lookup(cep: str) -> dict: ...    # memoiza chamadas caras
```

`itertools.batched` (3.12+) é ótimo para processar em lotes; `islice` fatia
*generators* preguiçosamente.

## decimal — dinheiro sem erro de float

`float` tem imprecisão binária (`0.1 + 0.2 != 0.3`). Para valores monetários, use
`Decimal`:

```python
from decimal import Decimal
Decimal("0.1") + Decimal("0.2")      # Decimal('0.3')
```

## tempfile, shutil, os

```python
import tempfile, shutil, os
with tempfile.NamedTemporaryFile(delete=False) as tmp:
    tmp.write(b"...")
shutil.move(tmp.name, destino)       # escrita atômica: grava em tmp e move
os.environ["DATABASE_URL"]           # ler env (configuração)
```

O padrão "grava em temporário + `move`" garante **escrita atômica** (ninguém lê um
arquivo pela metade) — importante para idempotência.

## Erros comuns

- `datetime` naive e misturar fusos.
- *Split* manual de CSV (quebra com aspas/vírgulas internas).
- `float` para dinheiro.
- Montar caminhos com concatenação de strings em vez de `pathlib`.

## Boas práticas

- UTC em todo lugar; `pathlib` para caminhos; `csv`/`json` para formatos.
- `dataclass` para registros; `argparse` para parâmetros.
- Escrita atômica (tmp + move) em saídas de pipeline.

## Relação com outros conceitos

- `json`/`csv` conectam a [formatos de dados](../../08-data-formats/README.md).
- CLIs são acionadas por [orquestração](../../11-orchestration/README.md).

## Exercícios

1. Leia um JSONL grande linha a linha e escreva um CSV com `csv.DictWriter`.
2. Escreva uma função que recebe `--date` via `argparse` e deriva a partição UTC.
3. Processe um iterável em lotes de 500 com `itertools.batched`/`islice`.
4. Demonstre o erro de `float` com dinheiro e corrija com `Decimal`.

## Referências

- Documentação da stdlib (docs.python.org): `pathlib`, `datetime`, `zoneinfo`,
  `csv`, `json`, `dataclasses`, `argparse`, `itertools`, `decimal`.
