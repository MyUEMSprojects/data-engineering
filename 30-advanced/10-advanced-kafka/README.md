# Kafka avançado

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: aprofundamento de ferramenta essencial*
>
> Pré-requisito: [módulo 18](../../18-message-brokers/README.md). Aqui: **internals, garantias e operação em
> escala**. Versões atuais usam **KRaft** (sem ZooKeeper); confira recursos/configs da sua versão.

## 1. Internals do armazenamento

- **Log segmentado**: cada partição é um diretório de **segmentos** (`.log` + índices `.index`/`.timeindex`);
  escrita **append-only** sequencial; leitura por offset via índice esparso. O broker usa **page cache** e
  **zero-copy** (`sendfile`) — por isso é rápido.
- **Retenção**: por tempo/tamanho **por segmento** (remove segmentos inteiros); **log compaction**
  (`cleanup.policy=compact`) mantém o **último valor por chave** (com *tombstones* para deletar).
- **Tiered storage** (KIP-405): segmentos antigos vão para object storage barato; retenção longa com custo
  menor ([retenção/replay](../../18-message-brokers/05-ordering-retention-replay/README.md)).
- **KRaft**: metadados replicados via **Raft** num quorum de controllers (substitui ZooKeeper); simplifica
  operação e escala de partições.

## 2. Replicação e durabilidade em detalhe

```text
Líder da partição ◄── followers (ISR) buscam (fetch) o log do líder
High Watermark (HW) = offset mais alto replicado a TODAS as ISR → só até o HW é visível ao consumidor
```

- **ISR** (in-sync replicas): réplicas "em dia". `min.insync.replicas` + `acks=all` ⇒ commit exige N réplicas
  ISR; abaixo disso, produtor recebe erro (**prefere consistência a disponibilidade** — CP-ish).
- **`unclean.leader.election.enable`**: se `true`, permite líder **fora do ISR** (disponibilidade, **risco
  de perda**); mantenha `false` para dados críticos.
- **Leader epoch** evita divergência/truncamento incorreto após eleições.
- **Rack awareness** (`broker.rack`): réplicas em zonas/racks diferentes (sobrevive a perda de AZ).
- **Follower fetching** (leitura de réplica local, KIP-392): reduz tráfego inter-AZ/custo.
- Tuning: `replication.factor=3`, `min.insync.replicas=2`, `acks=all`, `replica.lag.time.max.ms`.

## 3. Garantias: idempotência, transações e exactly-once

### Producer idempotente

`enable.idempotence=true`: o broker deduplica por **Producer ID + sequence number** por partição ⇒ sem
duplicatas/reordenação por retries **dentro de uma sessão** (padrão em clients modernos).

### Transações

`transactional.id` permite **escrever atomicamente em várias partições/tópicos** e **commitar offsets de
consumo** na mesma transação (**consume-transform-produce**):

```python
producer.init_transactions()
producer.begin_transaction()
producer.produce("saida", key, value)
producer.send_offsets_to_transaction(offsets, consumer.consumer_group_metadata())
producer.commit_transaction()      # tudo ou nada: saída + offsets
```

- Consumidores usam `isolation.level=read_committed` para **não ver** mensagens de transações abortadas.
- Base do **exactly-once** do [Kafka Streams](../../17-streaming/06-kafka-streams/README.md)
  (`exactly_once_v2`) e de pipelines Flink→Kafka (2PC no sink).
- **Limites**: EOS vale **dentro do Kafka** (tópico→tópico). Para **sinks externos**, exige sink
  **idempotente/transacional** ([delivery semantics](../../17-streaming/04-delivery-semantics/README.md)).
- Custo: latência extra, **coordinator de transações**, *transactional.id* gerido por instância.

## 4. Consumo avançado

- **Consumer groups e rebalanceamento**: protocolo *eager* (stop-the-world) vs **cooperative sticky**
  (incremental); **static membership** (`group.instance.id`) evita rebalanço em reinícios curtos; novo
  **KIP-848** (protocolo de grupos de próxima geração) reduz custos de rebalance — confira disponibilidade.
- **Controle de offsets**: commit manual **após** durabilidade da saída ([at-least-once](../../17-streaming/04-delivery-semantics/README.md));
  `seek`/reset para replay; **`auto.offset.reset`**.
- **Paralelismo**: ≤ nº de partições por grupo; processe **em ordem por partição/chave**; para mais
  paralelismo, **particionar mais** ou usar modelos como *parallel consumer* (cuidado com ordem).
- **Backpressure/lag**: `pause()/resume()`, `max.poll.records`, `max.poll.interval.ms`, autoscaling por lag
  ([backpressure](../../18-message-brokers/06-backpressure/README.md)).
- **Dead Letter Topic + retry topics** (padrão): falha → tópico de retry com delay/backoff → DLQ; consumidor
  idempotente.
- **Seek por timestamp** (`offsetsForTimes`) para replay a partir de um instante.

## 5. Particionamento e design de tópicos

- **Chave/partitioner**: define ordem/skew; partitioner customizado para evitar hot partitions
  (ex.: *salting* de chaves quentes — perde ordem global por chave).
- **Nº de partições**: dimensionar por throughput e paralelismo; **aumentar quebra o mapeamento
  chave→partição**; limite prático por broker/cluster (milhares por broker; KRaft ajuda) — planeje com folga.
- **Compactação vs delete**; **tópicos de estado/changelog**; **tópicos de baixa cardinalidade** (compact).
- **Convenções** de nomes, ACLs, quotas, schema registry por tópico ([contratos](../../29-data-contracts/README.md),
  [Avro](../../08-data-formats/05-avro/README.md)).
