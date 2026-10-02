# Ordering, retention e replay

> 🟣 Distributed Systems · Parte de [18 — Message Brokers](../README.md)

## Ordering (ordem)

- **Garantia do Kafka**: ordem **dentro de uma partição**. Entre partições **não** há ordem global.
- Para ordem por entidade (ex.: todos os eventos de um pedido), use a **mesma chave** → mesma partição.
- Ordem global estrita exigiria **uma só partição** (sem paralelismo) — raramente vale a pena.
- Retries do producer podem reordenar sem idempotência; com `enable.idempotence=true` a ordem por
  partição é preservada.
- No consumo, processamento **paralelo** dentro de uma partição pode reordenar efeitos — mantenha
  processamento serial por partição (ou por chave) quando a ordem importa.
- Eventos podem ainda chegar fora de ordem em **event time** (ver
  [tempo e janelas](../../17-streaming/03-time-and-windows/README.md)): ordem de log ≠ ordem de
  ocorrência.

## Retention (retenção)

O log não cresce para sempre. Políticas por tópico:

- **Por tempo** — `retention.ms` (ex.: 7 dias).
- **Por tamanho** — `retention.bytes`.
- **Compactação (log compaction)** — `cleanup.policy=compact` mantém **só o último valor por chave**
  (o tópico vira um snapshot de estado atual; ideal para changelogs, [CDC](../../09-etl-elt/06-cdc/README.md),
  tabelas de lookup — base das `KTable`s).
- Combinável (`compact,delete`).

Retenção é uma decisão de **custo × janela de replay**: quanto mais retém, mais histórico para replay e
mais disco.

## Replay (reprocessamento)

Por o log reter os dados, é possível **reler** do passado:

- **Novo consumidor/grupo** começando em `earliest`.
- **Reset de offsets** de um grupo (`kafka-consumer-groups --reset-offsets --to-datetime ...`).
- **Reprocessar após bug** na lógica do consumidor/pipeline ([backfill](../../09-etl-elt/08-backfill/README.md)).
- **Reconstruir estado/tabelas** a partir do log (base de event sourcing e arquitetura Kappa).

```bash
kafka-consumer-groups.sh --bootstrap-server b:9092 --group lake-writer \
  --topic pedidos --reset-offsets --to-datetime 2024-01-15T00:00:00.000 --execute
```

### Pré-requisitos para um replay seguro

- Consumidores **[idempotentes](../../09-etl-elt/07-idempotency-retries/README.md)** (reprocessar não
  duplica).
- **Retenção suficiente** — se o dado já expirou, não há replay (considere arquivar para o lake: camada
  [bronze](../../14-data-lake/03-medallion-architecture/README.md) como segunda fonte de verdade).
- Pipelines parametrizados/determinísticos.

## Tiered storage

Kafka moderno suporta **tiered storage** (offload de segmentos antigos para object storage), permitindo
retenções muito longas a custo menor — aproximando o log de um arquivo replayable.

## Erros comuns

- Assumir ordem global do tópico.
- Retenção curta demais para a necessidade de replay/backfill.
- Replay com consumidor não-idempotente (duplicatas).
- Compactação em tópico que precisa de histórico completo (compact apaga versões antigas).
- Processar em paralelo dentro da partição e perder ordem.

## Boas práticas

- Chave = entidade que exige ordem; um consumidor serial por partição.
- Defina retenção pelo caso de uso; arquive no lake como rede de segurança.
- Use `compact` para estado/lookup, `delete` para eventos.
- Documente e teste o procedimento de replay.

## Relação com outros conceitos

- [Partitions/offsets](../04-partitions-offsets-consumer-groups/README.md),
  [Kafka](../02-apache-kafka/README.md), [delivery semantics](../../17-streaming/04-delivery-semantics/README.md).
- [Backfill](../../09-etl-elt/08-backfill/README.md), [event sourcing](../../30-advanced/02-event-sourcing-cqrs/README.md).

## Exercícios

1. Como garantir ordem dos eventos de um mesmo pedido? Qual o custo?
2. Quando usar `compact` vs `delete`?
3. Faça um replay resetando offsets a um instante e explique o que precisa ser idempotente.
4. Calcule a retenção/disco para 5 MB/s por 7 dias com RF=3.

## Referências

- Documentação do Kafka (log compaction, retention, tiered storage).
- Kleppmann, M. *DDIA* — cap. 11 (replaying old messages).
