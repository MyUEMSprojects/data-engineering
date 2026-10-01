# Compressão

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

**Compressão** reduz o tamanho dos dados em disco/rede, codificando-os de forma mais
eficiente. Em Data Engineering, compressão não é só "economizar espaço" — é **reduzir I/O
e custo** (menos bytes lidos = consultas mais rápidas e, em cloud, contas menores).

## Por que importa

- **Menos I/O** — ler dados comprimidos é frequentemente **mais rápido** (o gargalo
  costuma ser o disco/rede, não a CPU que descomprime).
- **Menos custo** — storage e, crucialmente, **bytes lidos** (BigQuery/Athena cobram por
  isso).
- **Menos banda** — transferências e replicação mais baratas.

## Dois tipos de compressão

### Encoding (compressão leve, específica de formato)

Formatos colunares ([Parquet](../04-parquet/README.md)/[ORC](../06-orc/README.md)) aplicam
*encodings* **antes** do codec geral, aproveitando que valores da mesma coluna são
parecidos:

- **Dictionary encoding** — substitui valores repetidos por índices de um dicionário
  (ótimo para baixa cardinalidade: `uf`, `status`).
- **Run-Length Encoding (RLE)** — `SP,SP,SP,SP` → `(SP, 4)`.
- **Delta encoding** — guarda diferenças entre valores próximos (bom para timestamps/ids
  sequenciais).

Isso é o motivo de colunar comprimir tão bem (ver
[row vs columnar](../08-row-vs-columnar/README.md)).

### Codecs de compressão (compressão geral)

Aplicados por cima: **snappy, gzip, zstd, lz4, brotli, bzip2**. Trocam **velocidade** por
**razão de compressão**.

## Comparação dos codecs

| Codec | Velocidade | Razão | Splittable* | Uso típico |
| --- | --- | --- | --- | --- |
| **snappy** | muito rápida | moderada | sim (em Parquet) | **padrão** em Parquet/analytics |
| **zstd** | rápida + ajustável | alta | sim (em Parquet) | ótimo equilíbrio (cada vez mais o default) |
| **lz4** | rapidíssima | baixa/moderada | sim | latência mínima |
| **gzip** | lenta | alta | **não** (como .gz puro) | arquivos texto, compatibilidade |
| **brotli** | lenta | muito alta | sim (em Parquet) | arquivamento |
| **bzip2** | muito lenta | muito alta | sim | raro |

\* "Splittable" = pode ser dividido em pedaços para processamento paralelo (importante em
[Spark](../../16-distributed-processing/README.md)). Um **`.csv.gz`** inteiro **não** é
splittable (um worker tem que descomprimir tudo) — um gargalo clássico. Já a compressão
**dentro** do Parquet é splittable por row group, independentemente do codec.

## Como escolher

```text
Analytics/lake (Parquet)      → snappy (padrão) ou zstd (melhor razão, pouco custo) ✅
Latência mínima               → lz4/snappy
Arquivamento/cold storage     → zstd (nível alto)/gzip/brotli
Texto para troca/compat.      → gzip
Spark em arquivos de texto    → evite .gz (não splittable); use formatos splittable
```

**Recomendação prática:** Parquet + **zstd** (ou snappy) para a maioria dos casos de
analytics. zstd dá razão de gzip com velocidade perto de snappy.

## Exemplo

```python
import pandas as pd
df.to_parquet("vendas.zstd.parquet", compression="zstd")
df.to_parquet("vendas.snappy.parquet", compression="snappy")
```

```bash
# compressão de texto
gzip -9 dados.csv          # máxima razão, lento
zstd -19 dados.csv         # razão alta, mais rápido que gzip -9
```

## Trade-offs a entender

- **CPU vs I/O** — mais compressão gasta mais CPU; compensa quando o I/O (disco/rede/custo)
  é o gargalo (quase sempre em analytics). Para dados "quentes" lidos o tempo todo, um
  codec rápido (snappy/lz4) pode ganhar.
- **Compressão vs splittability** — escolha codecs/formatos que permitam paralelismo em
  processamento distribuído.
- **Tamanho do bloco** — row groups/stripes muito pequenos reduzem a eficiência da
  compressão (ver [small files](../../14-data-lake/06-small-files-compaction/README.md)).

## Erros comuns

- Armazenar CSV/JSON sem compressão (desperdício enorme).
- Usar `.csv.gz` grande em Spark (não splittable → um worker só).
- Buscar sempre a razão máxima (gzip/brotli) quando a velocidade importa mais.
- Ignorar que colunar + encoding já comprime muito antes do codec.

## Boas práticas

- Dados analíticos em Parquet com snappy/zstd.
- Prefira formatos/codecs splittable para processamento distribuído.
- zstd como bom default de equilíbrio; ajuste o nível conforme quente/frio.
- Dimensione row groups/arquivos para boa razão de compressão.

## Relação com outros conceitos

- Habilitada por [Parquet](../04-parquet/README.md)/[ORC](../06-orc/README.md) e
  [row vs columnar](../08-row-vs-columnar/README.md).
- Impacta [custo](../../19-cloud/08-cost-management/README.md) e
  [performance de Spark](../../16-distributed-processing/11-performance-tuning/README.md).
- Relaciona-se a [small files/compaction](../../14-data-lake/06-small-files-compaction/README.md).

## Exercícios

1. Grave o mesmo DataFrame em Parquet com snappy, zstd e gzip; compare tamanho e tempo de
   leitura.
2. Explique por que um `.csv.gz` gigante é ruim para Spark.
3. Para um dataset "quente" (lido muitas vezes) vs "frio" (arquivado), escolha codecs e
   justifique.
4. Demonstre o efeito do dictionary encoding numa coluna de baixa cardinalidade.

## Referências

- Documentação do Apache Parquet (encodings e compressão).
- facebook/zstd, google/snappy (docs dos codecs).
- Kleppmann, M. *DDIA* — cap. 3.
