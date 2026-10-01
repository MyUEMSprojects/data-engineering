# Distributed databases

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: fundamento avançado*

## O que é

**Bancos de dados distribuídos** armazenam e processam dados **em múltiplos nós** (talvez em várias
regiões), apresentando-se como **um sistema lógico único**, com **escala horizontal**, **tolerância a
falhas** e, em alguns, **transações ACID distribuídas**. Aprofunda
[particionamento](../../06-databases/06-partitioning-sharding/README.md),
[replicação](../../06-databases/07-replication/README.md) e
[consistência](../../06-databases/08-concurrency-consistency/README.md), com o rigor de
[sistemas distribuídos](../../01-foundations/05-distributed-systems-fundamentals/README.md).

## Por que existem

Um relacional single-node (Postgres/MySQL) escala **verticalmente** e por **réplicas de leitura**, mas tem
**teto de escrita**, **ponto único de falha de região** e sharding manual doloroso. Aplicações globais/de
altíssima escala precisam de **escrita escalável, HA multi-região e consistência forte** — o que motivou
duas famílias: **NoSQL distribuído** (consistência mais relaxada) e **NewSQL**.

## As famílias

| Família | Modelo | Consistência | Exemplos |
| --- | --- | --- | --- |
| **NoSQL distribuído (Dynamo-style)** | key-value/wide-column, **leaderless**, quorum | **ajustável/eventual** (AP) | Cassandra, ScyllaDB, DynamoDB (opção forte), Riak |
| **NewSQL** | **SQL + ACID distribuído**, escala horizontal | **forte** (serializable/linearizável por transação) | **Google Spanner**, **CockroachDB**, **YugabyteDB**, TiDB, AlloyDB/Aurora DSQL (distintos) |
| **Sharded relacional** | relacional + sharding gerenciado | por shard; cross-shard limitado | Vitess (MySQL), Citus (Postgres) |
| **Multi-modelo global** | vários modelos, replicação global | níveis configuráveis | Cosmos DB (5 níveis) |
| **Documento distribuído** | documentos, sharding+replica sets | configurável | MongoDB |

Em **analytics**, engines MPP distribuídas ([warehouses](../../13-data-warehouse/README.md),
[Spark](../../16-distributed-processing/README.md), Pinot/ClickHouse) são outra categoria "distribuída",
focada em OLAP.

## Os problemas fundamentais (e as soluções)

### 1. Particionamento (sharding)
Dividir os dados por **chave** (hash/range) entre nós; **rebalanceamento** ao crescer (consistent hashing,
*ranges* dinâmicos que se dividem/mesclam — Spanner/Cockroach); **hot spots**
([partitioning](../../06-databases/06-partitioning-sharding/README.md)).

### 2. Replicação e consenso
Cada partição é replicada em N nós; **consenso (Paxos/Raft)** elege líder e **ordena as escritas** com
maioria (quorum), tolerando falhas sem perder dados confirmados. Ex.: **Raft por range/tablet** em
Cockroach/Yugabyte/TiDB; **Paxos** no Spanner.

```text
escrita ─► líder do range ─► replica para a maioria (Raft/Paxos) ─► commit
falha do líder → nova eleição (poucos segundos) → continua
```

### 3. Transações distribuídas
Transação atingindo **várias partições** exige **atomicidade** entre nós: **two-phase commit (2PC)**
(coordenador + participantes; custo e risco de bloqueio) combinado com consenso para o coordenador
tolerar falhas. Estratégias de isolamento: **MVCC distribuído**, locks, ou **timestamps globais**.

### 4. Tempo e ordenação
Ordenar eventos entre nós sem relógio global confiável:

- **Relógios lógicos/híbridos (HLC)** — CockroachDB/Yugabyte (com limites de *clock skew*).
- **TrueTime** (Spanner): relógios atômicos/GPS com **incerteza limitada** → *commit wait* garante
  **consistência externa (linearizabilidade global)**. Recurso exclusivo de infraestrutura Google.
- Daí: Spanner/Cockroach oferecem **serializabilidade** com custos de **latência** (coordenação cross-
  região).

### 5. Consistência vs disponibilidade vs latência
Sob **partição de rede**: **CP** (recusa para manter consistência — Spanner, Cockroach, etcd) vs **AP**
(responde com dado possivelmente antigo — Cassandra/Dynamo). **PACELC**: mesmo sem partição, há trade-off
**latência × consistência** (replicação síncrona entre regiões custa dezenas–centenas de ms)
([CAP/PACELC](../../01-foundations/05-distributed-systems-fundamentals/README.md),
[consistência](../../06-databases/08-concurrency-consistency/README.md)).

