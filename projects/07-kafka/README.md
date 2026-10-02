# Projeto 07 — Kafka: producer → broker → consumer → PostgreSQL

> 🟣 Nível: avançado · Módulos: [18 Message brokers](../../18-message-brokers/README.md),
> [17 Streaming](../../17-streaming/README.md), [09 ETL/ELT (idempotência e falhas)](../../09-etl-elt/07-idempotency-retries/README.md) ·
> Anterior: [Projeto 06](../06-spark/README.md) · Próximo: [Projeto 08](../08-streaming/README.md)

## Objetivo

Construir o caminho clássico de eventos — **producer → Kafka → consumer → banco** — com as propriedades que
distinguem um pipeline de brinquedo de um de produção:

- **semântica de entrega**: *at-least-once* + **destino idempotente** ⇒ efeito *exactly-once* no resultado;
- **ordem por chave** (e por que ela só vale dentro de uma partição);
- **consumer group**, *rebalance* e **falha de consumidor** (crash real, não simulado);
- **DLQ** (*dead-letter queue*) para mensagens-veneno, sem travar o fluxo;
- **lag** como métrica de saúde, **commit manual** de offsets e **commit síncrono depois do destino**.

## Arquitetura

```text
 produtor (confluent-kafka)                  Kafka (KRaft, 1 broker)                     consumidores (grupo "orders-sink")
 enable.idempotence=true, acks=all   ┌────────────────────────────────────┐   ┌──────────────────────────────────────────────┐
 chave = order_id  ───────────────►  │ orders.events        6 partições   │──►│ A ─┐   poll → parse/valida                       │
 (eventos + mensagens-veneno)        │  p0 p1 p2 p3 p4 p5   (log + offsets)│   │ B ─┴─►  inválida ─► DLQ (flush) ─────────────┼─► orders.events.dlq
                                     └────────────────────────────────────┘   │         válidas ─► PostgreSQL (1 transação)   │   (headers: erro + origem)
                                                                              │         só ENTÃO commit síncrono do offset    │
                                                                              └──────────────────┬───────────────────────────┘
                                          PostgreSQL ◄─────────────────────────────────────────────┘
                                          order_events  (PK event_id = "order_id-seq")  histórico imutável, ON CONFLICT DO NOTHING
                                          orders_current (PK order_id)                  estado atual: só AVANÇA (WHERE seq novo > seq atual)
```

### O contrato da ordem de operações (o coração do projeto)

```text
 1. parse/validação      inválida → DLQ (headers: error, source=topic:partição:offset)
 2. flush da DLQ         a DLQ precisa estar durável ANTES de o offset avançar
 3. escrita no destino   1 transação; idempotente (event_id + seq)
 4. commit do offset     síncrono, SÓ DEPOIS de 2 e 3
```

| Se o processo morre… | Resultado | Por quê |
| --- | --- | --- |
| antes do passo 3 | lote **reentregue**, gravado normalmente | nada foi gravado nem commitado |
| **entre 3 e 4** | lote **reentregue**, reaplicado **sem duplicar** | destino idempotente absorve (é o cenário do demo) |
| (hipótese errada) *commit antes de gravar* | dado **perdido** para sempre | offset já avançou, gravação nunca ocorreu |

> Por isso a escolha é **"pode repetir, nunca pode perder"** (*at-least-once*) + idempotência — e não
> *at-most-once*. *Exactly-once* fim a fim existe (transações Kafka) mas só dentro do ecossistema Kafka;
> para um banco externo, idempotência é a solução prática ([delivery semantics](../../17-streaming/04-delivery-semantics/README.md)).

## Requisitos

Docker + Compose, Python ≥ 3.11 (`confluent-kafka`, `psycopg`). Portas configuráveis (a 5432 costuma estar ocupada):

```bash
export KAFKA_PORT=9092 POSTGRES_PORT=5432      # ajuste se necessário
```

## Estrutura

