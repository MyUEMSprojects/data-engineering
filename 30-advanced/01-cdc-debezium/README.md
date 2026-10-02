# CDC e Debezium (avançado)

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: especialização de alto valor prático*
>
> Conceito e abordagens de CDC em [ETL/CDC](../../09-etl-elt/06-cdc/README.md). Aqui: **Debezium em
> profundidade** e os desafios de produção.

## O que é Debezium

**Debezium** é uma plataforma open source de **CDC log-based**: conectores (sobre
[Kafka Connect](../../18-message-brokers/07-kafka-connect/README.md)) que leem o **log de transações** de
bancos (Postgres WAL, MySQL binlog, SQL Server CDC, MongoDB oplog, Oracle LogMiner/XStream) e publicam **eventos
de mudança** em tópicos Kafka — um tópico por tabela. Também roda em modo **Debezium Server** (sem Kafka) e
embutido (engine).

```text
Postgres (WAL) ─► Debezium Connector ─► Kafka (topics: server.schema.tabela) ─► consumidores (lake, warehouse, cache, busca, microsserviços)
```

## Anatomia do evento

```json
{
  "before": {"id": 7, "uf": "SP"},
  "after":  {"id": 7, "uf": "RJ"},
  "source": {"connector":"postgresql","db":"app","schema":"public","table":"clientes",
             "lsn": 4398046511104, "txId": 812, "ts_ms": 1700000000000, "snapshot":"false"},
  "op": "u",                 // c=create, u=update, d=delete, r=read (snapshot), t=truncate
  "ts_ms": 1700000000123
}
```

- `before`/`after` permitem **reconstruir** a mudança (before depende da config — ex.: `REPLICA IDENTITY FULL`
  no Postgres para obter `before` completo).
- **Chave** da mensagem = PK da linha → ordem **por registro** na partição ([ordem](../../18-message-brokers/05-ordering-retention-replay/README.md)).
- **Tombstone** (valor `null`) após um `delete` permite **log compaction** remover a chave.

## Ciclo: snapshot + streaming

1. **Snapshot inicial** (`snapshot.mode`: `initial`, `schema_only`, `never`, `when_needed`...): lê o estado
   atual (consistente) e emite eventos `op=r`.
2. **Streaming**: continua do **offset do log** (LSN/binlog position) onde o snapshot terminou — sem lacunas.
3. **Snapshots incrementais** (sinalizados via *signal table*): re-snapshot de tabelas **sem parar** o
   streaming — útil para backfill/novas tabelas ([backfill](../../09-etl-elt/08-backfill/README.md)).

## Configuração mínima de um conector (Postgres, ilustrativo)

```json
{
  "name": "pg-app-cdc",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "pg", "database.port": "5432",
    "database.user": "debezium", "database.password": "${file:/secrets/pg.properties:password}",
    "database.dbname": "app",
    "topic.prefix": "app",
    "plugin.name": "pgoutput",
    "slot.name": "debezium_app",
    "table.include.list": "public.clientes,public.pedidos",
    "snapshot.mode": "initial",
    "key.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "transforms": "unwrap",
    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState"
  }
}
```

(Propriedades variam por versão do Debezium — confira a documentação. Segredos via *config providers*,
nunca em texto claro — [secrets](../../26-security/04-secrets-management/README.md).)

**Pré-requisitos no banco**: Postgres `wal_level=logical`, usuário com `REPLICATION`, publicação/slot;
MySQL `binlog_format=ROW`, `binlog_row_image=FULL`. Dê só os privilégios mínimos.

## SMT úteis

- **`ExtractNewRecordState`** ("unwrap"): achata o envelope e emite só o estado `after` (+ metadados opcionais
  `__op`, `__deleted`) — simplifica sinks relacionais.
- **Outbox Event Router**: implementa o **Outbox pattern** — publica eventos de uma tabela *outbox* escrita na
  **mesma transação** do domínio (garante atomicidade evento+dado; base de [event-driven](../../17-streaming/02-event-driven-architecture/README.md)
  e [event sourcing](../02-event-sourcing-cqrs/README.md)).
- Roteamento, mascaramento de campos (PII), filtros ([mascaramento](../../26-security/07-data-masking-pii/README.md)).

## Consumindo e aplicando no destino

- **Lakehouse/warehouse**: sinks que fazem `MERGE`/upsert por PK (Iceberg/Delta/Hudi sinks, Snowflake/BigQuery
  connectors, Flink/Spark) — estado atual + opcionalmente **histórico** (SCD2/append do changelog)
  ([SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md)).
