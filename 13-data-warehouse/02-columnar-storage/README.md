# Columnar storage (no warehouse)

> 🔵 Analytics Platforms · Parte de [13 — Data Warehouse](../README.md)

## O que é

Warehouses analíticos armazenam dados **por coluna** (não por linha), assim como os formatos
[Parquet/ORC](../../08-data-formats/04-parquet/README.md). Este é o mecanismo central por trás da
performance de um warehouse. O conceito geral está em
[row vs columnar](../../08-data-formats/08-row-vs-columnar/README.md); aqui vemos como ele se
manifesta **dentro do warehouse** e o que isso implica no seu uso diário.

## Por que o warehouse é colunar

Consultas analíticas tocam **poucas colunas de muitas linhas** (`SUM(valor) GROUP BY uf`).
Armazenamento colunar entrega três ganhos decisivos:

1. **Column pruning** — lê só as colunas da query (menos I/O e, em cobrança por bytes, menos
   custo).
2. **Compressão forte** — valores do mesmo tipo/domínio juntos comprimem muito (dictionary, RLE)
   → menos dados em disco e em trânsito (ver [compressão](../../08-data-formats/09-compression/README.md)).
3. **Vetorização e data skipping** — processar uma coluna contígua é cache-friendly/SIMD, e
   estatísticas por bloco (min/max) permitem **pular** dados que não casam o filtro.

## Implicações práticas (o que muda no seu dia a dia)

### `SELECT *` é caro — selecione colunas

Como só as colunas lidas custam I/O (e dinheiro no BigQuery), `SELECT *` lê tudo. Sempre
selecione as colunas necessárias:

```sql
-- caro: lê TODAS as colunas
SELECT * FROM fct_vendas WHERE dt = '2024-01-15';
-- barato: lê só 2 colunas
SELECT uf, valor FROM fct_vendas WHERE dt = '2024-01-15';
```

### Tabelas largas não penalizam quem não usa as colunas

No colunar, adicionar colunas que você não consulta **não** encarece queries que não as usam
(só ocupam storage). Isso favorece dimensões largas e desnormalizadas (ver
[dimensões](../../07-data-modeling/08-dimension-tables/README.md)).

### Filtros se beneficiam de data skipping

Estatísticas por bloco (min/max) + [particionamento/clustering](../03-partitioning-clustering/README.md)
permitem pular grandes faixas de dados — por isso filtrar por coluna de partição/cluster é tão
eficaz.

## Micro-partições / blocos

Cada warehouse organiza os dados colunares em blocos com estatísticas:

- **BigQuery** — armazenamento colunar (Capacitor) + partições + clustering.
- **Snowflake** — **micro-partitions** automáticas (~16 MB comprimidos) com min/max por coluna;
  *pruning* automático baseado nelas; clustering keys melhoram a organização.
- **Redshift** — blocos de 1 MB por coluna com **zone maps** (min/max) para skipping; *sort keys*
  organizam fisicamente.

A ideia é a mesma: dados colunares + estatísticas por bloco = pular o que não interessa.

## Encoding e compressão automáticos

Warehouses escolhem/aplicam encodings por coluna automaticamente (dictionary para baixa
cardinalidade, etc.), então colunas de baixa cardinalidade (`status`, `uf`) comprimem
excelentemente e são baratas de ler.

## Por que não é bom para OLTP

Colunar é péssimo para escritas/updates pontuais linha a linha (precisaria tocar muitos blocos
de colunas). Por isso warehouses são **append/batch** e não substituem bancos
[OLTP](../../01-foundations/07-oltp-vs-olap/README.md). Updates/deletes existem mas são caros;
prefira padrões de [carga](../../09-etl-elt/04-loading/README.md) batch (append/overwrite por
partição/merge).

## Erros comuns

- `SELECT *` (lê e paga por colunas que não usa).
- Fazer muitos `UPDATE`/`DELETE` pontuais (colunar não é OLTP).
- Esquecer que filtrar por coluna não particionada/clusterizada não aproveita skipping.
- Tipos ineficientes (strings enormes onde um enum/categoria serviria).

## Boas práticas

- Selecione colunas; evite `SELECT *`.
- Aproveite data skipping com [partição/cluster](../03-partitioning-clustering/README.md).
- Prefira carga batch (append/merge) a updates pontuais.
- Use tipos adequados; dimensões largas são ok no colunar.

## Relação com outros conceitos

- Conceito base: [row vs columnar](../../08-data-formats/08-row-vs-columnar/README.md),
  [Parquet](../../08-data-formats/04-parquet/README.md), [compressão](../../08-data-formats/09-compression/README.md).
- [Partitioning/clustering](../03-partitioning-clustering/README.md),
  [query optimization](../04-query-optimization/README.md).

## Exercícios

1. Compare o custo (bytes lidos) de `SELECT *` vs `SELECT col1, col2` numa tabela larga.
2. Explique como min/max por bloco permite data skipping num filtro de faixa.
3. Justifique por que uma dimensão larga e desnormalizada não penaliza queries que usam poucas
   colunas.
4. Explique por que muitos updates pontuais são caros num warehouse colunar.

## Referências

- Documentação de armazenamento de BigQuery (Capacitor), Snowflake (micro-partitions),
  Redshift (zone maps).
- Kleppmann, M. *DDIA* — cap. 3.
