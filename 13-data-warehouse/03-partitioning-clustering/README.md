# Partitioning e clustering

> 🔵 Analytics Platforms · Parte de [13 — Data Warehouse](../README.md)

## O que é

Duas técnicas para organizar fisicamente os dados no warehouse e permitir **data skipping** —
ler apenas os dados relevantes para a query:

- **Particionamento** — divide a tabela em segmentos por uma coluna (geralmente **data**), de
  modo que filtros por essa coluna leiam só as partições necessárias (*partition pruning*).
- **Clustering** (ou *sort keys*) — ordena/agrupa os dados **dentro** das partições por colunas
  frequentemente filtradas, melhorando o skipping por bloco.

São o equivalente dos [índices](../../05-sql/07-indexes/README.md) no mundo colunar: não há
B-tree, mas sim organização física + estatísticas.

## Por que importa (custo e performance)

Em warehouses, ler menos dados = **mais rápido e mais barato** (sobretudo na cobrança por bytes
do BigQuery). Particionar e clusterizar bem pode reduzir o custo de uma query de "varrer a tabela
toda" para "ler só o dia de interesse". É a alavanca nº 1 de otimização de warehouse.

## Particionamento

### Por data (o padrão)

```sql
-- BigQuery
CREATE TABLE fct_vendas (dt DATE, uf STRING, valor NUMERIC)
PARTITION BY dt;
-- query que filtra por dt lê SÓ aquela partição
SELECT SUM(valor) FROM fct_vendas WHERE dt = '2024-01-15';   -- partition pruning
```

Benefícios:

- **Partition pruning** — filtros por data leem só as partições certas.
- **Retenção/overwrite por partição** — descartar ou reprocessar um período é um drop/overwrite
  de partição (ver [loading](../../09-etl-elt/04-loading/README.md),
  [idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- Alinha-se ao padrão de carga incremental ([incremental](../../09-etl-elt/05-full-vs-incremental/README.md)).

### Cuidado: over/under-partitioning

- **Partições grandes demais** (ex.: por ano) → pruning fraco (lê demais).
- **Partições pequenas demais** (ex.: por minuto) → muitas partições minúsculas, overhead de
  metadados e o [small files problem](../../14-data-lake/06-small-files-compaction/README.md). Em
  BigQuery há limite de partições por tabela.
- Granularidade **diária** é o equilíbrio usual.

## Clustering / sort keys

Dentro das partições (ou da tabela), ordenar por colunas de filtro frequente co-localiza dados
semelhantes, melhorando o data skipping por bloco (min/max mais "apertados").

```sql
-- BigQuery: partição por data + clustering por uf e produto
CREATE TABLE fct_vendas (...)
PARTITION BY dt
CLUSTER BY uf, produto_id;
```

- **BigQuery** — `CLUSTER BY` (até 4 colunas; ordem importa — mais seletiva/usada primeiro).
- **Snowflake** — *clustering keys* (reorganizam micro-partitions; há *auto-clustering*).
- **Redshift** — *sort keys* (compound/interleaved) + *distribution keys* (ver abaixo).

## Distribution (específico de MPP como Redshift)

Em warehouses MPP com nós fixos (Redshift), a **distribution key** define como as linhas são
espalhadas entre os nós — crucial para **joins** (co-localizar as linhas que serão juntadas evita
mover dados entre nós, o *shuffle*). Opções: `KEY` (por coluna), `ALL` (replica tabela pequena a
todos os nós — como um broadcast), `EVEN`. Escolher mal causa [skew](../../16-distributed-processing/04-distributed-joins-skew/README.md)
e shuffle caro. (BigQuery/Snowflake gerenciam isso automaticamente.)

## Como escolher as colunas

- **Particione** pela coluna de filtro temporal mais comum (quase sempre uma data) e que também
  serve à retenção/carga.
- **Clusterize/ordene** pelas colunas de filtro de igualdade/faixa mais frequentes depois da data
  (`uf`, `cliente_id`).
- **Distribua** (Redshift) pela chave de join mais comum para co-localizar.

## Verificando o efeito

Use o plano/perfil de query (ver [query optimization](../04-query-optimization/README.md)) e os
**bytes/partições lidos**: um bom particionamento mostra "leu 1 partição de 365", não "varreu a
tabela".

## Erros comuns

- Não particionar tabelas grandes → toda query varre tudo (lento/caro).
- Filtrar por uma coluna **não** particionada/clusterizada (sem skipping).
- Over-partitioning (partições minúsculas, estourar limites, small files).
- Distribution key ruim no Redshift → shuffle/skew em joins.
- Aplicar função sobre a coluna de partição no filtro (impede pruning): `WHERE DATE(ts)=...` em
  vez de filtrar a coluna de partição diretamente.

## Boas práticas

- Particione por data (granularidade diária típica); clusterize por colunas de filtro frequentes.
- No Redshift, escolha distribution/sort keys pensando nos joins e filtros.
- Filtre pela coluna de partição diretamente (sem funções) para ativar o pruning.
- Meça bytes/partições lidos; ajuste conforme as queries reais.

## Relação com outros conceitos

- Baseia-se em [columnar storage](../02-columnar-storage/README.md) e
  [particionamento em geral](../../06-databases/06-partitioning-sharding/README.md).
- Reduz custo em [query optimization](../04-query-optimization/README.md) e evita
  [shuffle/skew](../../16-distributed-processing/04-distributed-joins-skew/README.md).
- Similar ao [partitioning no lake](../../14-data-lake/05-partitioning/README.md).

## Exercícios

1. Particione uma tabela de vendas por dia e clusterize por UF; mostre o pruning num filtro de
   data.
2. Explique por que `WHERE DATE(ts) = '...'` pode impedir o partition pruning e como corrigir.
3. Escolha distribution e sort keys para uma tabela de fatos que junta com uma dimensão grande
   (Redshift).
4. Dê um exemplo de over-partitioning e seu problema.

## Referências

- Documentação de partição/clustering do BigQuery; clustering keys do Snowflake; dist/sort keys
  do Redshift.
- Kimball, R. *The Data Warehouse Toolkit* (aggregações/performance).
