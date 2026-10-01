# Partitions, offsets e consumer groups

> 🟣 Distributed Systems · Parte de [18 — Message Brokers](../README.md)

## Partições

Um tópico é dividido em **partições**: logs ordenados e independentes. Elas são a unidade de:

- **Paralelismo** — partições são lidas/escritas em paralelo por brokers e consumidores diferentes.
- **Ordem** — a ordem só é garantida **dentro** de uma partição.
- **Escala** — distribuem dados/carga pelo cluster (ver [sharding](../../06-databases/06-partitioning-sharding/README.md)).
- **Replicação** — cada partição é replicada ([Kafka](../02-apache-kafka/README.md)).

```text
tópico "pedidos": P0 [m0 m3 m6 ...]  P1 [m1 m4 m7 ...]  P2 [m2 m5 m8 ...]
```

Nº de partições = teto de paralelismo dos consumidores de um grupo.

## Offsets

O **offset** é o número sequencial de um registro **dentro de uma partição** (0, 1, 2, ...). O consumidor
guarda "até onde leu" por partição; o Kafka persiste isso no tópico interno `__consumer_offsets`.
Offsets são o [checkpoint](../../10-data-pipelines/04-checkpoints-idempotency/README.md) do consumo e
decidem a [semântica de entrega](../../17-streaming/04-delivery-semantics/README.md). Resetar offsets
permite **replay** ([ordering/retention/replay](../05-ordering-retention-replay/README.md)).

## Consumer groups

Um **consumer group** é um conjunto de consumidores que **compartilham** a leitura de um tópico: cada
partição é atribuída a **no máximo um** consumidor do grupo.

```text
tópico (3 partições)        grupo "lake-writer"
   P0 ─────────────────────► consumidor A
   P1 ─────────────────────► consumidor B
   P2 ─────────────────────► consumidor C
```

- **Escala horizontal** — mais consumidores (até o nº de partições) = mais paralelismo.
- **Consumidor extra além do nº de partições fica ocioso.**
- **Grupos diferentes** lêem o mesmo tópico **independentemente** (cada um com seus offsets) — pub/sub:
  um grupo grava no lake, outro alimenta alertas.

## Rebalanceamento

Quando consumidores entram/saem/falham, as partições são **reatribuídas** (*rebalance*). Durante isso
pode haver pausa. Estratégias *cooperative/incremental* minimizam a interrupção. Falha de consumidor →
partições vão para outros, que retomam do **último offset commitado**.

## Escolhendo o nº de partições

- Alvo de **throughput**: partições ≥ (vazão desejada ÷ vazão por partição).
- Alvo de **paralelismo**: ≥ nº máximo de consumidores esperado.
- **Trade-offs**: mais partições = mais overhead (arquivos, memória, rebalanço, latência de eleição).
- **Aumentar depois quebra o mapeamento chave→partição** (a ordem por chave se perde para dados
  novos) — planeje com folga.

## Chave e distribuição

A chave define a partição ([producers](../03-producers-consumers/README.md)): mesma chave → mesma partição
→ ordem por entidade. Chaves muito concentradas geram **skew**/hot partition.

## Lag

`lag = último offset da partição − offset commitado do grupo`. Lag crescente = consumidor não acompanha
([backpressure](../06-backpressure/README.md)). Monitore por grupo/partição.

## Erros comuns

- Mais consumidores que partições (ociosos).
- Chave que concentra tudo numa partição.
- Poucas partições e depois precisar escalar (reparticionar quebra ordem).
- Ignorar rebalanceamentos frequentes (instabilidade).
- Confundir offset (por partição) com ordem global do tópico (não existe).

## Boas práticas

- Dimensione partições com folga; chave pensada para ordem e distribuição.
- Um grupo por finalidade de consumo; monitore lag por partição.
- Rebalanceamento cooperativo; consumidores com processamento dentro do `max.poll.interval.ms`.

## Relação com outros conceitos

- [Kafka](../02-apache-kafka/README.md), [producers/consumers](../03-producers-consumers/README.md),
  [ordering/replay](../05-ordering-retention-replay/README.md).
- [Shuffle/skew](../../16-distributed-processing/04-distributed-joins-skew/README.md),
  [checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md).

## Exercícios

1. Dado um tópico com 4 partições, quantos consumidores ativos cabem num grupo? E em dois grupos?
2. Explique por que a ordem é só por partição e como garantir ordem por pedido.
3. Calcule partições necessárias para 100 MB/s se cada partição suporta ~10 MB/s.
4. O que acontece com os offsets quando um consumidor cai?

## Referências

- Documentação do Kafka (Consumer groups); Narkhede et al., *Kafka: The Definitive Guide* — cap. 4.
