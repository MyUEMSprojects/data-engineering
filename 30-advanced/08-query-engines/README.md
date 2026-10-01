# Query engines (Trino/Presto)

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: ferramenta/arquitetura*

## O que é

**Query engines** (motores de consulta) executam **SQL distribuído** sobre dados **sem serem donos do
armazenamento** — separam **computação** de **storage**. **Trino** (e seu antecessor/irmão **Presto**) é o
mais conhecido: um motor **MPP** de SQL interativo que consulta **lakes/lakehouses** (S3, HDFS, Iceberg,
Delta, Hive) e **múltiplas fontes** (Postgres, MySQL, Kafka, MongoDB, Elasticsearch...) **numa única
consulta (federação)**.

> Histórico: **Presto** nasceu no Facebook (2012). Um grupo dos criadores forkou em 2019 (PrestoSQL), que
> hoje é **Trino** (nome desde 2020). **PrestoDB** continua como projeto separado (Linux Foundation). São
> **parecidos mas divergentes** — confira qual você usa.

## Por que existem

- **SQL interativo sobre o lake** sem carregar dados num warehouse (arquitetura **lakehouse** — ver
  [lakehouse](../../15-lakehouse/README.md)).
- **Federação**: juntar dados de **várias fontes** sem ETL (ad hoc/exploração).
- **Desacoplamento**: o dado fica em **formatos abertos** ([Parquet/ORC](../../08-data-formats/04-parquet/README.md),
  [Iceberg/Delta](../../15-lakehouse/README.md)); vários motores leem o mesmo dado.
- **Escala elástica** de compute, latência de segundos (vs minutos de Spark/Hive).

## Arquitetura (Trino)

```text
Cliente (CLI/JDBC/BI) ─► Coordinator (parse, otimiza, planeja, agenda)
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
              Worker 1     Worker 2     Worker N      ← executam fragmentos do plano em paralelo, em memória, via pipelines
                 │            │            │
              Conectores ─► Hive/Iceberg/Delta (S3) · Postgres · Kafka · MongoDB · ...
```

- **Coordinator** — recebe a query, **otimiza** (CBO), divide em **estágios/fragmentos**, agenda splits.
- **Workers** — processam **splits** de dados em paralelo; trocam dados entre estágios por **exchange**
  (shuffle) em memória/rede ([shuffle](../../16-distributed-processing/03-partitioning-shuffle/README.md)).
- **Conectores (connectors)** — *plugins* que expõem cada fonte como **catalog.schema.table**; definem
  metadados, splits e leitura (com **pushdown** de predicados/projeções/agregações quando suportado).
- Execução **pipelinada e em memória** (sem gravar intermediários em disco por padrão) → baixa latência;
  por isso **não é feito para jobs ETL gigantes tolerantes a falha** (v. FTE abaixo).

## Catálogos e SQL

```sql
-- catálogo.esquema.tabela
SELECT c.uf, sum(p.valor) AS receita
FROM iceberg.vendas.pedidos p                    -- lakehouse (Iceberg em S3)
JOIN postgresql.crm.clientes c ON c.id = p.cliente_id   -- Postgres operacional (federado)
WHERE p.dt >= DATE '2024-01-01'
GROUP BY c.uf;
```
ANSI SQL com extensões; suporta window functions, CTEs, funções JSON/array, `MERGE`/`UPDATE`/`DELETE` em
tabelas lakehouse (Iceberg/Delta) conforme conector/versão.

## Otimização

- **Predicate/projection pushdown** e **partition pruning** (Hive/Iceberg) — leia só o necessário
  ([Parquet](../../08-data-formats/04-parquet/README.md)).
- **Cost-based optimizer** — depende de **estatísticas** (`ANALYZE`); escolhe ordem de join e estratégia
  (**broadcast** vs **partitioned/shuffle join** — [joins distribuídos](../../16-distributed-processing/04-distributed-joins-skew/README.md)).
- **Dynamic filtering** — usa o lado pequeno do join para filtrar o lado grande em runtime.
- **Skew/spill**: configurar memória por query/nó; **spill to disk** opcional; **resource groups** para
  isolar cargas.
- **Fault-tolerant execution (FTE)** (Trino): persiste intermediários (retries de tarefas/queries) para
  **queries longas/ETL** mais resilientes, ao custo de desempenho.
- Formatos colunares + tamanho de arquivo adequado ([small files](../../14-data-lake/06-small-files-compaction/README.md)).

## Trino vs outros motores

