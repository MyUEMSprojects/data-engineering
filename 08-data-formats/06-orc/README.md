# ORC

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

**Apache ORC (Optimized Row Columnar)** é um formato de arquivo **colunar**, binário e
comprimido, criado no ecossistema **Hive/Hadoop**. Conceitualmente é muito parecido com o
[Parquet](../04-parquet/README.md): otimizado para analytics, com projeção de colunas,
compressão e *data skipping* por estatísticas.

## Por que existe

Surgiu para melhorar a performance do Hive sobre o formato RCFile. Oferece armazenamento
colunar eficiente, índices leves embutidos e, historicamente, melhor integração com Hive
e suporte a **transações ACID** no Hive antes do Parquet ter equivalentes no mundo
lakehouse.

## Estrutura interna

```text
Arquivo ORC
├── Stripes (blocos de ~64–256 MB de linhas)
│   ├── Index Data (min/max, posições → data skipping)
│   ├── Row Data (dados por coluna, comprimidos)
│   └── Stripe Footer
├── File Footer (schema, estatísticas, lista de stripes)
└── Postscript (versão, compressão)
```

- **Stripes** ≈ *row groups* do Parquet.
- **Índices leves** por stripe (min/max, e opcionalmente *bloom filters*) → pula stripes/
  *row groups* que não casam com o filtro.
- Estatísticas no footer para projeção e pushdown.

## ORC vs Parquet

São tão parecidos que a escolha geralmente é ditada pelo **ecossistema**, não por
diferenças técnicas dramáticas:

| | Parquet | ORC |
| --- | --- | --- |
| Layout | colunar | colunar |
| Origem/ecossistema | Spark, universal, cloud | Hive/Hadoop |
| Suporte amplo | **mais universal** (cloud, engines modernas) | forte em Hive/Hadoop |
| Compressão | excelente | excelente (às vezes ligeiramente melhor) |
| Tipos aninhados | sim (Dremel) | sim |
| ACID histórico | via lakehouse | Hive ACID nativo (antigo) |

Na prática moderna (cloud, Spark, lakehouse), **Parquet é o default**; ORC domina onde há
**Hive legado** ou política específica do ecossistema. Ambos são colunares e você escolhe
pelo que o resto do stack usa.

## Lendo/escrevendo

```python
import pyarrow.orc as orc
import pyarrow as pa

table = orc.read_table("vendas.orc", columns=["id", "valor"])
with open("out.orc", "wb") as f:
    orc.write_table(table, f)
```

Spark: `df.write.format("orc").save(...)` / `spark.read.orc(...)`.

## Quando usar

- **Use ORC** quando o ambiente é **Hive/Hadoop** ou a organização padronizou nele.
- **Prefira [Parquet](../04-parquet/README.md)** para projetos novos, cloud, Spark,
  [lakehouse](../../15-lakehouse/README.md) e interoperabilidade máxima.

## Erros comuns

- Debater ORC vs Parquet como se fosse decisão crítica — siga o ecossistema; ambos são
  ótimos colunares.
- Misturar ORC e Parquet no mesmo dataset sem necessidade (complica ferramentas).
- Esperar comportamento de linha (ORC é colunar; mesmas limitações de mutação que
  Parquet — ver [lakehouse](../../15-lakehouse/README.md) para ACID/updates).

## Boas práticas

- Dimensione stripes adequadamente; aproveite bloom filters para colunas de filtro de
  igualdade.
- Column pruning + predicate pushdown (como no Parquet).
- Padronize **um** formato colunar por plataforma.

## Relação com outros conceitos

- Conceito base: [row vs columnar](../08-row-vs-columnar/README.md).
- Primo direto: [Parquet](../04-parquet/README.md).
- Ecossistema: Hive/[warehouse](../../13-data-warehouse/README.md),
  [lakehouse](../../15-lakehouse/README.md).

## Exercícios

1. Grave o mesmo dataset em ORC e Parquet e compare tamanho e tempo de agregação.
2. Explique quando você escolheria ORC em vez de Parquet.
3. Descreva como o *data skipping* por stripe funciona em ORC.

## Referências

- Documentação do Apache ORC (orc.apache.org).
- Documentação do Hive; PyArrow ORC.
