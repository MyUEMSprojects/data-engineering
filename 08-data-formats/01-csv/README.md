# CSV

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

**CSV (Comma-Separated Values)** é um formato de texto onde cada linha é um registro e os
campos são separados por um delimitador (vírgula, `;`, tab). É o formato mais universal e
simples — e, por isso mesmo, cheio de armadilhas.

```csv
id,nome,valor,uf
1,"Silva, João",99.90,SP
2,Maria,150.00,RJ
```

## Por que existe / quando usar

- **Universal** — qualquer ferramenta lê (Excel, bancos, linguagens).
- **Legível** por humanos; ótimo para troca simples, amostras, exports pontuais.
- **Use** para volumes pequenos/médios, interoperabilidade máxima, entrada/saída para
  pessoas.
- **Evite** para analytics em escala e armazenamento de longo prazo — prefira
  [Parquet](../04-parquet/README.md).

## As armadilhas do CSV (o que todo DE sofre)

CSV **não tem padrão rígido** (o RFC 4180 é frouxo e pouco seguido). Problemas comuns:

- **Delimitador dentro do valor** — "Silva, João" tem vírgula; precisa de **aspas**.
- **Aspas dentro de aspas** — escapadas como `""`.
- **Quebras de linha dentro de campos** — um campo com `\n` quebra parsers ingênuos.
- **Encoding** — UTF-8? latin-1? UTF-8 com BOM? Acentos corrompem se errar (ver
  [stdlib](../../04-python-for-data-engineering/05-stdlib-for-de/README.md)).
- **Sem tipos** — tudo é string; "01" vira `1`? datas em que formato? `NULL` vs `""` vs
  `"NULL"`?
- **Cabeçalho** — tem? sempre? nomes consistentes?
- **Delimitador regional** — em locais que usam vírgula decimal, o separador vira `;`.

Por isso: **nunca** faça parse de CSV com `split(',')`. Use um parser que entende aspas/
escapes (módulo `csv` do Python, pandas, [polars](../../04-python-for-data-engineering/12-polars/README.md)).

## Ler/escrever corretamente

```python
import csv
with open("dados.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):     # respeita aspas, escapes
        ...

# pandas / polars
import pandas as pd
df = pd.read_csv("dados.csv", dtype={"id": "int64"}, parse_dates=["data"])
import polars as pl
df = pl.read_csv("dados.csv")          # mais rápido para arquivos grandes
```

## Por que CSV é ruim para analytics em escala

- **Orientado a linha** — para somar uma coluna, lê o arquivo **inteiro** (ver
  [row vs columnar](../08-row-vs-columnar/README.md)).
- **Sem compressão eficiente** nem estatísticas/índices → muito I/O.
- **Sem schema** — custo de parse/inferência a cada leitura; tipos ambíguos.
- **Sem projeção** — não dá para ler só as colunas que você quer.

Em um data lake, CSV é aceitável na camada *raw* (como chegou), mas as camadas refinadas
devem ser [Parquet](../04-parquet/README.md).

## Boas práticas (quando CSV for inevitável)

- Especifique **encoding** (`utf-8`) e documente o delimitador.
- Sempre **cabeçalho** com nomes consistentes (`snake_case`).
- Aspas em campos com delimitador/quebra; escape padronizado.
- Documente o significado de `NULL`/vazio.
- Para volumes grandes, **comprima** (`.csv.gz`) e particione — ou melhor, converta para
  Parquet.
- Prefira **TSV** (tab) quando os dados têm muitas vírgulas (menos conflito).

## Erros comuns

- `split(',')` manual quebrando com aspas/vírgulas internas.
- Encoding errado → acentos corrompidos.
- Confiar em inferência de tipo (datas, "0123" viram números).
- Usar CSV como formato analítico de longo prazo.
- Misturar delimitadores/locale (vírgula decimal).

## Relação com outros conceitos

- Alternativa analítica: [Parquet](../04-parquet/README.md).
- Conceito por trás da lentidão: [row vs columnar](../08-row-vs-columnar/README.md).
- Ingestão/limpeza: [ETL](../../09-etl-elt/README.md); leitura em Python:
  [stdlib csv](../../04-python-for-data-engineering/05-stdlib-for-de/README.md).

## Exercícios

1. Crie um CSV com vírgulas e quebras de linha dentro de campos e prove que `split(',')`
   falha, mas o módulo `csv` acerta.
2. Leia o mesmo arquivo em UTF-8 e latin-1 e observe a corrupção de acentos.
3. Converta um CSV grande para Parquet e compare tamanho e tempo de uma agregação de
   coluna.
4. Liste 5 metadados que você documentaria ao entregar um CSV para outro time.

## Referências

- RFC 4180 (formato CSV).
- Documentação do módulo `csv` (Python), pandas e Polars.
