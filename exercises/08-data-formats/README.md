# Exercícios — Módulo 08: Formatos de dados

Teoria em [08-data-formats](../../08-data-formats/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Linha × coluna

Por que uma consulta `SELECT avg(amount) FROM sales` é muito mais rápida em Parquet do que em CSV com os mesmos dados?

<details><summary>Gabarito</summary>

Parquet é **colunar**: lê só a coluna `amount` (*column pruning*), comprimida por tipo (dicionário/RLE) e com estatísticas por *row group*. CSV é textual por linha: precisa ler e *parsear* **todas** as colunas. Ver [linha vs coluna](../../08-data-formats/08-row-vs-columnar/README.md) e a medição do [Projeto 06](../../projects/06-spark/README.md) (E1).
</details>

## 2. 🟢 Conceitual — JSON Lines

Por que pipelines preferem **JSONL** a um único array JSON `[ {...}, {...} ]` para arquivos grandes?

<details><summary>Gabarito</summary>

JSONL tem **um registro por linha**: dá para processar em *streaming*, dividir o arquivo em partes, anexar (`append`) e tolerar uma linha corrompida sem invalidar o arquivo. O array único exige parsear tudo na memória e é inválido se truncado.
</details>

## 3. 🔵 Debugging — O CSV que quebra

Um CSV tem a linha `10,"Silva, João",Av. "Paulista" 100,paid`. O parser ingênuo `line.split(",")` devolve 6 campos. Quais são **três** armadilhas de CSV e como lidar com elas?

<details><summary>Gabarito</summary>

(1) **Delimitador dentro de campo** (aspas); (2) **aspas escapadas** (`""`); (3) **quebras de linha** dentro de campo, **encoding** (UTF-8 × Latin-1/BOM) e ausência de **tipos/nulos** (`""` × vazio × `NULL`). Use um parser de verdade (`csv`, `pyarrow.csv`), declare **schema e encoding**, e prefira Parquet/JSONL em pipelines. Ver [CSV](../../08-data-formats/01-csv/README.md).
</details>

## 4. 🔵 Conceitual — Evolução de schema

Uma coluna `coupon` (opcional) será adicionada a um tópico/arquivo. Classifique como **backward**, **forward** ou **full** compatível cada mudança: (a) adicionar campo **com default**; (b) remover campo **obrigatório**; (c) renomear campo; (d) adicionar campo **sem default**.

<details><summary>Gabarito</summary>

(a) **backward e forward** (full) quando o campo é opcional/tem default. (b) quebra **forward** (leitores antigos esperam o campo) — e é *backward* só se leitores novos o ignoram. (c) **quebra ambos** (é remover + adicionar) — use *alias*. (d) quebra **backward**: leitor novo não consegue ler dados antigos sem valor. Regra: **só adicione campos opcionais**. Ver [evolução de schema](../../08-data-formats/10-schema-evolution/README.md) e [compatibilidade](../../29-data-contracts/04-compatibility-versioning/README.md).
</details>

## 5. 🟣 Implementação — Medir formato e compressão

Escreva um script que gera 1 milhão de linhas e compara **tamanho em disco** e **tempo de leitura de uma coluna** em CSV, Parquet+snappy e Parquet+zstd.

<details><summary>Gabarito</summary>

```python
import os, time, pyarrow as pa, pyarrow.csv as pc, pyarrow.parquet as pq, numpy as np

n = 1_000_000
t = pa.table({"id": np.arange(n), "amount": np.random.rand(n) * 100, "status": np.random.choice(["paid", "shipped", "canceled"], n)})
pc.write_csv(t, "t.csv")
pq.write_table(t, "t_snappy.parquet", compression="snappy")
pq.write_table(t, "t_zstd.parquet", compression="zstd")

for f in ["t.csv", "t_snappy.parquet", "t_zstd.parquet"]:
    s = time.perf_counter()
    col = pc.read_csv(f)["amount"] if f.endswith(".csv") else pq.read_table(f, columns=["amount"])["amount"]
    print(f"{f:18} {os.path.getsize(f)/1e6:7.1f} MB  leitura de 'amount': {time.perf_counter()-s:.3f}s")
```

Resultado típico (1 M linhas, 3 colunas): CSV ≈ 34 MB, Parquet+snappy ≈ 13 MB, +zstd ≈ 9 MB, e leitura de uma coluna mais rápida em Parquet (a diferença cresce com o nº de colunas); **zstd** comprime mais que snappy (mais CPU). Dados aleatórios comprimem mal — repita com dados reais. Ver [compressão](../../08-data-formats/09-compression/README.md).
</details>

## 6. 🟣 Arquitetura — Formato por camada

Escolha o formato para: (a) tópico Kafka de eventos com múltiplos produtores; (b) camada bronze de um lake; (c) gold consultada por BI; (d) payload de uma API interna entre serviços. Justifique.

<details><summary>Gabarito</summary>

(a) **Avro** (ou Protobuf) + *schema registry*: schema compacto e evolução controlada. (b) **JSONL/Avro cru** (preserva o original) ou Parquet se já tipado. (c) **Parquet** (ou tabela Delta/Iceberg): colunar, com *pushdown*. (d) **Protobuf/JSON**: contrato forte e baixa latência (Protobuf) ou simplicidade (JSON). Ver [Avro](../../08-data-formats/05-avro/README.md), [Protobuf](../../08-data-formats/07-protobuf/README.md).
</details>
