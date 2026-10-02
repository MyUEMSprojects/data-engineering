# CDC — Change Data Capture

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

**Change Data Capture (CDC)** é a técnica de **capturar as mudanças** (inserts, updates,
**deletes**) de um banco de dados de origem assim que acontecem, para propagá-las a outros
sistemas (lake, warehouse, cache, outro serviço) — tipicamente em tempo quase real e com
**impacto mínimo** na fonte.

## Por que existe / que problema resolve

A extração incremental por [watermark](../05-full-vs-incremental/README.md) tem limites:
não captura **deletes**, depende de uma coluna `updated_at` confiável e consulta a fonte
periodicamente (carga na origem, latência). CDC resolve tudo isso lendo as mudanças direto
da origem — completo (inclui deletes), de baixa latência e de baixo impacto.

## Abordagens de CDC

### 1. Log-based (baseado no log de transações) — a melhor

Lê o **log de replicação** do banco ([WAL](../../06-databases/01-relational-concepts/README.md)
no Postgres, **binlog** no MySQL, redo log no Oracle). Como o log já existe (para
[replicação](../../06-databases/07-replication/README.md)/recovery), o impacto na fonte é
mínimo e todas as mudanças (inclusive deletes) são capturadas em ordem.

```text
App ─► escreve ─► Banco ─► WAL/binlog ─► [Debezium] ─► Kafka ─► lake/warehouse
```

**Debezium** (sobre [Kafka Connect](../../18-message-brokers/README.md)) é a ferramenta de
referência. Produz um stream de eventos de mudança (um por linha alterada).

### 2. Trigger-based

[Triggers](../../05-sql/12-procedures-functions/README.md) no banco escrevem as mudanças em
uma tabela de auditoria, que é então lida. Funciona em qualquer banco, mas **adiciona carga
de escrita** na fonte e acopla lógica ao banco.

### 3. Query-based (polling)

Consultas periódicas por `updated_at` (= [incremental por watermark](../05-full-vs-incremental/README.md)).
Simples, mas não é "CDC de verdade": não pega deletes, tem latência e carga de leitura.

| Abordagem | Deletes | Latência | Impacto na fonte | Complexidade |
| --- | --- | --- | --- | --- |
| Log-based | ✅ | baixa | mínimo | média (infra) |
| Trigger-based | ✅ | baixa | médio (escrita) | média |
| Query-based | ❌ | alta | leitura periódica | baixa |

## Anatomia de um evento CDC

Cada mudança vira um evento com o **antes** e **depois**, a operação e metadados:

```json
{
  "op": "u",                               // c=create, u=update, d=delete, r=snapshot
  "before": {"id": 7, "uf": "SP"},
  "after":  {"id": 7, "uf": "RJ"},
  "source": {"table": "clientes", "lsn": 123456, "ts_ms": 1700000000000}
}
```

Isso permite ao consumidor aplicar a mudança (upsert/delete) no destino e até reconstruir
histórico ([SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md)).

## Snapshot inicial + streaming

CDC geralmente faz um **snapshot** inicial (lê o estado atual da tabela) e depois passa a
**streamar** as mudanças a partir daquele ponto do log — garantindo que o destino comece
completo e siga atualizado.

## Processando CDC no destino

- **Upsert/merge** por chave aplica inserts/updates; **delete** remove (ou marca soft
  delete) — ver [loading](../04-loading/README.md).
- Eventos podem chegar **fora de ordem/duplicados** → use a posição do log (LSN/offset) e
  [idempotência](../07-idempotency-retries/README.md) para aplicar corretamente.
- Para analytics, muitas vezes guarda-se o **stream de mudanças** (append) e constrói-se o
  estado atual/histórico via [dedupe](../09-deduplication/README.md)/SCD.

## Casos de uso

- **Replicar OLTP → lake/warehouse** em tempo quase real, sem bater na produção.
- **Sincronizar** bancos/serviços/caches.
- **Event-driven architecture** — transformar mudanças de banco em eventos (ver
  [streaming](../../17-streaming/README.md)).
- **Auditoria/histórico** e alimentar [SCD2](../../07-data-modeling/10-slowly-changing-dimensions/README.md).

## Requisitos e cuidados

- **Configuração na fonte**: Postgres precisa de `wal_level=logical` + *replication slot*;
  MySQL de `binlog_format=ROW`.
- **Replication slots** (Postgres) retêm WAL até serem consumidos → se o consumidor cai, o
  WAL **acumula** e pode encher o disco da fonte. Monitore!
- **Schema changes** na origem precisam ser propagados (ver
  [schema evolution](../../08-data-formats/10-schema-evolution/README.md)).
- **Ordem e exactly-once** — trate com offsets + idempotência (ver
  [delivery semantics](../../17-streaming/04-delivery-semantics/README.md)).

## Erros comuns

- Usar polling por `updated_at` e achar que é CDC completo (perde deletes).
- Não monitorar replication slots → disco da fonte enche.
- Ignorar ordem/duplicação dos eventos (aplicar updates fora de ordem).
- Não planejar mudanças de schema da origem.

## Boas práticas

- Prefira **log-based** (Debezium) para baixo impacto e captura completa.
- Snapshot inicial + streaming; aplique com upsert idempotente por chave.
- Monitore lag e slots; trate schema evolution e deletes explicitamente.
- Use a posição do log para ordenar/deduplicar.

## Relação com outros conceitos

- Habilitado pelo [log de replicação](../../06-databases/07-replication/README.md).
- Alimenta [incremental](../05-full-vs-incremental/README.md),
  [streaming](../../17-streaming/README.md), [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md).
- Depende de [idempotência](../07-idempotency-retries/README.md),
  [Kafka](../../18-message-brokers/README.md).

## Exercícios

1. Compare CDC log-based, trigger-based e query-based em deletes, latência e impacto.
2. Descreva a configuração mínima para habilitar CDC num Postgres e num MySQL.
3. Dado um stream de eventos CDC, escreva a lógica de aplicar create/update/delete por chave
   de forma idempotente.
4. Explique o risco dos replication slots e como monitorá-lo.

## Referências

- Documentação do Debezium (debezium.io).
- Kleppmann, M. *DDIA* — cap. 11 (change data capture, event logs).
- Documentação do PostgreSQL (logical replication) e MySQL (binlog).