| Motor | Perfil | Quando |
| --- | --- | --- |
| **Trino/Presto** | **SQL interativo/federado**, MPP em memória, sem storage próprio | exploração/BI no lake, **federação**, lakehouse multi-motor |
| **Spark SQL** | batch **ETL** pesado, tolerante a falhas, ML, ecossistema | transformações grandes/complexas ([Spark](../../16-distributed-processing/README.md)) |
| **Hive/Tez** | batch legado sobre Hadoop | legado |
| **Athena** | **Trino/Presto gerenciado** (serverless, AWS) | SQL no S3 sem operar cluster |
| **Starburst / Dremio** | distribuições/plataformas comerciais (Trino/Arrow) | suporte, governança, aceleração |
| **DuckDB** | **single-node** analítico embutido | dados que cabem numa máquina; dev/CI |
| **BigQuery/Snowflake** | warehouses gerenciados com storage próprio | analytics gerenciado ([warehouse](../../13-data-warehouse/README.md)) |
| **ClickHouse/Pinot/Druid** | OLAP em tempo real | baixa latência/alta concorrência ([real-time](../05-real-time-analytics/README.md)) |

## Casos de uso

- **Camada SQL do lakehouse** (Trino + Iceberg + catálogo REST/Hive/Glue): vários usuários, vários motores.
- **Self-service/BI** sobre o lake (Superset/Looker/Tableau → Trino).
- **Federação ad hoc** (cruzar OLTP + lake sem ETL) e **migração/validação** entre sistemas.
- **Data virtualization** ([data fabric](../04-data-fabric/README.md)).
- **Substituir Hive** em ambientes Hadoop legados.

## Limitações / trade-offs

- **Federação** é conveniente, mas **performance e carga** dependem da fonte (cuidado ao bater em OLTP de
  produção); joins grandes entre sistemas são lentos — materialize o recorrente.
- **Não é ETL pesado ideal** por padrão (memória/sem intermediários persistidos; use FTE ou Spark).
- **Concorrência alta** exige dimensionamento/resource groups; gestão de memória por query.
- Dependência de **metastore/catálogo** e estatísticas.
- Operação de cluster (ou usar Athena/Starburst Galaxy).
- Diferenças entre **Trino × PrestoDB × Athena** (funções, conectores, versões).

## Segurança e governança

Autenticação (OAuth2/LDAP/Kerberos/OIDC), **autorização** por catálogo/tabela/coluna, **row filters/
column masks** (conforme conector/Ranger/OPA), TLS; **credenciais por usuário/impersonation** para as fontes;
auditoria via event listeners ([acesso](../../25-data-governance/05-access-control-classification/README.md),
[IAM](../../26-security/02-iam/README.md)).

## Erros comuns

- Federar consultas pesadas contra bancos de produção (impacto operacional).
- Sem estatísticas (`ANALYZE`) → planos ruins; small files/colunar mal organizado.
- Usar Trino como motor de ETL massivo sem FTE (queries longas falhando).
- Não limitar memória/concorrência (um usuário derruba o cluster) — sem resource groups.
- Confundir Trino com Presto/Athena (comportamentos diferentes).
- Expor o cluster sem autenticação/autorização.

## Boas práticas

- Dados em **Parquet/Iceberg** bem particionados e com estatísticas; catálogo confiável.
- **Materialize** (dbt/Spark) o que é recorrente; use federação para exploração.
- Resource groups, limites de memória, fila por perfil de uso; observabilidade (query logs, UI).
- Pushdown-friendly (filtros simples, evitar funções que impedem pushdown).
- Prefira gerenciado (Athena/Starburst Galaxy) se o time for pequeno.

## Relação com outros conceitos

- [Lakehouse](../../15-lakehouse/README.md), [Iceberg](../../15-lakehouse/05-apache-iceberg/README.md),
  [Spark](../../16-distributed-processing/README.md), [joins distribuídos](../../16-distributed-processing/04-distributed-joins-skew/README.md),
  [data fabric](../04-data-fabric/README.md), [warehouse](../../13-data-warehouse/README.md).

## Exercícios

1. Escreva uma consulta federada Iceberg (S3) + Postgres no Trino e descreva o plano distribuído.
2. Explique pushdown e dynamic filtering e como reduzem I/O num join fato×dimensão.
3. Quando você escolheria Trino, Spark SQL ou DuckDB para uma transformação? Justifique.
4. Configure (conceitualmente) resource groups para isolar BI interativo de queries de ETL.

## Referências

- Documentação do Trino (trino.io); Sethi et al., "Presto: SQL on Everything" (ICDE 2019);
  docs de AWS Athena, Starburst; Iceberg/Delta connectors.
