# Event-driven architecture

> 🟣 Distributed Systems · Parte de [17 — Streaming](../README.md)

## O que é

**Arquitetura orientada a eventos (EDA)** é um estilo em que os componentes se comunicam produzindo e
consumindo **eventos** — registros imutáveis de "algo que aconteceu" (`PedidoCriado`,
`PagamentoAprovado`) — em vez de chamarem uns aos outros diretamente. Os produtores emitem eventos num
log/broker ([Kafka](../../18-message-brokers/README.md)); os consumidores reagem a eles de forma
**assíncrona e desacoplada**.

## Por que importa para DE

EDA é a base do streaming e da integração em tempo real. Para o Data Engineer, eventos são uma
**fonte** rica (cada ação do usuário/sistema vira um dado) e um mecanismo de **desacoplamento** entre
sistemas operacionais e a plataforma de dados — frequentemente via
[CDC](../../09-etl-elt/06-cdc/README.md) (mudanças de banco viram eventos).

## Evento vs comando vs request

- **Evento** — "isto aconteceu" (fato no passado, imutável): `PedidoCriado`. O produtor não sabe/não se
  importa quem vai consumir.
- **Comando** — "faça isto" (dirigido a alguém): `CriarPedido`.
- **Request/response (síncrono)** — A chama B e espera a resposta (acoplado no tempo).

EDA favorece **eventos** → desacoplamento (quem emite não conhece os consumidores).

## Como funciona

```text
Produtor ──(evento)──► [ Broker / Log (Kafka) ]──► Consumidor A (atualiza cache)
                                              ├──► Consumidor B (grava no lake)
                                              └──► Consumidor C (dispara e-mail)
   um evento, muitos consumidores independentes (pub/sub)
```

- O **log** ([Kafka](../../18-message-brokers/01-queue-vs-log/README.md)) retém os eventos; novos
  consumidores podem ler desde o início (*replay*).
- Consumidores processam no seu ritmo, independentemente uns dos outros.

## Benefícios

- **Desacoplamento** — adicionar um consumidor não afeta o produtor nem os outros.
- **Escalabilidade** — produtores e consumidores escalam separadamente; o broker absorve picos
  (*buffer*/backpressure).
- **Resiliência** — se um consumidor cai, os eventos ficam no log; ele retoma depois (por
  [offset](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md)).
- **Tempo real** — reações imediatas a eventos.
- **Replay / auditoria** — reprocessar o histórico de eventos (reconstruir estado, corrigir bugs).

## Trade-offs (não é grátis)

- **Complexidade** — fluxo assíncrono é mais difícil de entender/depurar que request/response.
- **Consistência eventual** — consumidores atualizam em momentos diferentes (ver
  [consistência](../../06-databases/08-concurrency-consistency/README.md)).
- **Ordem e duplicação** — eventos podem chegar fora de ordem/duplicados ([delivery
  semantics](../04-delivery-semantics/README.md)); exige [idempotência](../../09-etl-elt/07-idempotency-retries/README.md).
- **Schema** — contratos de evento precisam de disciplina ([schema evolution](../../08-data-formats/10-schema-evolution/README.md),
  [data contracts](../../29-data-contracts/README.md)).
- **Debugging distribuído** — rastrear um fluxo exige observabilidade/tracing.

## Padrões relacionados

- **Pub/Sub** — produtores publicam; múltiplos consumidores assinam.
- **Event sourcing** — o **log de eventos é a fonte da verdade**; o estado é derivado reproduzindo os
  eventos (ver [advanced](../../30-advanced/02-event-sourcing-cqrs/README.md)).
- **CQRS** — separar o modelo de escrita (comandos) do de leitura (consultas) — ver
  [advanced](../../30-advanced/02-event-sourcing-cqrs/README.md).
- **CDC como eventos** — mudanças de banco viram um stream de eventos (ver
  [CDC](../../09-etl-elt/06-cdc/README.md)).
- **Outbox pattern** — publicar eventos de forma atômica com a transação do banco (evita perder
  eventos).

## EDA e a plataforma de dados

```text
Apps/serviços ──eventos──► Kafka ──► stream processing (Flink/KStreams/Spark) ──► lake/warehouse
                                 └──► consumidores operacionais (cache, notificações)
```

Eventos alimentam tanto reações operacionais quanto a ingestão analítica — a mesma fonte serve os dois
mundos (base da arquitetura [Kappa](../../01-foundations/04-data-systems/README.md)).

## Design de eventos

- **Imutáveis** e nomeados no passado (`PedidoCriado`, não `CriarPedido`).
- **Autocontidos** o suficiente para o consumidor agir (ou com referência para buscar detalhes).
- **Versionados** com compatibilidade ([schema evolution](../../08-data-formats/10-schema-evolution/README.md)/
  registry).
- Chave de partição pensada para **ordem** onde importa (eventos da mesma entidade na mesma partição —
  ver [Kafka](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md)).

## Erros comuns

- Usar EDA onde request/response síncrono seria mais simples (complexidade à toa).
- Ignorar ordem/duplicação (consumidores não-idempotentes).
- Eventos sem contrato/versionamento (quebram consumidores).
- Perder eventos por não publicar atomicamente com a transação (use outbox).
- Esperar consistência forte imediata entre consumidores.

## Boas práticas

- Eventos imutáveis, bem nomeados, versionados e com contrato.
- Consumidores **idempotentes** e tolerantes a ordem/duplicação.
- Use outbox/CDC para publicar sem perder eventos.
- Observabilidade/tracing para depurar fluxos assíncronos.
- Use EDA quando o desacoplamento/tempo real justificar.

## Relação com outros conceitos

- [Message brokers/Kafka](../../18-message-brokers/README.md),
  [delivery semantics](../04-delivery-semantics/README.md),
  [stateful](../05-stateful-processing/README.md).
- [CDC](../../09-etl-elt/06-cdc/README.md),
  [event sourcing/CQRS](../../30-advanced/02-event-sourcing-cqrs/README.md),
  [data contracts](../../29-data-contracts/README.md).

## Exercícios

1. Modele 4 eventos de um e-commerce (nomes no passado, campos) e os consumidores de cada.
2. Diferencie evento, comando e request/response com exemplos.
3. Explique por que consumidores precisam ser idempotentes numa EDA.
4. Descreva o outbox pattern e o problema que ele resolve.

## Referências

- Kleppmann, M. *DDIA* — cap. 11 (event streams).
- Stopford, B. *Designing Event-Driven Systems* (Confluent, gratuito).