- **Aplicação idempotente** pelo **PK + posição do log (LSN/ts_ms)**; descarte eventos antigos/duplicados
  ([idempotência](../../09-etl-elt/07-idempotency-retries/README.md), [delivery semantics](../../17-streaming/04-delivery-semantics/README.md)).
- **Deletes**: aplicar `delete` ou *soft delete* (`__deleted=true`) conforme necessidade analítica/LGPD.

## Desafios de produção

| Desafio | Descrição | Mitigação |
| --- | --- | --- |
| **Replication slot retendo WAL** (Postgres) | consumidor parado ⇒ WAL cresce e **enche o disco** da fonte | monitorar `pg_replication_slots`/lag; alertas; `max_slot_wal_keep_size`; remover slots órfãos |
| **Schema evolution** | DDL na origem muda o schema dos eventos | Schema Registry + compatibilidade; processo de mudança com o produtor ([contratos](../../29-data-contracts/README.md)) |
| **Ordem e duplicatas** | at-least-once; reprocessamento após restart | idempotência por PK+LSN |
| **Snapshot de tabelas grandes** | longo/pesado | snapshots incrementais; janela; réplica |
| **Tipos especiais** | decimais, timestamps, JSON, geometria | converters/`decimal.handling.mode`; documentar |
| **Transações grandes / alto volume** | picos de latência | particionar tópicos, tuning, scaling de consumidores |
| **Failover do banco** | slots/posições em réplicas | Postgres 17+ failover slots/estratégias; testar runbook |
| **Segurança/PII** | dados sensíveis nos tópicos | SMT de mascaramento, ACLs de tópico, criptografia |
| **TRUNCATE / dados sem PK** | tabelas sem PK dificultam upsert | exigir PK; REPLICA IDENTITY adequada |
| **Impacto na fonte** | leitura do log é leve, mas snapshot não | réplica/janelas; limitar tabelas |

## Alternativas e quando usar CDC

- **Alternativas**: [polling por watermark](../../09-etl-elt/05-full-vs-incremental/README.md) (não pega
  deletes), triggers, CDC **gerenciado** (AWS DMS, GCP Datastream, Fivetran/Airbyte CDC, Estuary), Maxwell,
  `pg_logical`. Muitos SaaS gerenciados escondem a complexidade (trade: custo/controle).
- **Use CDC** para replicação OLTP→lake/warehouse com baixa latência e **deletes**, sincronizar caches/busca,
  alimentar eventos. **Não use** se polling diário simples basta (menos peças).

## Erros comuns

- Não monitorar o replication slot (disco da fonte enche).
- Esperar `before` completo sem `REPLICA IDENTITY FULL`/config.
- Aplicar eventos sem idempotência/ordem (estado errado no destino).
- Ignorar evolução de schema da origem.
- Privilégios amplos para o usuário do conector; senha em claro.
- Tabelas sem PK; snapshot de tabela gigante em horário de pico.

## Boas práticas

- Conector com privilégios mínimos; `table.include.list` explícito; Schema Registry (Avro/Protobuf).
- Monitorar lag, slots, offsets, falhas de conector/tasks; alertas e runbooks.
- Sink idempotente por PK+posição; política clara de deletes/histórico.
- Testar failover, snapshot incremental e evolução de schema antes de produção.
- Considere gerenciado se o time for pequeno.

## Relação com outros conceitos

- [CDC (ETL)](../../09-etl-elt/06-cdc/README.md), [Kafka Connect](../../18-message-brokers/07-kafka-connect/README.md),
  [replicação/WAL](../../06-databases/07-replication/README.md), [event sourcing/outbox](../02-event-sourcing-cqrs/README.md),
  [lakehouse](../../15-lakehouse/README.md), [Projeto 07/08](../../projects/07-kafka/README.md).

## Exercícios

1. Descreva a configuração do Postgres e o conector para replicar `clientes` e `pedidos` ao lake.
2. Explique como aplicar eventos CDC de forma idempotente num destino Iceberg (PK + LSN).
3. Que métricas/alertas você configuraria para evitar o problema do replication slot?
4. Explique o Outbox pattern e o problema que resolve (dual-write).

## Referências

- Documentação do Debezium (debezium.io); Kleppmann, *DDIA* (cap. 11 — CDC); docs de Postgres logical
  decoding e MySQL binlog; AWS DMS / GCP Datastream.