```text
07-kafka/
├── docker-compose.yml           # Kafka 3.9 em modo KRaft (sem ZooKeeper) + PostgreSQL 16
├── sql/init.sql                 # order_events (histórico) + orders_current (estado) com constraints
├── src/kpipe/
│   ├── events.py                # contrato do evento, geração determinística, parse/validação, gabarito
│   ├── producer.py              # idempotente, acks=all, lz4, backpressure (BufferError), veneno injetável
│   ├── consumer.py              # commit manual, cooperative-sticky, session.timeout 10 s
│   ├── pipeline.py              # o loop: valida → DLQ → destino → commit  (com gancho de falha)
│   ├── sink.py                  # PostgresSink idempotente (transação única)
│   ├── admin.py                 # tópicos, lag por partição, leitura da DLQ
│   └── cli.py                   # topics | produce | consume | lag | report | demo
└── tests/                       # 25 unitários (sem infra) + 6 de integração (Kafka + PG reais)
```

## Execução

```bash
cd projects/07-kafka
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
docker compose up -d                                  # aguarde o healthcheck (~15 s)
export PYTHONPATH=src KAFKA_BOOTSTRAP=localhost:${KAFKA_PORT:-9092} \
       PG_DSN=postgresql://de:de@localhost:${POSTGRES_PORT:-5432}/sink

# DEMO COMPLETO (autoverificável; sai com código != 0 se algum check falhar)
python -m kpipe demo

# passo a passo, à mão
python -m kpipe produce --orders 1000 --poison 5     # eventos de 1000 pedidos + 5 mensagens-veneno
python -m kpipe consume --group orders-sink --name A # (outro terminal: --name B) → divisão de partições
python -m kpipe lag --group orders-sink              # lag por partição
python -m kpipe report --orders 1000                 # destino × gabarito calculado dos eventos
docker compose down -v
```

Saída verificada do `demo` (1500 pedidos → 5117 mensagens; consumidor A **morre de verdade** — `os._exit` —
entre gravar e commitar):

```text
== 3. dois consumidores, mesmo grupo; o 'A' morre no lote 2 (antes do commit) ==
   [A +  0.1s] ATRIBUÍDAS: [0, 1, 2, 3, 4, 5]
   [A +  0.1s] REVOGADAS: [0, 1, 2]                       ← B entrou no grupo: rebalance incremental (cooperative-sticky)
   [A +  3.1s] REVOGADAS: [3, 4, 5]                       ← A morreu; sem close(), sem commit
   [B + 63.1s] ATRIBUÍDAS: [0, 1, 2, 3, 4, 5]             ← B assume tudo
   B processou: {'dlq': 7, 'messages': 5117, 'inserted': 4912, 'duplicates_ignored': 198, 'state_updates': 2370, 'stale_ignored': 78}
== 4. verificações ==
   ✔ o consumidor A realmente morreu (exit != 0)
   ✔ todos os eventos válidos estão no destino
   ✔ nenhum evento duplicado no destino
   ✔ estado atual de TODOS os pedidos correto
   ✔ houve REENTREGA (lote do crash reprocessado) e foi absorvida          ← duplicates_ignored = 198
   ✔ DLQ recebeu as 7 mensagens-veneno (distintas por origem)
   ✔ lag final = 0
   DLQ: 9 mensagens (7 distintas — a diferença são reentregas) · motivos: {'empty_payload': 2, 'invalid_json': 2, 'missing_field:amount': 1, 'unknown_status': 1, 'unsupported_schema_version:99': 1}
```

Leia com atenção três linhas:

- **`duplicates_ignored: 198`** — o lote que A gravou e não commitou foi **reentregue** a B e absorvido pelo
  `ON CONFLICT DO NOTHING` (≈ um lote de 200). Sem idempotência, seriam 198 pedidos duplicados.
- **`stale_ignored: 78`** — pedidos cujo evento reentregue **não** era mais novo que o estado atual: o `WHERE seq > atual`
  protege o estado contra reentrega *e* contra evento fora de ordem.
- **DLQ com 9 mensagens (7 distintas)** — a **DLQ também é *at-least-once***: o lote reentregue reenviou os
  venenos dele. Quem consome a DLQ precisa deduplicar (aqui, pelo header `source = tópico:partição:offset`).

