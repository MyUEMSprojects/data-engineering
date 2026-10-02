# Fundamentos de sistemas distribuídos

> 🟢 Foundations · Parte de [01 — Fundamentos](../README.md)

## O que é e por que importa para DE

Um **sistema distribuído** é um conjunto de computadores que coopera para
aparecer como um sistema único. Praticamente toda tecnologia de dados em escala —
[Spark](../../16-distributed-processing/README.md),
[Kafka](../../18-message-brokers/README.md),
[warehouses](../../13-data-warehouse/README.md) distribuídos,
[object storage](../../19-cloud/02-object-storage/README.md) — é distribuída.
Entender os conceitos (e as leis que não dá para burlar) é o que permite
raciocinar sobre consistência, falhas e performance sem decorar o comportamento
de cada ferramenta.

## Por que distribuir

- **Escala horizontal** — quando uma máquina não dá conta de volume/tráfego,
  adiciona-se mais máquinas (*scale out*) em vez de uma máquina maior (*scale up*),
  que tem limite físico e custo não-linear.
- **Tolerância a falhas** — réplicas sobrevivem à queda de um nó.
- **Proximidade** — dados perto de quem usa (geodistribuição, *data locality*).

O preço: **complexidade**. Rede falha, mensagens atrasam, nós caem, relógios
divergem. Sistemas distribuídos existem para gerenciar isso.

## Conceitos fundamentais

### Particionamento (partitioning / sharding)

