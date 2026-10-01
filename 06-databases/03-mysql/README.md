# MySQL

> 🔵 Core · Parte de [06 — Databases](../README.md)

## O que é

**MySQL** é um banco relacional de código aberto, um dos mais usados do mundo
(especialmente em aplicações web e no stack LAMP). **MariaDB** é um *fork* compatível,
criado após a aquisição do MySQL pela Oracle. Para o Data Engineer, MySQL é
principalmente uma **fonte** de dados operacionais a extrair.

## Por que conhecer

Muitíssimas aplicações (WordPress, e-commerces, SaaS) rodam sobre MySQL. Você vai
extrair dados dele — via réplica, dump ou [CDC](../../09-etl-elt/06-cdc/README.md) do
**binlog**. Entender suas particularidades evita surpresas.

## Storage engines

Diferente do Postgres, MySQL tem **engines plugáveis**:

- **InnoDB** (padrão) — transacional (ACID), MVCC, chaves estrangeiras, *row-level
  locking*. **Use este.**
- **MyISAM** (legado) — sem transações nem FKs, *table-level locking*. Evite para
  dados novos.

## Diferenças práticas vs PostgreSQL

| Aspecto | PostgreSQL | MySQL (InnoDB) |
| --- | --- | --- |
| Aderência ao padrão SQL | muito alta | boa, com desvios |
| Tipos | ricos (`jsonb`, arrays, ranges) | mais limitados (`JSON` sem índice nativo tão forte) |
| Isolamento default | READ COMMITTED | **REPEATABLE READ** |
| Índices | B-tree, GIN, GiST, BRIN... | B-tree (InnoDB), full-text, limitado |
| CTEs/window | desde sempre | desde MySQL 8.0 |
| `UPSERT` | `INSERT ... ON CONFLICT` | `INSERT ... ON DUPLICATE KEY UPDATE` |
| CDC (log) | WAL (logical/replication slots) | **binlog** |
| Chaves estrangeiras | impostas | impostas (InnoDB) |

> MySQL 8.0+ fechou muitas lacunas (CTEs, window functions, melhor JSON). Em versões
> antigas, cuidado: faltam esses recursos.

## Pegadinhas importantes para DE

- **Collation/charset** — use `utf8mb4` (o antigo `utf8` do MySQL **não** cobre todos
  os caracteres Unicode, ex.: emojis). Erros de encoding em ingestão vêm muito disso.
- **Modo SQL "frouxo"** em versões/config antigas aceitava dados inválidos
  silenciosamente (datas `0000-00-00`, truncamento). Verifique o `sql_mode`.
- **Case sensitivity** de nomes de tabela depende do SO/config.
- **`REPEATABLE READ`** como default muda a semântica de leituras concorrentes vs
  Postgres.

## Operação básica

```bash
mysql -h host -u user -p db
```

```sql
SHOW DATABASES;
SHOW TABLES;
DESCRIBE pedidos;
SHOW INDEX FROM pedidos;
-- carga rápida
LOAD DATA INFILE 'dados.csv' INTO TABLE pedidos
  FIELDS TERMINATED BY ',' IGNORE 1 LINES;
```

`LOAD DATA INFILE` é o equivalente ao `COPY` do Postgres para carga em massa.

## Extração para analytics

- **Réplica de leitura** — aponte sua extração para a réplica, não para o primário.
- **`mysqldump`/`mydumper`** — dumps lógicos (mydumper é paralelo e mais rápido).
- **Binlog + Debezium** — [CDC](../../09-etl-elt/06-cdc/README.md) em tempo quase real
  (requer `binlog_format=ROW`).

## Subindo com Docker

```yaml
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: app
    command: ["--binlog-format=ROW"]     # habilita CDC
    ports: ["3306:3306"]
```

## MySQL vs PostgreSQL: qual escolher

- **Postgres** — padrão recomendado para projetos novos de dados: tipos ricos
  (`jsonb`), extensibilidade, aderência ao SQL, melhor para workloads analíticos
  leves.
- **MySQL** — ótima opção para apps web tradicionais, enorme base instalada, simples e
  rápido para OLTP simples. Você frequentemente o encontra como **fonte legada**.

Na prática, como DE você usa o que a empresa já tem como origem e, no destino
analítico, escolhe Postgres/warehouse.

## Erros comuns

- `utf8` em vez de `utf8mb4` → caracteres corrompidos na ingestão.
- Assumir recursos de SQL que só existem no 8.0+ em um servidor antigo.
- Extrair do primário e impactar a produção.
- Ignorar `sql_mode` permissivo que deixou dados inválidos entrarem.
- Usar MyISAM para dados que precisam de transações/integridade.

## Boas práticas

- InnoDB + `utf8mb4` + `sql_mode` estrito.
- Extração via réplica/CDC (binlog ROW).
- `LOAD DATA`/mydumper para volumes grandes.
- Documente diferenças de dialeto ao portar SQL entre MySQL e Postgres.

## Relação com outros conceitos

- Implementa [conceitos relacionais](../01-relational-concepts/README.md); comparar com
  [PostgreSQL](../02-postgresql/README.md).
- Binlog → [CDC](../../09-etl-elt/06-cdc/README.md).
- [Replicação](../07-replication/README.md) para extração.

## Exercícios

1. Suba um MySQL 8 via Docker com `binlog-format=ROW` e carregue dados com
   `LOAD DATA`.
2. Liste 5 diferenças de SQL/comportamento entre MySQL e Postgres relevantes para
   portar queries.
3. Explique o problema do `utf8` vs `utf8mb4` com um exemplo de dado que quebra.
4. Descreva como configurar CDC a partir do binlog do MySQL.

## Referências

- Documentação oficial do MySQL (dev.mysql.com/doc) e do MariaDB.
- *High Performance MySQL*, Schwartz et al. O'Reilly.
