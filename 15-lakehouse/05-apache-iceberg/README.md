# Apache Iceberg

> 🔵 Analytics Platforms · Parte de [15 — Lakehouse](../README.md)

## O que é

**Apache Iceberg** é um *table format* open source (criado na Netflix, hoje Apache) para grandes
tabelas analíticas sobre [object storage](../../14-data-lake/02-object-storage/README.md).
Destaca-se pela **neutralidade de engine** (projetado desde o início para ser lido/escrito por
muitas engines — Spark, Flink, Trino, Dremio, e warehouses como BigQuery/Snowflake) e por resolver
problemas de escala e evolução que o particionamento Hive clássico tinha.

## Por que surgiu (os problemas do "Hive table")

O formato de tabela Hive (diretório + [metastore](../../14-data-lake/07-metadata/README.md) +
partições por diretório) tinha falhas em escala:

- Partições atreladas ao **layout de diretórios** → mudar o esquema de partição exige reescrever
  tudo; filtros dependem de o usuário conhecer as partições.
- **Listagem de diretórios** cara/eventualmente consistente para descobrir arquivos.
- Sem [ACID](../03-acid-on-object-storage/README.md) real, sem time travel.

Iceberg rastreia **os arquivos exatos** de cada versão em metadados próprios, desacoplando a tabela
do layout de diretórios.

## Como funciona: a hierarquia de metadados

```text
catalog ─► metadata.json (versão atual: schema, partition spec, snapshots)
             └─► manifest list (um snapshot) ─► manifest files ─► data files (Parquet/ORC/Avro)
                                                   (+ estatísticas por arquivo p/ pruning)
```

- **Snapshot** — uma versão imutável da tabela (lista exata de data files).
- **Commit** — via **catálogo**, com *compare-and-swap* atômico do ponteiro para o novo
  `metadata.json` → ACID (ver [ACID sobre object storage](../03-acid-on-object-storage/README.md)).
- O pruning usa estatísticas nos **manifests** (não depende de listar diretórios).

## Recursos que diferenciam

- **Hidden partitioning** — a tabela sabe particionar (ex.: por dia derivado de um timestamp) **sem**
  o usuário precisar filtrar pela coluna de partição explicitamente. `WHERE event_ts >= ...` já ativa
  o pruning (resolve a armadilha do Hive `WHERE DATE(ts)=...`).
- **Partition evolution** — mudar o esquema de partição **sem reescrever** dados antigos (ex.: de
  mensal para diário a partir de agora).
- **Schema evolution segura** — adicionar/renomear/reordenar colunas por **ID** (não por posição/
  nome), sem quebrar (ver [schema evolution](../../08-data-formats/10-schema-evolution/README.md)).
- **Time travel** e **branching/tagging** (Nessie/catálogos) — versões nomeadas, isolamento de
  experimentos.
- **Engine-neutro** — o maior diferencial: vários motores lêem/escrevem a mesma tabela.

## Exemplos (Spark SQL)

```sql
CREATE TABLE catalog.db.vendas (id bigint, uf string, valor double, event_ts timestamp)
USING iceberg PARTITIONED BY (days(event_ts));     -- hidden partitioning por dia

MERGE INTO catalog.db.vendas t USING updates s ON t.id = s.id
  WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *;

SELECT * FROM catalog.db.vendas FOR SYSTEM_VERSION AS OF 123;    -- time travel
CALL catalog.system.rewrite_data_files('db.vendas');            -- compaction
CALL catalog.system.expire_snapshots('db.vendas', TIMESTAMP '...');
```

## O catálogo é central

Iceberg depende de um **catálogo** para o commit atômico e para localizar a tabela: Hive Metastore,
AWS Glue, **REST catalog**, Nessie, JDBC, etc. A escolha do catálogo afeta concorrência e
interoperabilidade (o **REST catalog** padroniza isso e vem ganhando tração).

## Por que é a tendência

A **convergência** do mercado está em torno do Iceberg como **formato aberto comum**: Snowflake,
BigQuery, Databricks (via Uniform/compat), AWS, Trino e Flink suportam Iceberg. Isso significa
**um dado aberto, várias engines** — reduzindo lock-in (ver
[lake vs warehouse vs lakehouse](../02-lake-vs-warehouse-vs-lakehouse/README.md)).

## Trade-offs

- **Depende de catálogo** bem configurado (complexidade operacional).
- Ecossistema de ferramentas de manutenção ainda amadurecendo em alguns pontos vs Delta no
  Databricks.
- Como todo lakehouse, exige **compaction** e **expiração de snapshots** (manutenção).

## Quando usar

- Quer **neutralidade de engine** e evitar lock-in (vários motores sobre o mesmo dado).
- Tabelas **muito grandes** com evolução frequente de partição/schema.
- Está apostando na **convergência** (warehouses lendo Iceberg).

## Erros comuns

- Negligenciar o catálogo (afeta concorrência/atomicidade).
- Não rodar `rewrite_data_files` (small files) nem `expire_snapshots` (storage).
- Mexer nos arquivos "por fora" do Iceberg.
- Achar que hidden partitioning dispensa pensar na chave de partição (ainda importa).

## Boas práticas

- Escolha um catálogo adequado (REST catalog para interoperabilidade).
- Use hidden/partition evolution e schema evolution por ID.
- Agende compaction e expiração de snapshots.
- Prefira Iceberg quando a neutralidade de engine/convergência for prioridade.

## Relação com outros conceitos

- [ACID sobre object storage](../03-acid-on-object-storage/README.md),
  [metadata](../../14-data-lake/07-metadata/README.md),
  [schema evolution](../../08-data-formats/10-schema-evolution/README.md).
- Compara com [Delta](../04-delta-lake/README.md) e [Hudi](../06-apache-hudi/README.md);
  lido por [warehouses](../../13-data-warehouse/README.md) e [Spark](../../16-distributed-processing/README.md).

## Exercícios

1. Crie uma tabela Iceberg com hidden partitioning por dia e mostre o pruning sem filtrar a coluna
   de partição explicitamente.
2. Faça partition evolution (mensal → diário) e explique por que não reescreve o histórico.
3. Faça time travel para um snapshot anterior e rode `rewrite_data_files`.
4. Explique o papel do catálogo no commit atômico do Iceberg.

## Referências

- Documentação oficial do Apache Iceberg (iceberg.apache.org) — spec, catalogs, procedures.
