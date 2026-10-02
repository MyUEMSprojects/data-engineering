# 06 — Databases

> 🔵 Nível 2 — Core · Pré: [05 — SQL](../05-sql/README.md) ·
> Próximo: [07 — Data Modeling](../07-data-modeling/README.md)

Enquanto o módulo de [SQL](../05-sql/README.md) foca na **linguagem**, este foca nos
**sistemas**: como os bancos de dados funcionam por dentro (storage engines,
índices, concorrência), os diferentes **modelos** (relacional e NoSQL) e as
preocupações **operacionais** (replicação, sharding, backup, disaster recovery)
que o Data Engineer precisa dominar para escolher, operar e extrair dados.

## Por que importa

Você escolhe fontes e destinos de dados o tempo todo. Saber os **trade-offs** entre
um banco relacional e um key-value, entre replicação e sharding, entre consistência
forte e eventual, é o que permite projetar sistemas corretos — e extrair dados de
origens operacionais sem derrubá-las.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Conceitos relacionais](01-relational-concepts/README.md) | Modelo relacional, storage engines, WAL |
| 02 | [PostgreSQL](02-postgresql/README.md) | O relacional de referência para DE |
| 03 | [MySQL](03-mysql/README.md) | Diferenças e quando usar |
| 04 | [NoSQL](04-nosql/README.md) | Key-value, document, column-family, graph |
| 05 | [Indexação (nível de sistema)](05-indexing/README.md) | B-tree vs LSM, estratégia operacional |
| 06 | [Particionamento e sharding](06-partitioning-sharding/README.md) | Escalar dados horizontalmente |
| 07 | [Replicação](07-replication/README.md) | Alta disponibilidade e leituras |
| 08 | [Concorrência e consistência](08-concurrency-consistency/README.md) | MVCC, modelos de consistência |
| 09 | [Backup, recovery e DR](09-backup-recovery-dr/README.md) | Proteger e restaurar dados |

## Dependências internas

```text
Conceitos relacionais ─► PostgreSQL / MySQL
         │
         ├─► NoSQL (quando o relacional não serve)
         │
         ▼
Indexação ─► Particionamento/sharding ─► Replicação ─► Concorrência/consistência
         │
         ▼
Backup / recovery / DR
```

## Checkpoint

- [ ] Explicar o modelo relacional e o papel do WAL/storage engine.
- [ ] Escolher entre PostgreSQL, MySQL e um NoSQL conforme o caso.
- [ ] Explicar os 4 modelos NoSQL e um caso de uso de cada.
- [ ] Diferenciar B-tree (OLTP) de LSM-tree (write-heavy) e seus trade-offs.
- [ ] Explicar particionamento vs sharding vs replicação (e quando usar cada).
- [ ] Descrever replicação leader-follower e o impacto do *lag* nas leituras.
- [ ] Definir RPO/RTO e esboçar uma estratégia de backup + DR.

## Referências do módulo

- Kleppmann, M. *Designing Data-Intensive Applications*. O'Reilly, 2017 — caps.
  2, 3, 5, 6.
- Documentação do PostgreSQL e do MySQL.
- Petrov, A. *Database Internals*. O'Reilly, 2019.
