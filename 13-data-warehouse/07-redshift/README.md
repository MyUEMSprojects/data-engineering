# Redshift

> 🔵 Analytics Platforms · Parte de [13 — Data Warehouse](../README.md)

## O que é

**Amazon Redshift** é o data warehouse da AWS. Foi um dos pioneiros dos warehouses colunares MPP
na nuvem. Diferente do [BigQuery](../05-bigquery/README.md) (serverless) e, em parte, do
[Snowflake](../06-snowflake/README.md), o Redshift clássico expõe mais do **cluster** (nós,
distribuição, sort keys), exigindo mais *tuning* — embora versões recentes (RA3 e **Redshift
Serverless**) tenham modernizado isso.

## Arquitetura

```text
Leader node (coordena, planeja) ──► Compute nodes ──► slices (unidades de paralelismo)
```

- **Leader node** — recebe a query, planeja e distribui.
- **Compute nodes** — processam em paralelo (MPP); divididos em **slices**.
- **RA3** — nós com **managed storage** que separa storage (em S3) de compute (aproximando-se do
  modelo moderno); **Redshift Serverless** remove o gerenciamento de cluster.

## Os três "keys" que definem a performance

No Redshift clássico, você **projeta** a distribuição física — é o que mais afeta performance:

### Distribution style (como as linhas se espalham pelos nós)

- `KEY` — por uma coluna (co-localiza linhas da mesma chave → joins sem mover dados).
- `ALL` — replica a tabela em **todos** os nós (para dimensões pequenas → evita shuffle no join,
  como um broadcast).
- `EVEN` — distribui uniformemente (sem chave de join clara).
- `AUTO` — o Redshift escolhe.

Escolher a dist key certa **co-localiza** os dados que serão juntados, evitando o **shuffle**
(`DS_DIST_*`) — o maior custo em joins MPP (ver
[distributed joins/skew](../../16-distributed-processing/04-distributed-joins-skew/README.md)).

### Sort keys (ordenação física → data skipping)

Ordenam os dados em disco; com **zone maps** (min/max por bloco de 1 MB), permitem pular blocos em
filtros (ver [partitioning/clustering](../03-partitioning-clustering/README.md)). `COMPOUND` (prefixo)
ou `INTERLEAVED` (vários filtros igualmente).

### (Compression) encoding por coluna

Redshift aplica encodings de compressão por coluna (`AZ64`, `ZSTD`...); `COPY` com `COMPUPDATE`
pode escolher automaticamente.

## Carga de dados

```sql
COPY fct_vendas FROM 's3://bucket/dados/'
IAM_ROLE 'arn:aws:iam::...:role/redshift'
FORMAT AS PARQUET;
```

`COPY` a partir do [S3](../../19-cloud/02-object-storage/README.md) é o carregador em massa
(paraleliza entre slices). Evite `INSERT` linha a linha.

## Recursos úteis

- **Redshift Spectrum** — consultar [Parquet](../../08-data-formats/04-parquet/README.md) no S3
  sem carregar (ponte com [data lake](../../14-data-lake/README.md)).
- **RA3 managed storage** / **Serverless** — menos gestão de cluster.
- **Concurrency scaling** — adiciona capacidade temporária sob pico de concorrência.
- **Materialized views**, **workload management (WLM)** para priorizar cargas.
- Integra com [dbt](../../28-dbt/README.md) e o ecossistema AWS.

## Manutenção (mais que nos outros)

- **VACUUM** — recupera espaço e reordena após deletes/updates (tabelas "incham"); versões recentes
  automatizam mais.
- **ANALYZE** — atualiza estatísticas para o planejador.
- Monitorar **skew** de distribuição e *spilling* via tabelas de sistema (svl/stl/svv).

## Boas práticas específicas

- Escolha **dist key** pela chave de join mais comum; `ALL` para dimensões pequenas.
- **Sort key** pela coluna de filtro frequente (muitas vezes a data).
- `COPY` do S3 (Parquet) para carga; evite inserts pontuais.
- Rode VACUUM/ANALYZE (ou confie no automático) e monitore skew/spilling.
- Considere RA3/Serverless para reduzir gestão de infra.

## Trade-offs

- **Mais tuning** que BigQuery/Snowflake (dist/sort keys, vacuum) no modo clássico — poder e
  responsabilidade.
- Forte integração AWS (vantagem se você já é AWS; *lock-in* caso contrário).
- RA3/Serverless aproximam da experiência moderna, reduzindo essa carga.

## Quando usar

Faz muito sentido se a organização **já é AWS** e quer integração nativa (S3, IAM, Glue). O modo
clássico recompensa quem domina o tuning MPP; Serverless/RA3 para quem quer menos gestão.

## Erros comuns

- Dist key ruim → shuffle/skew em joins.
- Sort key ausente → sem data skipping.
- `INSERT` linha a linha em vez de `COPY`.
- Esquecer VACUUM/ANALYZE (modo clássico) → lentidão e planos ruins.

## Relação com outros conceitos

- Implementa [arquitetura MPP](../01-concepts-architecture/README.md),
  [columnar](../02-columnar-storage/README.md),
  [partition/cluster via dist/sort keys](../03-partitioning-clustering/README.md).
- Comparar com [BigQuery](../05-bigquery/README.md), [Snowflake](../06-snowflake/README.md).
- AWS: [cloud/AWS](../../19-cloud/09-aws/README.md); Spectrum ⇄ [lake](../../14-data-lake/README.md).

## Exercícios

1. Escolha dist e sort keys para uma tabela de fatos que junta com uma dimensão pequena e filtra
   por data; justifique.
2. Carregue Parquet do S3 com `COPY` e explique por que é melhor que inserts.
3. Use `EXPLAIN` para identificar um `DS_DIST_INNER` (shuffle) e proponha mudar a dist key.
4. Explique quando migrar do Redshift clássico para RA3/Serverless.

## Referências

- Documentação oficial do Amazon Redshift (docs.aws.amazon.com/redshift).