> ⏱️ **Sobre o tempo (3 min no meu ambiente)**: o *rebalance* após a morte de um consumidor deveria levar
> ~`session.timeout.ms` (10 s). No meu WSL2 o **relógio do sistema oscilava ±54 s a cada 5 s** (`systemd-timesyncd`
> brigando com a sincronização do Hyper-V: `timedatectl` mostra *System clock synchronized: no* e o `dmesg` *"Time
> jumped backwards"*), o que estica todos os *timeouts* do Kafka — até um laço Python puro com `sleep(0.2)` via
> "travadas" de 54 s. **Não é o código**: os mesmos testes passam, só devagar. Veja *Troubleshooting*.

## Testes

```bash
pytest -q -m "not integration"                          # 25 testes, 0,1 s, sem Docker
KAFKA_BOOTSTRAP=localhost:9092 PG_DSN=postgresql://de:de@localhost:5432/sink pytest -q -m integration
#   6 testes de integração com Kafka e PostgreSQL REAIS (tópicos/grupos únicos por teste)
```

| Grupo | O que garante |
| --- | --- |
| **Contrato do evento** | *roundtrip*; **14 formas de lixo** → cada uma com **motivo explícito** (JSON truncado, payload vazio, versão de schema, campo ausente, `seq` inválido incl. `True`/`"1"`, status, valor negativo/`NaN`, timestamp); gerador determinístico, em ordem de tempo, `seq` de 1 em 1 por pedido |
| **Ordem das operações (fakes)** | a sequência é exatamente `dlq.flush → sink.write → commit`; offset commitado = **último + 1 por partição**; commit **síncrono**; falha do destino ⇒ **sem commit**; falha *entre gravar e commitar* ⇒ offsets intactos; `PARTITION_EOF` ignorado e demais erros **propagam** |
| **DLQ** | veneno vai para `t.dlq` com a **mesma chave/valor**, e headers `error` e `source`; o resto do lote segue |
| **Integração — ponta a ponta** | destino == gabarito, 5 venenos na DLQ com header, **lag = 0** |
| **Integração — crash** | morre entre gravar e commitar ⇒ meio gravado; reinício do grupo ⇒ completo, **0 duplicatas**, `duplicates_ignored > 0` |
| **Integração — ordem** | todo evento de um pedido veio da **mesma partição** e em `seq` crescente |
| **Integração — sink** | **idempotente** (reenvio: 0 inseridos); evento antigo **tardio** não regride o estado; transação **tudo-ou-nada** (violação de `CHECK` desfaz o lote inteiro) |

## Decisões arquiteturais e trade-offs

- **Chave = `order_id`**: a ordem do Kafka vale **por partição**; a mesma chave → mesma partição, então os
  eventos de um pedido chegam em ordem. Custo: pedidos "quentes" concentram carga (*hot partition*) — mesmo
  problema de skew do [Projeto 06](../06-spark/README.md). Não há ordem **global** entre pedidos
  ([ordenação e partições](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md)).
- **6 partições** = teto de paralelismo do grupo (mais consumidores que partições ficam ociosos) e muito
  difícil de reduzir depois; aumentar **muda** o mapeamento chave→partição (quebra a ordem histórica).
- **Idempotência por chave natural (`order_id-seq`)** em vez de UUID gerado pelo producer: reenvios do
  mesmo evento colidem *por construção*. Custo: o produtor precisa de um `seq` confiável por pedido.
- **Estado "só avança" (`WHERE EXCLUDED.seq > seq`)**: robusto a reentrega **e** a evento fora de ordem; o
  histórico (`order_events`) mantém tudo, o estado é derivado. É o padrão *event log + materialized state*.
- **Commit manual e síncrono, por lote, depois do destino**: mais lento que `enable.auto.commit` (que commita
  por tempo, *antes* de saber se você processou ⇒ pode **perder**), mas é o que dá a garantia. Lotes maiores
  amortizam o custo do commit; lotes menores reduzem o reprocessamento após uma falha — um *knob* real.
- **DLQ em vez de "pular" ou "travar"**: veneno não pode bloquear a partição (*head-of-line blocking*) nem
  sumir. Mantém-se o payload **original** + motivo + coordenadas — dá para reprocessar depois de corrigir.
  Em produção, alerte quando a DLQ crescer ([observabilidade](../../24-observability/README.md)).
- **Producer idempotente (`enable.idempotence`, `acks=all`)** evita duplicatas causadas por *retries* do próprio
  producer; **não** evita o produtor *reenviar* o mesmo evento por lógica de aplicação — por isso o destino
  também é idempotente (defesa em camadas).
- **`cooperative-sticky`**: rebalance incremental (só as partições que mudam de dono param), em vez do *stop-the-world*
  do `range`. Você vê no log: A perde `[0,1,2]` quando B entra, **sem** parar `[3,4,5]`.
- **1 broker, replicação 1** e `PLAINTEXT`: **só estudo**. Produção: ≥ 3 brokers, `replication.factor=3`,
  `min.insync.replicas=2`, TLS/SASL e ACLs ([segurança](../../26-security/README.md)).
- **Esquema em JSON com `schema_version`**: simples e legível; sem *schema registry* não há compatibilidade
  garantida. Evolução: Avro/Protobuf + Schema Registry ([formatos](../../08-data-formats/05-avro/README.md),
  [contratos](../../29-data-contracts/README.md)).
- **Por que PostgreSQL como destino**: mostra a parte difícil (transação + idempotência) sem outra tecnologia.
  Para volume alto, o destino natural é um lake/warehouse via **Kafka Connect** ([Connect](../../18-message-brokers/07-kafka-connect/README.md)).

## Troubleshooting

- **Rebalance/ocioso demorando minutos e `time.time()` "pulando"** — relógio do WSL2/VM instável. Diagnóstico:
  `timedatectl` (*synchronized: no*), `dmesg | tail` (*Time jumped backwards*). Correção (Windows, PowerShell):
  `wsl --shutdown`; dentro do WSL: `sudo systemctl disable --now systemd-timesyncd` (deixa só a sincronização do
  Hyper-V). O mesmo problema derruba tokens JWT do Airflow no [Projeto 03](../03-orchestration/README.md).
- **`Connection refused` / `Broker: Coordinator load in progress`** nos primeiros segundos — o broker ainda
  inicia; espere o *healthcheck* (`docker compose ps`).
- **Porta ocupada** — `KAFKA_PORT=9192 POSTGRES_PORT=5437 docker compose up -d` e ajuste `KAFKA_BOOTSTRAP`/`PG_DSN`.
  O `ADVERTISED_LISTENERS` usa a mesma `KAFKA_PORT`: o cliente precisa alcançar **o endereço anunciado**, não só o
  endereço de bootstrap (erro clássico de Kafka em Docker).
- **Tópico "preso" depois de apagar** — `python -m kpipe demo` já espera a remoção terminar antes de recriar.

## Possíveis melhorias (exercícios)

1. **Escalar**: suba 3 consumidores (`--name A/B/C`) e observe a divisão `[0,1] [2,3] [4,5]`; mate um com `kill -9`.
2. **Backpressure**: faça o destino lento (`pg_sleep`) e acompanhe o **lag** crescer (`kpipe lag`); depois ajuste `--batch-size`.
3. **Hot key**: faça 40% dos eventos de um único `order_id`/cliente e meça o desbalanceamento por partição.
4. **Transações Kafka**: consuma-processa-produza para um tópico derivado com `transactional.id` (*exactly-once* dentro do Kafka).
5. **Schema Registry + Avro**: troque o JSON; quebre a compatibilidade de propósito e veja o produtor falhar.
6. **Outbox / CDC**: em vez de o produtor "falar com o Kafka", leia a tabela de pedidos com Debezium ([módulo 30](../../30-advanced/01-cdc-debezium/README.md)).
7. **Reprocessamento (*replay*)**: apague o destino e **reposicione** o grupo (`kafka-consumer-groups.sh --reset-offsets --to-earliest`, dentro do contêiner) — a retenção do tópico é o limite.
8. **Métricas**: exporte lag e taxa de DLQ para o Prometheus (padrão do [Projeto 04](../04-data-quality/README.md)) e crie alertas.
9. Alimente o **Projeto 08** (streaming) com este tópico.

## Referências

- [Apache Kafka — documentação](https://kafka.apache.org/documentation/) (consumer groups, delivery semantics, KRaft) ·
  [confluent-kafka-python](https://docs.confluent.io/kafka-clients/python/current/overview.html) ·
  [librdkafka CONFIGURATION](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md).
- Kleppmann, *Designing Data-Intensive Applications* (cap. 11, *stream processing*); módulos
  [18](../../18-message-brokers/README.md) e [17](../../17-streaming/README.md).
