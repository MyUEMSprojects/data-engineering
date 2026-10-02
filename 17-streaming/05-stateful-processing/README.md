# Stateful processing

> 🟣 Distributed Systems · Parte de [17 — Streaming](../README.md)

## O que é

Processamento **com estado (stateful)** é quando o resultado de um evento depende de eventos
**anteriores** — o sistema precisa **lembrar** algo entre eventos. Oposto do **stateless** (cada evento
é processado isoladamente). Agregações, [janelas](../03-time-and-windows/README.md), joins de stream e
detecção de padrões são todos stateful.

## Stateless vs stateful

```text
Stateless:  para cada evento, transforma/filtra isoladamente (map, filter)
            → não precisa lembrar nada
Stateful:   "soma acumulada por usuário", "contagem por janela", "join de dois streams"
            → precisa MANTER estado entre eventos
```

Exemplos stateful:

- **Agregações contínuas** — total/contagem/média por chave (acumula).
- **[Janelas](../03-time-and-windows/README.md)** — a janela guarda os eventos/agregados até fechar.
- **Joins de stream** — buffer de um lado esperando o outro casar.
- **Deduplicação** — lembrar IDs já vistos ([dedupe](../../09-etl-elt/09-deduplication/README.md)).
- **Detecção de padrões/sessões** — sequência de eventos no tempo.

## O desafio: estado em sistema distribuído

O estado precisa ser:

- **Particionado** — o estado de cada chave vive no nó que processa aquela chave (particionado pela
  chave, como no [shuffle](../../16-distributed-processing/03-partitioning-shuffle/README.md)).
- **Durável/tolerante a falhas** — se o nó cai, o estado **não pode se perder** (senão a contagem
  "zera"). Resolvido com [checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md) do
  estado.
- **Escalável** — pode crescer muito (ex.: estado por usuário em milhões de usuários) → precisa ser
  gerenciado eficientemente (em memória + disco/RocksDB).

## Como as engines gerenciam estado

- **Local state + checkpoint** — cada operador mantém seu estado localmente (memória/RocksDB) e o
  **persiste periodicamente** num storage durável (checkpoint). Em falha, restaura do último checkpoint
  (ver [checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md)).
- **[Flink](../07-flink/README.md)** — estado de primeira classe: *keyed state*, *state backends*
  (memória/RocksDB), checkpoints distribuídos (Chandy-Lamport) e *savepoints* → forte em stateful +
  exactly-once.
- **[Kafka Streams](../06-kafka-streams/README.md)** — *state stores* locais (RocksDB) respaldados por
  um **changelog topic** no Kafka (o estado é reconstruível relendo o changelog).
- **[Spark Structured Streaming](../08-spark-structured-streaming/README.md)** — estado em checkpoint;
  operações como `mapGroupsWithState`/agregações mantêm estado entre micro-batches.

## Estado + exactly-once

Para resultados corretos, o estado precisa ser consistente com os offsets consumidos: o checkpoint
salva **estado + posição de leitura juntos**, de forma atômica. Assim, ao restaurar, o sistema retoma
sem perder nem duplicar o efeito no estado (ver [delivery semantics](../04-delivery-semantics/README.md)).

## Gerenciamento de tamanho do estado (TTL)

Estado pode crescer indefinidamente (ex.: lembrar IDs para dedupe "para sempre"). Soluções:

- **TTL** — expirar estado antigo (ex.: lembrar IDs só por 24h).
- **Janelas** fecham e liberam seu estado após o watermark + allowed lateness.
- **Compaction** do changelog (Kafka Streams) mantém só o valor mais recente por chave.

Estado sem limite é uma causa comum de OOM/crescimento de custo em jobs de streaming longos.

## Exemplo conceitual: contagem por usuário

```text
evento(user=A) → estado[A] = 1
evento(user=A) → estado[A] = 2     (lembrou o 1 anterior)
evento(user=B) → estado[B] = 1
[checkpoint: salva {A:2, B:1} + offsets]
[crash] → restaura {A:2, B:1} do checkpoint → continua sem perder a contagem
```

## Erros comuns

- Assumir que estado sobrevive a reinícios sem checkpoints (perde o acumulado).
- Estado sem TTL/limite → cresce até OOM.
- Checkpoint de estado desalinhado dos offsets → inconsistência (dupla contagem/perda).
- Fazer agregação "global" sem particionar por chave (não escala).
- Mudar a lógica/estado e reusar checkpoint incompatível.

## Boas práticas

- Particione o estado pela chave; use state backend adequado (RocksDB para estado grande).
- **Checkpoint** estado + offsets juntos (tolerância a falhas + exactly-once).
- Limite o estado com **TTL**/janelas; monitore o tamanho do estado.
- Planeje migração de estado ao mudar a lógica (savepoints/full-refresh).

## Relação com outros conceitos

- [Tempo e janelas](../03-time-and-windows/README.md),
  [delivery semantics](../04-delivery-semantics/README.md),
  [checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md).
- Engines: [Flink](../07-flink/README.md), [Kafka Streams](../06-kafka-streams/README.md),
  [Spark](../08-spark-structured-streaming/README.md).

## Exercícios

1. Classifique como stateless ou stateful: filtrar eventos; contar por usuário; média móvel; mapear
   campos; join de dois streams.
2. Explique como o estado sobrevive à queda de um nó (checkpoint).
3. Descreva por que o estado precisa de TTL e dê um exemplo de dedupe com TTL.
4. Explique por que checkpoint de estado e offsets precisam ser atômicos juntos.

## Referências

- Akidau, T. et al. *Streaming Systems* — estado e consistência.
- Documentação de state/checkpoints do Flink; state stores do Kafka Streams.
- Kleppmann, M. *DDIA* — cap. 11.
