# Row vs Columnar

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

A forma como os dados de uma tabela são **fisicamente organizados** em disco/memória:

- **Row-based (orientado a linha)** — guarda todos os valores de uma linha juntos, uma
  linha após a outra.
- **Columnar (orientado a coluna)** — guarda todos os valores de uma coluna juntos, uma
  coluna após a outra.

Este é **o conceito mais importante do módulo** — explica por que [Parquet](../04-parquet/README.md)/
[warehouses](../../13-data-warehouse/README.md) são rápidos para analytics e por que
[OLTP vs OLAP](../../01-foundations/07-oltp-vs-olap/README.md) usam armazenamentos opostos.

## A diferença, visualmente

Tabela:

```text
id | nome  | valor | uf
1  | Ana   | 100   | SP
2  | Bob   | 200   | RJ
3  | Carol | 150   | SP
```

```text
Row-based (CSV, OLTP, Avro):
[1,Ana,100,SP] [2,Bob,200,RJ] [3,Carol,150,SP]
→ uma linha inteira é contígua

Columnar (Parquet, ORC, warehouse):
[1,2,3] [Ana,Bob,Carol] [100,200,150] [SP,RJ,SP]
→ cada coluna é contígua
```

## Por que importa: padrões de acesso opostos

### OLTP (transacional) → prefere row-based

"Me dê o pedido 2 **inteiro**" ou "atualize a linha do cliente 7". Tudo da linha está
junto → uma leitura/escrita pega o registro completo. Ver
[OLTP](../../01-foundations/07-oltp-vs-olap/README.md).

### OLAP (analítico) → prefere columnar

"Some `valor` de 1 bilhão de linhas". No columnar, lê-se **só a coluna `valor`**,
ignorando `nome`, `uf`, etc. → uma fração do I/O. No row-based, seria preciso ler **todas
as colunas de todas as linhas** só para somar uma.

```text
SUM(valor) de 1 bilhão de linhas:
row-based:   lê todas as colunas de todas as linhas (muito I/O desperdiçado)
columnar:    lê só a coluna valor (I/O mínimo) ✅
```

## As três vantagens do columnar para analytics

1. **Menos I/O (column pruning)** — lê só as colunas da query. Consultas analíticas tocam
   poucas colunas de muitas linhas.
2. **Compressão muito melhor** — valores do **mesmo tipo e domínio** ficam juntos (todos
   os `uf` em sequência: `SP,RJ,SP,SP,...`), o que comprime muito (RLE, dictionary). Ver
   [compressão](../09-compression/README.md).
3. **Vetorização / data skipping** — processar uma coluna contígua é cache-friendly e
   vetorizável (SIMD); estatísticas por bloco (min/max) permitem **pular** dados
   (*predicate pushdown*).

## Por que row-based vence em OLTP

- Escrever/ler **uma linha inteira** é uma operação única e contígua.
- Updates pontuais não precisam tocar todas as colunas em locais diferentes.
- Baixa latência por registro, alta concorrência de pequenas operações.

## Resumo comparativo

| Aspecto | Row-based | Columnar |
| --- | --- | --- |
| Melhor para | OLTP, pegar/gravar linhas inteiras | OLAP, agregar colunas |
| Leitura de poucas colunas | lê tudo | lê só o necessário ✅ |
| Escrita linha a linha | eficiente ✅ | ineficiente (acumula) |
| Compressão | moderada | excelente ✅ |
| Updates pontuais | ok ✅ | caro (reescrever) |
| Exemplos | CSV, Avro, Postgres/MySQL (heap) | Parquet, ORC, BigQuery, Redshift |

## Não é tudo preto-no-branco

- Alguns bancos OLTP têm **índices/réplicas colunares** para acelerar analytics (ex.:
  Postgres com extensões; HTAP).
- [Apache Arrow](../../04-python-for-data-engineering/13-pyarrow/README.md) é columnar **em
  memória** (acelera processamento), enquanto Parquet é columnar **em disco**.
- *Lakehouse* ([Delta/Iceberg](../../15-lakehouse/README.md)) usa Parquet (columnar) +
  camada de metadados para trazer updates/ACID ao mundo colunar.

## Erros comuns

- Usar CSV/row-based para analytics em escala → I/O e custo enormes.
- Usar colunar para OLTP/escrita linha a linha → péssimo desempenho.
- Confundir "columnar" (layout analítico, Parquet) com "wide-column" NoSQL
  ([Cassandra](../../06-databases/04-nosql/03-column-family/README.md)) — nomes parecidos,
  coisas diferentes.
- `SELECT *` num warehouse colunar (anula o benefício do pruning).

## Boas práticas

- Columnar (Parquet) para camadas analíticas; row-based para OLTP.
- Selecione só as colunas necessárias para aproveitar o pruning.
- Entenda que a mesma tabela pode viver em formatos diferentes conforme o uso.

## Relação com outros conceitos

- Motiva [Parquet](../04-parquet/README.md)/[ORC](../06-orc/README.md) e
  [warehouses](../../13-data-warehouse/README.md).
- Base de [OLTP vs OLAP](../../01-foundations/07-oltp-vs-olap/README.md).
- Arrow em memória: [PyArrow](../../04-python-for-data-engineering/13-pyarrow/README.md).

## Exercícios

1. Desenhe como a tabela de exemplo fica em disco nos dois layouts.
2. Explique, em termos de I/O, por que `SUM(valor)` é muito mais barato no columnar.
3. Dê um caso onde row-based é a escolha certa e justifique.
4. Diferencie "columnar analítico" de "wide-column NoSQL".

## Referências

- Kleppmann, M. *DDIA* — cap. 3 ("Column-Oriented Storage").
- Abadi, D. et al. — papers sobre column stores (C-Store/Vertica).
- Documentação do Apache Parquet e do Arrow.
