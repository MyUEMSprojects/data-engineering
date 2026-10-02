# PostgreSQL

> 🔵 Core · Parte de [06 — Databases](../README.md)

## O que é

**PostgreSQL** (ou "Postgres") é um banco de dados relacional de código aberto,
maduro e extensível, considerado o mais aderente ao padrão SQL. É o banco "default"
recomendado para a maioria dos projetos e uma fonte/ferramenta onipresente em Data
Engineering.

## Por que o DE deve conhecer bem

- É a **fonte OLTP** mais comum (muitas aplicações usam Postgres).
- Serve de **banco de desenvolvimento/analytics leve** e aparece nos
  [projetos](../../projects/README.md) deste repositório.
- Seu **WAL** alimenta [CDC](../../09-etl-elt/06-cdc/README.md) (Debezium).
- É extensível a ponto de virar warehouse/lake leve (ver extensões abaixo).

## Características de destaque

- **Padrão SQL + extras** — [CTEs recursivas](../../05-sql/04-subqueries-ctes/README.md),
  [window functions](../../05-sql/05-window-functions/README.md),
  [GROUPING SETS](../../05-sql/13-analytical-sql/README.md).
- **Tipos ricos** — `jsonb`, `array`, `hstore`, `range`, `uuid`, `numeric` exato,
  `timestamptz`, tipos geométricos.
- **MVCC** — leituras não bloqueiam escritas (ver
  [concorrência](../08-concurrency-consistency/README.md)).
- **Índices variados** — B-tree, GIN, GiST, BRIN, hash (ver
  [indexação](../05-indexing/README.md)).
- **Extensibilidade** — extensões, UDFs em várias linguagens, *foreign data wrappers*.

## jsonb — relacional + semiestruturado

Postgres armazena e **consulta** JSON de forma eficiente (`jsonb`), unindo rigidez
relacional e flexibilidade de documento:

```sql
CREATE TABLE eventos (id bigint, payload jsonb);
SELECT payload->>'type' AS tipo,
       payload->'user'->>'id' AS user_id
FROM eventos
WHERE payload @> '{"type": "purchase"}';     -- operador de contenção
CREATE INDEX idx_payload ON eventos USING gin (payload);  -- índice p/ jsonb
```

Isso cobre muitos casos que levariam ingenuamente a um banco de documentos (ver
[document](../04-nosql/02-document/README.md)).

## Operação essencial (psql)

```bash
psql "postgresql://user:senha@host:5432/db"
```

```sql
\l            -- lista bancos
\dt           -- lista tabelas
\d pedidos    -- descreve a tabela
\di           -- índices
\timing on    -- mostra tempo das queries
\copy pedidos FROM 'dados.csv' CSV HEADER   -- carga rápida de CSV
```

`COPY`/`\copy` é a forma mais rápida de carga em massa (muito mais que `INSERT` um a
um).

## Subindo com Docker (usado nos projetos)

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: de
      POSTGRES_PASSWORD: de
      POSTGRES_DB: warehouse
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
volumes: { pgdata: {} }
```

## Manutenção que todo DE deveria saber

- **`VACUUM`/autovacuum** — recupera espaço de tuplas mortas do MVCC; tabelas
  "inchadas" ficam lentas.
- **`ANALYZE`** — atualiza estatísticas para o
  [planejador](../../05-sql/10-query-planning-explain/README.md).
- **Réplicas de leitura** — descarregar consultas analíticas (ver
  [replicação](../07-replication/README.md)).
- **Monitoramento** — `pg_stat_activity` (queries ativas),
  `pg_stat_user_indexes` (uso de índices).

## Extensões úteis para dados

| Extensão | Para quê |
| --- | --- |
| **PostGIS** | dados geoespaciais |
| **pg_partman** | particionamento gerenciado por tempo |
| **TimescaleDB** | séries temporais em escala |
| **Citus** | distribuir/sharding (escala horizontal) |
| **pg_stat_statements** | profiling de queries mais custosas |
| **postgres_fdw** | consultar outro Postgres como se fosse local |

## Quando Postgres (não) é suficiente

- **Suficiente** para OLTP, apps, analytics de pequeno/médio porte, protótipos, e boa
  parte de "big data" que, medido, não é tão big.
- **Insuficiente** para analytics de dezenas de TB com alta concorrência (prefira
  [warehouse colunar](../../13-data-warehouse/README.md)) e para escala de escrita
  extrema/distribuída (NoSQL/Citus).

## Erros comuns

- Ignorar autovacuum → *bloat* e lentidão.
- `INSERT` linha a linha em vez de `COPY` para cargas grandes.
- Usar `float` para dinheiro (use `numeric`).
- Rodar BI pesado no primário em vez de numa réplica.
- Não indexar `jsonb` consultado (GIN).

## Boas práticas

- `timestamptz` + UTC; `numeric` para dinheiro; `text` em vez de `varchar(n)`
  arbitrário.
- `COPY` para cargas; índices conforme as queries reais.
- Réplica para leituras analíticas; CDC via WAL para ingestão.
- Monitore `pg_stat_statements` e o uso de índices.

## Relação com outros conceitos

- Implementa os [conceitos relacionais](../01-relational-concepts/README.md).
- Comparação: [MySQL](../03-mysql/README.md).
- Fonte para [CDC](../../09-etl-elt/06-cdc/README.md) e destino nos
  [projetos](../../projects/01-basic-etl/README.md).

## Exercícios

1. Suba um Postgres via Docker, crie um schema com constraints e carregue um CSV com
   `\copy`.
2. Armazene eventos em `jsonb`, crie um índice GIN e consulte por um campo do JSON.
3. Use `pg_stat_statements` para achar as queries mais custosas de uma carga de teste.
4. Explique por que rodar relatórios no primário é problemático e como uma réplica
   resolve.

## Referências

- Documentação oficial do PostgreSQL (postgresql.org/docs).
- *PostgreSQL: Up and Running*, Obe & Hsu. O'Reilly.
