# Conceitos e arquitetura

> 🔵 Analytics Platforms · Parte de [13 — Data Warehouse](../README.md)

## O que é

Um **data warehouse** é um repositório central, integrado e orientado a assuntos, que armazena
dados históricos de várias fontes, **modelados** e otimizados para análise
([OLAP](../../01-foundations/07-oltp-vs-olap/README.md)). Diferente de um banco operacional, ele
é feito para **ler e agregar muito**, não para transações pontuais.

A definição clássica de Inmon: um warehouse é *subject-oriented, integrated, time-variant e
non-volatile* — organizado por assunto de negócio, integrando várias fontes, guardando histórico
e sem sofrer updates transacionais constantes.

## Por que existe

Rodar analytics direto nos bancos OLTP de produção é inviável (sobrecarrega a operação e os
dados estão normalizados/espalhados). O warehouse resolve: centraliza, integra, modela
([dimensional](../../07-data-modeling/04-dimensional-modeling/README.md)) e otimiza para
consultas analíticas — dando uma **fonte única de verdade** para BI e análise.

## Características arquiteturais

### Armazenamento colunar

Dados guardados por coluna (ver [columnar storage](../02-columnar-storage/README.md)) → lê só as
colunas da query, comprime muito, acelera agregações. É a base da performance analítica.

### MPP (Massively Parallel Processing)

Warehouses modernos distribuem dados e processamento por **muitos nós** que trabalham em
paralelo (ver [sistemas distribuídos](../../01-foundations/05-distributed-systems-fundamentals/README.md)).
Uma query grande é dividida entre nós, cada um processando sua fatia → escala horizontal.

```text
query ─► coordenador ─► divide entre N nós ─► cada nó processa sua partição ─► combina
```

### Separação de storage e compute (a revolução cloud)

Warehouses tradicionais (on-prem) acoplavam disco e CPU no mesmo nó — escalar um exigia escalar
o outro. Os warehouses na nuvem (BigQuery, Snowflake, Redshift RA3) **separam**:

- **Storage** — dados em [object storage](../../19-cloud/02-object-storage/README.md) barato e
  "infinito".
- **Compute** — clusters/slots elásticos que lêem desse storage, escaláveis sob demanda e
  independentes.

Benefícios: escalar compute sem mexer no storage; múltiplos clusters lendo os mesmos dados sem
contenção; pagar compute só quando usa; storage barato. É o que viabilizou o
[ELT](../../09-etl-elt/01-etl-vs-elt/README.md) moderno.

```text
      ┌──────── compute (elástico) ────────┐
      │ cluster A   cluster B   cluster C   │   ← escala independente
      └──────────────┬─────────────────────┘
                     ▼
         storage (object storage, barato, compartilhado)
```

## Modelos de cobrança (importa muito)

- **Por consumo/bytes** (BigQuery on-demand) — paga pelos **bytes lidos** por query → reduzir
  dados lidos = reduzir conta (particionar/clusterizar, evitar `SELECT *`).
- **Por tempo de compute** (Snowflake *warehouses*, BigQuery slots, Redshift) — paga por nós/
  tempo ativo → desligar quando ocioso, dimensionar o cluster.

O modelo de cobrança molda as decisões de design — ver [cost](../../19-cloud/08-cost-management/README.md).

## Warehouse vs data lake vs lakehouse

| | Warehouse | [Data Lake](../../14-data-lake/README.md) | [Lakehouse](../../15-lakehouse/README.md) |
| --- | --- | --- | --- |
| Dados | modelados, estruturados | brutos, qualquer formato | ambos |
| Schema | on-write | on-read | on-write + flexível |
| Otimizado para | SQL analítico | storage barato/variado | SQL + ML sobre lake |
| Custo de storage | maior | menor | menor (object storage) |

Warehouses são a escolha para analytics SQL estruturado; lakes para dados brutos/variados; o
lakehouse tenta unir os dois.

## O que vive no warehouse

Tabelas modeladas: camadas staging e **marts** [dimensionais](../../07-data-modeling/05-star-schema/README.md)
(fatos e dimensões), construídas por [ELT/dbt](../../28-dbt/README.md), consumidas por BI,
análises e [features de ML](../../31-data-engineering-and-ml/README.md).

## Erros comuns

- Tratar o warehouse como OLTP (muitas escritas pontuais, índices B-tree — não é o modelo).
- `SELECT *` e falta de partição → custo/tempo altos (especialmente cobrança por bytes).
- Modelar como no OLTP (normalizado demais) em vez de dimensional.
- Deixar compute ligado ocioso (desperdício).

## Boas práticas

- Modele dimensionalmente; carregue via ELT/dbt.
- Particione/clusterize e selecione colunas para reduzir bytes/tempo.
- Aproveite a separação storage/compute (escale/suspenda compute conforme uso).
- Monitore custo por query/por time.

## Relação com outros conceitos

- [Columnar](../02-columnar-storage/README.md),
  [partitioning/clustering](../03-partitioning-clustering/README.md),
  [otimização](../04-query-optimization/README.md).
- Modelagem: [dimensional](../../07-data-modeling/04-dimensional-modeling/README.md); carga:
  [ELT/dbt](../../28-dbt/README.md).
- Implementações: [BigQuery](../05-bigquery/README.md),
  [Snowflake](../06-snowflake/README.md), [Redshift](../07-redshift/README.md).

## Exercícios

1. Explique a separação storage/compute e por que ela viabilizou o ELT moderno.
2. Descreva como uma query grande é processada num sistema MPP.
3. Dado um modelo de cobrança por bytes lidos, liste 3 decisões de design para reduzir custo.
4. Compare quando usar warehouse, lake e lakehouse.

## Referências

- Inmon, W. *Building the Data Warehouse*; Kimball, R. *The Data Warehouse Toolkit*.
- Documentação de arquitetura de BigQuery, Snowflake, Redshift.
