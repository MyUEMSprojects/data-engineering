# Motivação e arquitetura do Lakehouse

> 🔵 Analytics Platforms · Parte de [15 — Lakehouse](../README.md)

## O problema que motivou o lakehouse

Até ~2020, a arquitetura padrão usava **dois sistemas**:

```text
Fontes ─► Data Lake (bruto, barato, ML)  ──(ETL)──►  Data Warehouse (modelado, confiável, BI)
```

Isso tem custos reais:

- **Dados duplicados** — o mesmo dado no lake e no warehouse.
- **Pipelines a mais** — mover do lake para o warehouse (mais complexidade, mais defasagem).
- **Dois sistemas para governar/pagar/manter.**
- **Lake sem confiabilidade** — o [lake cru](../../14-data-lake/README.md) não tem
  [ACID](../03-acid-on-object-storage/README.md), updates, schema enforcement nem time travel
  (vira [data swamp](../../14-data-lake/01-concepts/README.md)).
- **Warehouse sem flexibilidade** — caro, ruim para dados não-estruturados/ML, e frequentemente
  *lock-in* de formato.

## A ideia do lakehouse

Trazer as **garantias do warehouse** (ACID, schema, SQL performático, time travel) **para dentro do
lake**, sobre [object storage](../../14-data-lake/02-object-storage/README.md) barato e
[formatos abertos](../../08-data-formats/04-parquet/README.md) — eliminando a separação. Um sistema
só serve BI, ML e dados brutos.

```text
Fontes ─► Lakehouse (object storage + table format)  ─►  BI + ML + SQL + streaming
          (bronze/silver/gold em Delta/Iceberg/Hudi)
```

## Como funciona: a camada de metadados transacional

O lakehouse **não** é um novo armazenamento — é uma **camada de tabela** (table format) sobre
arquivos Parquet no object storage. Essa camada adiciona um **log/manifesto transacional** que
define, de forma atômica e versionada, **quais arquivos** compõem a tabela.

```text
object storage:
  tabela/
  ├── _delta_log/ (ou metadata/)   ◄── o log transacional: define a versão N da tabela
  │   ├── 000.json  (commit 1)
  │   └── 001.json  (commit 2)
  └── part-*.parquet               ◄── os dados (arquivos Parquet)
```

- Cada **commit** é uma entrada no log que diz "a tabela agora é estes arquivos" — **atômico**
  (ACID — ver [ACID sobre object storage](../03-acid-on-object-storage/README.md)).
- O log + estatísticas por arquivo habilitam **data skipping**, **time travel** (ler uma versão
  antiga), **schema enforcement/evolution** e **updates/deletes/MERGE** (reescrevendo arquivos e
  commitando a nova versão).

Isso resolve exatamente as limitações do [metadado de lake cru](../../14-data-lake/07-metadata/README.md).

## Capacidades do lakehouse

| Capacidade | O que permite |
| --- | --- |
| **ACID** | commits atômicos, sem leituras de estado parcial |
| **Upserts/MERGE/DELETE** | atualizar/deletar linhas (SCD, CDC, GDPR/LGPD) sobre o lake |
| **Time travel** | consultar/restaurar versões anteriores (auditoria, DR) |
| **Schema enforcement + evolution** | barrar dado inválido e evoluir schema com segurança |
| **Data skipping** | estatísticas por arquivo (além de partições) |
| **Compaction (`OPTIMIZE`)** | resolver [small files](../../14-data-lake/06-small-files-compaction/README.md) com segurança |
| **Streaming + batch** | mesma tabela serve os dois |

## Arquitetura típica (medallion sobre lakehouse)

As camadas [medallion](../../14-data-lake/03-medallion-architecture/README.md) viram tabelas
transacionais:

```text
🥉 bronze (Delta/Iceberg)  ─►  🥈 silver  ─►  🥇 gold  ─►  BI / ML
   (ACID, schema, time travel em cada camada)
```

Engines: [Spark](../../16-distributed-processing/README.md), Flink, Trino, DuckDB e warehouses
(BigQuery/Snowflake já lêem Iceberg) consultam as mesmas tabelas — **formato aberto, múltiplas
engines**.

## Trade-offs honestos

- **Não substitui tudo**: para OLTP continua-se usando [bancos operacionais](../../06-databases/README.md);
  o lakehouse é analítico. Para cargas puramente SQL já bem servidas por um warehouse gerenciado,
  pode ser complexidade a mais.
- **Operação**: gerenciar table formats, compaction e metadados exige maturidade (os gerenciados —
  Databricks, etc. — reduzem isso).
- **Maturidade**: excelente e em rápida evolução, mas certos recursos variam entre formatos/engines.

## Erros comuns

- Achar que lakehouse é um produto específico (é um **padrão/table format**, não uma marca).
- Esperar que resolva OLTP (é analítico).
- Adotar a complexidade de table formats sem precisar (um warehouse simples pode bastar).
- Ignorar compaction/manutenção (table format não dispensa operação).

## Boas práticas

- Use lakehouse quando quer **um** sistema para BI+ML+streaming sobre o lake, com ACID e formatos
  abertos.
- Organize em [medallion](../../14-data-lake/03-medallion-architecture/README.md) com tabelas
  transacionais.
- Agende compaction/otimização; gerencie retenção de versões (time travel custa storage).
- Prefira formatos abertos ([Iceberg](../05-apache-iceberg/README.md)) para evitar lock-in de
  engine.

## Relação com outros conceitos

- Une [lake](../../14-data-lake/README.md) e [warehouse](../../13-data-warehouse/README.md) (ver
  [comparação](../02-lake-vs-warehouse-vs-lakehouse/README.md)).
- [ACID sobre object storage](../03-acid-on-object-storage/README.md);
  formatos: [Delta](../04-delta-lake/README.md), [Iceberg](../05-apache-iceberg/README.md),
  [Hudi](../06-apache-hudi/README.md).

## Exercícios

1. Liste 4 problemas da arquitetura "lake + warehouse" que o lakehouse resolve.
2. Explique como o log transacional define uma versão atômica da tabela.
3. Dê 3 casos de uso que exigem upserts/deletes sobre o lake (ex.: LGPD, CDC, SCD).
4. Dê um caso em que um warehouse simples é preferível ao lakehouse.

## Referências

- Armbrust et al. "Lakehouse" (CIDR 2021).
- Documentação de Delta Lake, Iceberg, Hudi.
