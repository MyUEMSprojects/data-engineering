# Transformação

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

A transformação é o "T" do ETL/ELT: converter dados **brutos** em dados **úteis, limpos e
modelados** para consumo. É onde reside a maior parte da lógica de negócio de um pipeline —
limpeza, padronização, junção, agregação e [modelagem](../../07-data-modeling/README.md).

## Tipos de transformação

| Categoria | Exemplos |
| --- | --- |
| **Limpeza** | remover nulos/duplicatas, corrigir tipos, padronizar texto/datas |
| **Padronização** | UFs maiúsculas, moeda única, timezone UTC, trim de strings |
| **Enriquecimento** | juntar com dados de referência (lookup), geocoding |
| **Junção (join)** | combinar fontes/tabelas ([joins](../../05-sql/03-joins/README.md)) |
| **Agregação** | somas, médias, contagens por grupo |
| **Derivação** | colunas calculadas, categorização ([CASE](../../05-sql/01-select-filtering/README.md)) |
| **Modelagem** | fatos/dimensões, [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md) |
| **Deduplicação** | ver [dedupe](../09-deduplication/README.md) |

## Onde transformar

- **No warehouse com SQL/[dbt](../../28-dbt/README.md)** (ELT) — padrão moderno para
  analytics: declarativo, versionado, testável, escalável.
- **Em [Spark](../../16-distributed-processing/README.md)** — volumes muito grandes,
  lógica não-SQL, ML.
- **Em [Python/pandas/polars](../../04-python-for-data-engineering/11-pandas/README.md)** —
  dados pequenos/médios, lógica procedural, protótipos.

Ver [ETL vs ELT](../01-etl-vs-elt/README.md) para a decisão.

## Camadas de transformação (medallion)

Transformações são encadeadas em camadas de refino progressivo (ver
[medallion](../../14-data-lake/03-medallion-architecture/README.md)):

```text
raw/bronze (como chegou) ─► staging/silver (limpo, tipado, deduplicado) ─► marts/gold (modelado, agregado)
```

Cada camada tem uma responsabilidade clara (*separation of concerns*): não misture limpeza
com modelagem de negócio no mesmo passo.

## Princípios de transformação robusta

### 1. Funções puras e testáveis

Separe a **lógica** (entra dado, sai dado) do **I/O** (ler/gravar). Isso torna a
transformação [testável](../../04-python-for-data-engineering/09-testing-python/README.md)
sem banco/arquivo e reutilizável (ver
[organização de projetos](../../03-git-software-engineering/07-project-organization/README.md)).

### 2. Idempotência

Rodar a transformação duas vezes deve dar o mesmo resultado (ver
[idempotência](../07-idempotency-retries/README.md)) — crucial para reprocessar/backfill.

### 3. Determinismo

Evite não-determinismo (ordem aleatória, `now()` embutido sem controle) que torna o
resultado irreprodutível.

### 4. Preserve o bruto

Transforme a partir da camada raw (imutável); nunca transforme destrutivamente a fonte.

## Exemplo (SQL/dbt style, em CTEs)

```sql
with source as (
    select * from {{ ref('stg_pedidos') }}   -- staging limpo
),
limpo as (
    select
        id,
        lower(trim(email))            as email,
        cast(valor as numeric(12,2))  as valor,
        (created_at at time zone 'UTC')::date as dia
    from source
    where id is not null               -- descarta inválidos
),
dedup as (
    select *, row_number() over (partition by id order by updated_at desc) as rn
    from limpo
)
select * from dedup where rn = 1       -- mantém a versão mais recente
```

## Exemplo (polars)

```python
import polars as pl
out = (
    pl.scan_parquet("raw/pedidos/*.parquet")
      .filter(pl.col("id").is_not_null())
      .with_columns(
          pl.col("email").str.strip_chars().str.to_lowercase(),
          pl.col("valor").cast(pl.Float64),
      )
      .unique(subset=["id"], keep="last")
      .collect()
)
```

## Qualidade na transformação

A transformação é o ponto natural para **validar** (ver
[data validation](../10-data-validation/README.md)): rejeitar/segregar linhas inválidas,
checar contagens, aplicar [data quality](../../12-data-quality/README.md) e
[testes](../../28-dbt/05-tests/README.md). Decida a política: **falhar** o pipeline ou
**quarentenar** os registros ruins (ver [tratamento de falhas](../11-handling-failures/README.md)).

## Erros comuns

- Misturar I/O com lógica → impossível testar.
- Transformações não-idempotentes/não-determinísticas → backfill duplica/varia.
- Pular validação → dados ruins propagam silenciosamente.
- Fazer tudo num passo gigante em vez de camadas claras.
- Transformar na fonte OLTP (impacta produção) em vez do raw.

## Boas práticas

- Camadas claras (raw → staging → marts); funções puras.
- Idempotente e determinística; preserve o bruto.
- Valide na transformação; documente a lógica de negócio.
- Prefira SQL/dbt para analytics; Spark/Python quando fizer sentido.

## Relação com outros conceitos

- Modelagem: [dimensional](../../07-data-modeling/04-dimensional-modeling/README.md),
  [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md).
- Ferramentas: [dbt](../../28-dbt/README.md), [Spark](../../16-distributed-processing/README.md),
  [polars](../../04-python-for-data-engineering/12-polars/README.md).
- [Dedupe](../09-deduplication/README.md), [validação](../10-data-validation/README.md),
  [idempotência](../07-idempotency-retries/README.md).

## Exercícios

1. Escreva uma transformação (SQL ou polars) que limpa, deduplica e padroniza um dataset de
   pedidos, em camadas.
2. Refatore uma transformação acoplada ao I/O separando a lógica pura e teste-a.
3. Mostre por que `now()` embutido numa transformação atrapalha reprocessamento e como
   parametrizar a data.
4. Adicione uma etapa de validação que quarentena linhas com `valor` negativo.

## Referências

- Reis & Housley, *Fundamentals of Data Engineering* — transformação.
- Documentação do dbt (modelos e testes); Polars/Spark.
