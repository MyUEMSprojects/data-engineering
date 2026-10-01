# Databases gerenciados

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)

## O que é

Bancos de dados em que o provedor cuida de **provisionamento, patching, backups, replicação, failover e
monitoramento**, enquanto você cuida de **schema, queries, acesso e custo**. É [PaaS](../01-service-models/README.md)
aplicado a dados — quase sempre preferível a operar banco em VM própria.

## Categorias e equivalências

| Categoria | AWS | GCP | Azure |
| --- | --- | --- | --- |
| Relacional (OLTP) | RDS (Postgres/MySQL), Aurora | Cloud SQL, AlloyDB | Azure Database (Postgres/MySQL), SQL Database |
| Relacional distribuído | Aurora, DSQL | Spanner | Cosmos DB for PostgreSQL |
| Key-value / NoSQL | DynamoDB | Bigtable, Firestore | Cosmos DB (multi-API), Table Storage |
| Documento | DocumentDB | Firestore | Cosmos DB (Mongo API) |
| Cache | ElastiCache (Redis) | Memorystore | Azure Cache for Redis |
| Grafo | Neptune | — | Cosmos DB (Gremlin) |
| Data warehouse (OLAP) | Redshift | BigQuery | Synapse / Fabric |
| Streaming | MSK, Kinesis | Pub/Sub, Managed Kafka | Event Hubs |
| Busca | OpenSearch | — | Azure AI Search |

Ver os modelos em [databases](../../06-databases/README.md) e [NoSQL](../../06-databases/04-nosql/README.md).

## O que o provedor gerencia (e o que não)

**Gerencia**: instalação, patches, backups automáticos e PITR, réplicas de leitura, failover multi-AZ,
métricas, criptografia em repouso, escalonamento vertical assistido.

**Você ainda é responsável por**: modelagem/índices/queries, **permissões e rede**, parâmetros de tuning,
custos, janelas de manutenção, retenção de backup, testes de restauração ([DR](../../06-databases/09-backup-recovery-dr/README.md)),
e a **estratégia de extração** para analytics.

## Alta disponibilidade e escala

- **Multi-AZ** — réplica síncrona em outra zona, failover automático (HA). Não é escala de leitura.
- **Read replicas** — réplicas (assíncronas) para leitura/analytics e extração
  ([replicação](../../06-databases/07-replication/README.md), atenção ao lag).
- **Aurora/AlloyDB** — storage distribuído, failover rápido, até ~15 réplicas.
- **Spanner/Cosmos/DynamoDB** — escala horizontal global (consistência configurável — ver
  [CAP](../../01-foundations/05-distributed-systems-fundamentals/README.md)).
- **Serverless** (Aurora Serverless, DynamoDB on-demand) — escala conforme demanda.

## O ângulo do Data Engineer

- Bancos gerenciados são **fontes** OLTP: extraia de **réplicas** ou via **[CDC](../../09-etl-elt/06-cdc/README.md)**
  (habilite logical replication/binlog nos parâmetros), não do primário.
- **Snapshots/exports para S3/GCS** (ex.: RDS export em Parquet) facilitam cargas.
- Conexão: dentro de **VPC**, sem acesso público; segredos no [secret manager](../06-iam-secrets/README.md).
- Para analytics, use **warehouse/lakehouse**, não o OLTP.

## Custo

Instância (por hora, por tamanho), armazenamento provisionado/IOPS, backups além do incluído, tráfego
entre AZ/região, réplicas. NoSQL on-demand cobra por requisição (cuidado com hot keys/scans). Ver
[cost](../08-cost-management/README.md).

## Erros comuns

- Banco com IP público e senha fraca.
- Extrair analytics direto do primário.
- Sem teste de restauração; retenção de backup curta.
- Multi-AZ confundido com escala de leitura.
- Esquecer de habilitar parâmetros de CDC antes de precisar.
- Superdimensionar instância em vez de otimizar queries/índices.

## Boas práticas

- Multi-AZ para produção; réplicas para leitura/extração; backups + PITR testados.
- Rede privada, IAM/secret manager, criptografia (KMS), auditoria.
- Monitorar CPU/conexões/IOPS/lag/espaço; alertas.
- IaC para versionar a configuração ([IaC](../../22-infrastructure-as-code/README.md)).

## Relação com outros conceitos

- [Databases](../../06-databases/README.md), [CDC](../../09-etl-elt/06-cdc/README.md),
  [replicação](../../06-databases/07-replication/README.md), [warehouse](../../13-data-warehouse/README.md).
- [IAM/secrets](../06-iam-secrets/README.md), [networking](../05-networking/README.md).

## Exercícios

1. Mapeie, para um stack de dados, o serviço equivalente em AWS/GCP/Azure de: Postgres gerenciado, key-value, cache, warehouse.
2. Diferencie Multi-AZ de read replica.
3. Descreva como extrair de um RDS Postgres para o lake sem afetar a produção.

## Referências

- Documentação de RDS/Aurora, Cloud SQL/AlloyDB/Spanner, Azure Database/Cosmos DB.