- **Tamanho de mensagem**: evite payloads grandes (`message.max.bytes`); use **referência a object storage**
  ([claim check](../../19-cloud/02-object-storage/README.md)).

## 6. Performance e tuning

| Alvo | Alavancas |
| --- | --- |
| **Throughput (producer)** | `batch.size`, `linger.ms`, `compression.type` (`zstd`/`lz4`), `buffer.memory`, múltiplas partições |
| **Latência** | `linger.ms` baixo, `acks`, batch menor, rede/disco rápidos |
| **Durabilidade** | `acks=all`, `min.insync.replicas`, idempotência, `unclean=false` |
| **Consumidor** | `fetch.min.bytes`/`fetch.max.wait.ms`, `max.poll.records`, paralelismo |
| **Broker** | discos (SSD/NVMe), **page cache** grande, rede, `num.io.threads`/`num.network.threads`, JVM/GC (G1/ZGC), `log.segment.bytes` |

Compressão no **producer** (lote) economiza rede/disco; o broker mantém comprimido. Meça **end-to-end**
(p99) — não só throughput.

## 7. Operação em produção

- **Monitoramento essencial**: **consumer lag** (por grupo/partição), **under-replicated partitions**,
  **offline partitions**, ISR shrink/expand, request latency (produce/fetch p99), uso de disco/IO, **controller
  health**, taxa de erros, GC. Ferramentas: Prometheus (JMX exporter), Burrow, Cruise Control, Kafka UI,
  Confluent Control Center ([métricas](../../24-observability/02-metrics/README.md)).
- **Cruise Control**: rebalanceamento automático de partições/líderes por carga; **preferred leader
  election**.
- **Expansão/reassignment** de partições (`kafka-reassign-partitions`) com **throttle** para não saturar.
- **Upgrades rolling** (ordem broker-a-broker, compatibilidade de protocolo/`inter.broker.protocol`);
  **KRaft migration** de ZooKeeper (planejar).
- **Capacidade**: disco = vazão × retenção × RF ÷ compressão + folga; rede (replicação + consumidores).
- **Multi-cluster/DR**: **MirrorMaker 2**, Cluster Linking (Confluent), replicação ativa-ativa/passiva,
  mapeamento de offsets ([DR](../../06-databases/09-backup-recovery-dr/README.md)).
- **Segurança**: TLS, **SASL** (SCRAM/OAUTHBEARER/GSSAPI) ou mTLS, **ACLs** por tópico/grupo, **quotas**
  por cliente, criptografia at-rest (disco), segredos fora do código
  ([segurança](../../26-security/README.md)).
- **Gerenciado vs self-hosted**: Confluent Cloud, **MSK**, Redpanda Cloud, Aiven — reduz operação; avalie
  custo/lock-in/recursos ([cloud](../../19-cloud/README.md)).

## 8. Ecossistema avançado

- **Schema Registry** com política de compatibilidade e **data contracts** (regras/migrações) —
  [compatibilidade](../../29-data-contracts/04-compatibility-versioning/README.md).
- **Kafka Connect** em escala: tasks, DLQ, SMTs, secrets providers, exactly-once source (KIP-618) onde
  suportado ([Connect](../../18-message-brokers/07-kafka-connect/README.md), [Debezium](../01-cdc-debezium/README.md)).
- **Kafka Streams / ksqlDB / Flink** para processamento ([streaming](../../17-streaming/README.md)).
- **Alternativas compatíveis**: **Redpanda** (C++), **WarpStream**/diskless (storage em S3), Pulsar —
  trade-offs de latência/custo/operação.

## Erros comuns

- `acks=1`/`min.insync.replicas=1` em dados críticos; `unclean.leader.election=true` sem entender o risco.
- Sem monitorar lag/URP; descobrir problemas pelo usuário.
- Poucas partições (limita paralelismo) e depois reparticionar quebrando ordem.
- Esperar exactly-once "automático" com sinks externos não-idempotentes.
- Rebalanços em loop (processamento > `max.poll.interval.ms`); sem static membership/cooperative.
- Mensagens gigantes; retenção/disco subdimensionados; sem plano de DR.
- Chaves quentes (skew) e partitioner ignorado.

## Boas práticas

- Durabilidade por padrão (RF=3, `acks=all`, `min.insync=2`, idempotência, `unclean=false`).
- Consumidores idempotentes; commit após durabilidade; DLQ/retry; cooperative rebalancing + static membership.
- Projeto de chaves/partições com folga; schemas com compatibilidade; sem payloads gigantes.
- Observabilidade completa + Cruise Control; upgrades/DR ensaiados; segurança (TLS/SASL/ACL/quotas).
- Considere gerenciado quando o time não for especialista.

## Relação com outros conceitos

- [Módulo 18 (Kafka)](../../18-message-brokers/README.md), [delivery semantics](../../17-streaming/04-delivery-semantics/README.md),
  [Kafka Streams](../../17-streaming/06-kafka-streams/README.md), [CDC](../01-cdc-debezium/README.md),
  [contratos](../../29-data-contracts/README.md), [observabilidade](../../24-observability/README.md).

## Exercícios

1. Explique High Watermark, ISR e o efeito de `min.insync.replicas=2` com `acks=all` numa falha de broker.
2. Implemente (conceitualmente) um consume-transform-produce com transação e `read_committed`.
3. Dimensione partições e disco para 50 MB/s, RF=3, retenção de 7 dias, compressão 3:1.
4. Projete um fluxo de retry topics + DLQ para uma mensagem que falha por indisponibilidade de um sink.

## Referências

- Documentação do Apache Kafka (design, replication, transactions, KRaft, KIPs 405/392/848/618);
  Narkhede et al., *Kafka: The Definitive Guide*; Confluent blog (exactly-once, rebalancing).