Dividir os dados em partes (*partitions*/*shards*) distribuídas entre nós, para
paralelismo e para caber em várias máquinas.

- **Por hash** — distribui uniformemente; ruim para *range queries*.
- **Por faixa (range)** — bom para intervalos; risco de *hotspots*.
- Risco central: **skew** (partições desbalanceadas). Ver
  [sharding](../../06-databases/06-partitioning-sharding/README.md) e
  [shuffle/skew no Spark](../../16-distributed-processing/03-partitioning-shuffle/README.md).

### Replicação

Manter cópias do mesmo dado em vários nós, para disponibilidade e leitura
próxima/escalável.

- **Leader–follower (primary–replica)** — escritas no líder, leituras nas
  réplicas. Simples, mas o *lag* de replicação gera leituras desatualizadas.
- **Multi-leader / leaderless** (ex.: Dynamo-style) — mais disponibilidade,
  conflitos de escrita para resolver.
- Ligada ao trade-off de **consistência** abaixo. Ver
  [replicação](../../06-databases/07-replication/README.md).

### Consistência

"Quão atualizada e coerente" é a visão dos dados entre réplicas. Espectro:

- **Strong consistency / linearizability** — toda leitura vê a escrita mais
  recente; o sistema "parece" ter uma cópia só. Caro em latência/disponibilidade.
- **Eventual consistency** — réplicas convergem "no fim"; leituras podem ser
  antigas por um tempo. Comum em sistemas AP.
- Intermediárias: *read-your-writes*, *monotonic reads*, causal consistency.

Não confundir com o **C de ACID** (integridade de uma transação) — aqui é
consistência de **réplicas**.

### Disponibilidade (availability)

A probabilidade de o sistema responder (com sucesso) a uma requisição. Medida em
"noves" (99,9%, 99,99%). Aumenta com replicação e redundância.

## CAP theorem

Em um sistema distribuído que sofre uma **partição de rede (P)** — mensagens
entre nós se perdem ou atrasam — você só pode garantir **uma** entre:

- **C (Consistency)** — todos os nós veem o mesmo dado atualizado; ou
- **A (Availability)** — todo pedido recebe resposta (possivelmente desatualizada).

```text
                 Partição de rede acontece (P é inevitável)
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
            Escolher C                   Escolher A
   (recusar/bloquear p/ não            (responder com dado
    servir dado inconsistente)          possivelmente antigo)
        sistema "CP"                       sistema "AP"
```

Pontos-chave (e erros comuns):

- **Não é "escolha 2 de 3".** Como partições acontecem na prática, a escolha real
  é **C vs A durante a partição**. Fora de partições, dá para ter C e A.
- **CP** (ex.: muitos bancos com consenso, ZooKeeper): preferem recusar a servir
  dado inconsistente.
- **AP** (ex.: Cassandra, DynamoDB em certos modos): preferem responder sempre,
  aceitando dado eventualmente consistente.
- **PACELC** estende o CAP: *se Partição, escolha A ou C; senão (Else), escolha
  Latência ou Consistência.* Captura o custo de consistência mesmo sem falhas.

## Falhas, tempo e ordem

- **Falhas parciais** — parte do sistema falha enquanto o resto segue; o normal
  em distribuído.
- **Relógios não são confiáveis** — relógios de máquinas divergem; por isso se
  usam *logical clocks* (Lamport), *vector clocks* e identificadores monotônicos
  em vez de "hora da parede" para ordenar eventos.
- **Consenso** — concordar um valor apesar de falhas: algoritmos como Paxos e
  **Raft**. Base de coordenação (ex.: eleição de líder, metadados de
  [Kafka](../../18-message-brokers/README.md)).
- **Idempotência e exactly-once** — como a rede pode duplicar/reentregar, operações
  precisam ser [idempotentes](../../09-etl-elt/07-idempotency-retries/README.md);
  "exactly-once" é alcançado combinando at-least-once + deduplicação. Ver
  [delivery semantics](../../17-streaming/04-delivery-semantics/README.md).

## Escalabilidade

- **Vertical (scale up)** — máquina maior. Simples, limitado, caro no topo.
- **Horizontal (scale out)** — mais máquinas. Elástico, exige particionamento e
  coordenação.
- **Gargalos** — *shuffle*/rede, *skew*, pontos únicos (líder), estado
  compartilhado. Sistemas bem projetados minimizam coordenação e movimento de
  dados ([data locality](../../16-distributed-processing/03-partitioning-shuffle/README.md)).

## Exemplos em ferramentas de dados

| Conceito | Onde aparece |
| --- | --- |
| Particionamento + shuffle | [Spark](../../16-distributed-processing/03-partitioning-shuffle/README.md) |
| Replicação + partições + log | [Kafka](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md) |
| Consistência eventual | NoSQL [AP](../../06-databases/04-nosql/README.md) (Cassandra/Dynamo) |
| Consenso (Raft) | Metadados de brokers, bancos distribuídos |
| Durabilidade via replicação | [Object storage](../../19-cloud/02-object-storage/README.md) |

## Erros comuns

- Enunciar o CAP como "escolha 2 de 3" (o certo é C vs A **sob partição**).
- Confundir consistência de réplicas com o C de ACID.
- Confiar na hora de relógio para ordenar eventos distribuídos.
- Assumir que a rede é confiável (as [falácias da computação distribuída](https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing)).

## Relação com outros conceitos

- Sustenta [sistemas de dados](../04-data-systems/README.md) e todo o nível de
  [sistemas distribuídos](../../16-distributed-processing/README.md).
- Conecta-se a [replicação/sharding em databases](../../06-databases/README.md) e a
  [delivery semantics em streaming](../../17-streaming/04-delivery-semantics/README.md).

## Exercícios

1. **Conceitual.** Enuncie o CAP com suas palavras e dê um exemplo de quando você
   escolheria CP e outro em que escolheria AP.
2. **Debugging.** Um usuário escreve um dado e, ao recarregar, não o vê. Que
   propriedade de consistência está faltando e como o sistema poderia garanti-la?
3. **Arquitetura.** Explique por que `JOIN` entre duas tabelas grandes é caro em
   um sistema distribuído (dica: *shuffle*) e cite uma técnica para reduzir o
   custo.

## Referências

- Kleppmann, M. *Designing Data-Intensive Applications*. O'Reilly, 2017 — caps.
  5 (replicação), 6 (particionamento), 9 (consistência e consenso).
- Brewer, E. "CAP Twelve Years Later: How the 'Rules' Have Changed". *IEEE
  Computer*, 2012.
- Abadi, D. "Consistency Tradeoffs in Modern Distributed Database System Design"
  (PACELC), 2012.
- Ongaro, D.; Ousterhout, J. "In Search of an Understandable Consensus Algorithm
  (Raft)", 2014.
