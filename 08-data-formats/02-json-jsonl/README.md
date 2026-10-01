# JSON / JSONL

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

- **JSON (JavaScript Object Notation)** — formato de texto para dados **semiestruturados**
  (objetos aninhados, arrays, tipos básicos). Onipresente em APIs.
- **JSONL / NDJSON (JSON Lines)** — **um objeto JSON por linha**. É a forma correta de
  armazenar/streamar muitos registros JSON.

```json
{"id": 1, "cliente": {"nome": "Ana", "uf": "SP"}, "itens": ["x", "y"]}
```

```jsonl
{"id": 1, "type": "click", "ts": 1700000000}
{"id": 2, "type": "purchase", "ts": 1700000005}
```

## Por que existe / quando usar

- **APIs** retornam JSON — é o formato de ingestão nº 1 (ver
  [HTTP clients](../../04-python-for-data-engineering/08-http-clients/README.md)).
- **Semiestruturado** — bom para dados com schema variável/aninhado (eventos, logs,
  documentos).
- **Use** para ingestão de APIs, logs de eventos, camada *raw* de lakes, configs.
- **Evite** para analytics em escala (prefira [Parquet](../04-parquet/README.md)) — JSON é
  verboso, sem tipos fortes e caro de parsear.

## JSON vs JSONL (diferença crucial)

Um arquivo com **um array JSON gigante** (`[{...}, {...}, ...]`) exige carregar o arquivo
inteiro na memória para parsear → ruim para dados grandes. **JSONL** (um objeto por linha)
permite processar **linha a linha** via [generators](../../04-python-for-data-engineering/06-iterators-generators-context-managers/README.md),
é *append-friendly* (dá para anexar registros) e *splittable* (processamento paralelo).

```python
import json
# JSONL: streaming, memória constante
with open("eventos.jsonl", encoding="utf-8") as f:
    for linha in f:
        evento = json.loads(linha)
```

> Para armazenar muitos registros, **use JSONL, não um array JSON único.**

## Tipos e armadilhas

- Tipos JSON: string, number, boolean, null, object, array. **Não há data/decimal
  nativos** → datas viram strings (padronize ISO-8601/UTC); dinheiro em number perde
  precisão (ver [decimal](../../04-python-for-data-engineering/05-stdlib-for-de/README.md)).
- **Números grandes** (int64) podem perder precisão em parsers que usam float.
- **Schema variável** — cada objeto pode ter campos diferentes; ótimo para flexibilidade,
  ruim para consumo a jusante (precisa normalizar/validar).
- **Encoding** — sempre UTF-8; use `ensure_ascii=False` para preservar acentos ao
  escrever.

## Dados aninhados: o desafio da ingestão

JSON é hierárquico; o mundo analítico é tabular. Ingerir JSON exige **achatar**
(*flatten*) e **explodir** arrays em linhas:

```json
{"pedido": 1, "itens": [{"prod": "x", "qtd": 2}, {"prod": "y", "qtd": 1}]}
```

vira (explodindo `itens`):

```text
pedido | prod | qtd
  1    |  x   |  2
  1    |  y   |  1
```

Ferramentas: [pandas](../../04-python-for-data-engineering/11-pandas/README.md)
(`json_normalize`), [polars](../../04-python-for-data-engineering/12-polars/README.md)
(`explode`/`unnest`), Spark (`explode`), ou SQL com
[JSON functions / LATERAL](../../05-sql/13-analytical-sql/README.md). Warehouses modernos
(BigQuery/Snowflake/DuckDB) têm suporte nativo a JSON e arrays.

## Validação de schema

JSON não impõe schema. Para confiabilidade, valide na entrada:

- **[Pydantic](../../04-python-for-data-engineering/03-typing/README.md)** em Python.
- **JSON Schema** (padrão para descrever/validar a estrutura).
- [Data contracts](../../29-data-contracts/README.md) com o produtor.

## Performance

- Parsear JSON é **caro** (texto → objetos). Em escala, bibliotecas rápidas (`orjson`,
  parsers do polars/Arrow) ajudam.
- Para analytics repetido, **converta JSON para Parquet** uma vez e consulte o Parquet.

## Erros comuns

- Armazenar um array JSON único gigante em vez de JSONL → estouro de memória.
- `float` para dinheiro / perder precisão de int64.
- Datas como strings sem padrão/UTC.
- Confiar no schema (que varia) sem validar.
- Fazer analytics direto sobre JSON em vez de converter para colunar.

## Boas práticas

- JSONL para múltiplos registros; UTF-8 + `ensure_ascii=False`.
- Padronize datas (ISO-8601/UTC) e trate decimais com cuidado.
- Valide com Pydantic/JSON Schema na ingestão.
- Converta para [Parquet](../04-parquet/README.md) nas camadas refinadas.

## Relação com outros conceitos

- Ingestão de [APIs](../../04-python-for-data-engineering/08-http-clients/README.md).
- Postgres armazena/consulta JSON ([jsonb](../../06-databases/02-postgresql/README.md)).
- Alternativa com schema para streaming: [Avro](../05-avro/README.md).
- Achatamento na [transformação](../../09-etl-elt/03-transformation/README.md).

## Exercícios

1. Converta um array JSON grande em JSONL e processe-o com memória constante.
2. Ache um pedido com `itens` aninhados e explode-o em linhas (pandas/polars).
3. Valide eventos JSON com um modelo Pydantic e rejeite os inválidos.
4. Compare o tamanho e o tempo de agregação de um JSONL vs o mesmo dado em Parquet.

## Referências

- json.org; RFC 8259 (JSON); jsonlines.org.
- JSON Schema (json-schema.org); documentação `json`/`orjson`, pandas `json_normalize`.