## Modelos de consistência na prática

- **Linearizable/serializable** (NewSQL): comporta-se como **uma cópia**; ideal para finanças/inventário;
  custo de latência.
- **Eventual/tunable** (Cassandra/Dynamo): `W + R > N` para leitura forte opcional; **conflitos** resolvidos
  por *last-write-wins*, vector clocks, CRDTs.
- **Read-your-writes / sessão / causal** (Cosmos, Mongo): níveis intermediários.
- **Leituras com defasagem limitada (bounded staleness / follower reads)**: aceitar dado ligeiramente antigo
  para **baixa latência local**.

## Geodistribuição

- **Placement/localidade de dados** (por região/usuário): reduz latência e atende **residência de dados**
  (LGPD/GDPR — [compliance](../../25-data-governance/07-compliance-privacy/README.md)).
- **Multi-região ativo-ativo** exige tratar conflitos e latência de consenso; **ativo-passivo** simplifica.
- **Quorums** dimensionados para sobreviver à perda de uma região/zona.

## Quando usar / quando NÃO usar

- **Considere** quando precisa de **escrita escalável além de um nó**, **HA multi-região**, **consistência
  forte global**, ou **sharding manual** virou dor operacional.
- **Evite** se um **Postgres/MySQL bem dimensionado + réplicas** atende (a maioria dos casos): bancos
  distribuídos trazem **latência maior por escrita**, **complexidade operacional** e **custo**. "Distribuído"
  não é upgrade grátis.
- Para **analytics**, use warehouse/lakehouse — não um NewSQL OLTP.

## O ângulo do Data Engineer

- Como **fontes**: entender garantias para extrair com **consistência** (snapshots/timestamps), usar
  **CDC** do banco distribuído (Cockroach changefeeds, Spanner Change Streams, Cassandra CDC, DynamoDB
  Streams — [CDC](../01-cdc-debezium/README.md)) e lidar com **eventual consistency** na origem
  ([consistência](../../06-databases/08-concurrency-consistency/README.md)).
- **Modelagem de chaves** para evitar hot partitions ([sharding](../../06-databases/06-partitioning-sharding/README.md)).
- Ferramentas de **exportação** (BigQuery/Spanner federation, backups para S3/Parquet) para analytics.
- **Idempotência** nos pipelines frente a reentregas e leituras de réplicas defasadas.

## Erros comuns

- Adotar banco distribuído sem necessidade real (complexidade/latência/custo).
- Modelar chaves sequenciais (hot spot no range final) ou ignorar distribuição de acesso.
- Esperar latência de single-node em transações cross-região.
- Confundir "escala horizontal" com "consistência/transações grátis".
- Ignorar clock skew (em sistemas baseados em HLC) e a necessidade de NTP/relógios saudáveis.
- Usar NewSQL OLTP como motor analítico.
- Não planejar backup/restore/DR multi-região ([DR](../../06-databases/09-backup-recovery-dr/README.md)).

## Boas práticas

- Escolha a **garantia de consistência** pelo requisito de negócio, não pelo máximo.
- Projete chaves (e *interleaving*/co-localização) para **transações locais a uma partição**.
- Use **follower reads/bounded staleness** quando aceitável; defina localidade/residência de dados.
- Teste falhas (partições, perda de zona/região) e meça latência real de commit.
- Para dados analíticos, replique/exporte para o lake/warehouse.

## Relação com outros conceitos

- [Sistemas distribuídos/CAP](../../01-foundations/05-distributed-systems-fundamentals/README.md),
  [sharding](../../06-databases/06-partitioning-sharding/README.md), [replicação](../../06-databases/07-replication/README.md),
  [consistência](../../06-databases/08-concurrency-consistency/README.md), [NoSQL](../../06-databases/04-nosql/README.md),
  [managed DBs](../../19-cloud/04-managed-databases/README.md).

## Exercícios

1. Explique como Raft/Paxos mantém uma escrita durável com a queda do líder.
2. Compare Spanner/CockroachDB (NewSQL) e Cassandra (Dynamo-style) em consistência, latência e modelo.
3. Por que uma transação cross-região é cara? Cite 2PC, consenso e latência de rede.
4. Projete a chave primária de uma tabela de eventos para evitar hot spot num range-sharded DB.

## Referências

- Corbett et al., "Spanner" (OSDI 2012); Ongaro & Ousterhout, "Raft" (2014); DeCandia et al., "Dynamo" (2007);
  Taft et al., "CockroachDB" (SIGMOD 2020); Kleppmann, *DDIA* (caps. 5–9); documentação de Cockroach/Yugabyte/TiDB/Cassandra.
