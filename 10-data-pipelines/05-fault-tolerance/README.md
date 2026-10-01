# Fault tolerance

> 🔵 Pipelines · Parte de [10 — Data Pipelines](../README.md)

## O que é

**Tolerância a falhas** é a capacidade de um pipeline continuar correto e recuperável apesar
de falhas de componentes (rede, nós, dependências, dados ruins). No nível do pipeline/
orquestração, isso se traduz em retries, retomada por checkpoint, atomicidade, isolamento de
falhas e degradação graciosa. (O tratamento de falhas no nível de ETL está em
[handling failures](../../09-etl-elt/11-handling-failures/README.md); aqui é a visão de
pipeline/sistema distribuído.)

## Por que falhas são a norma

Quanto mais partes móveis (fontes, [brokers](../../18-message-brokers/README.md), clusters,
armazenamentos), maior a chance de **falha parcial** — algo falha enquanto o resto segue (ver
[sistemas distribuídos](../../01-foundations/05-distributed-systems-fundamentals/README.md)).
Um pipeline de produção que roda por anos **vai** encontrar todas elas. Projete assumindo
falha.

## Mecanismos no nível do pipeline

### Retries por tarefa

Orquestradores ([Airflow](../../11-orchestration/02-airflow/README.md)/Dagster/Prefect)
retentam tarefas individuais automaticamente (com backoff). Seguro **se** a tarefa for
[idempotente](../04-checkpoints-idempotency/README.md). Configure para transitórios; não
retente permanentes (ver [handling failures](../../09-etl-elt/11-handling-failures/README.md)).

### Isolamento de falhas (blast radius)

Uma tarefa que falha não deve derrubar o pipeline inteiro quando não precisa. Com um
[DAG](../02-dags-dependencies/README.md), só os ramos **dependentes** da tarefa falha ficam
bloqueados; ramos independentes continuam. Projete para limitar o "raio de explosão".

### Retomada por checkpoint

Jobs longos retomam do último [checkpoint](../04-checkpoints-idempotency/README.md) em vez de
recomeçar.

### Atomicidade

Escrita tudo-ou-nada (staging+swap, transação, lakehouse) evita estado parcial após crash
(ver [loading](../../09-etl-elt/04-loading/README.md)).

### Redundância e failover

Em sistemas distribuídos, [replicação](../../06-databases/07-replication/README.md) e
múltiplos workers permitem que a queda de um nó não pare o processamento (um executor Spark
cai → a tarefa é reatribuída a outro).

### Dead letter / quarentena

Dados/mensagens que falham repetidamente são isolados para não travar o fluxo bom (ver
[validação](../../09-etl-elt/10-data-validation/README.md)).

## Como as engines distribuídas toleram falhas

- **[Spark](../../16-distributed-processing/README.md)** — recomputa partições perdidas a
  partir da *lineage* do [RDD/DataFrame](../../16-distributed-processing/08-rdd-dataframe/README.md)
  (sabe como recriar cada pedaço); tarefas que falham são reexecutadas em outro executor.
- **[Kafka](../../18-message-brokers/README.md)** — partições replicadas; consumidores
  retomam por offset.
- **Streaming** — checkpoints de offset+estado garantem recuperação (ver
  [delivery semantics](../../17-streaming/04-delivery-semantics/README.md)).

## Degradação graciosa

Quando possível, degrade em vez de quebrar: servir o último resultado bom, pular uma fonte
opcional indisponível (sinalizando), ou processar parcialmente e marcar o restante. Decida
por caso (às vezes dados parciais são inaceitáveis).

## Dependências upstream e SLAs

Use **sensors** com timeout para fontes que podem atrasar; defina **SLAs** e alerte em
violação (ver [scheduling](../03-scheduling/README.md),
[SLO](../../24-observability/05-sli-slo-sla/README.md)). Não assuma que o upstream está
pronto.

## A base de tudo: idempotência

Nenhum desses mecanismos é seguro sem [idempotência](../04-checkpoints-idempotency/README.md):
retries, retomada e failover **reexecutam** trabalho, e isso só é seguro se reexecutar não
duplicar/corromper. É o pré-requisito universal.

## Erros comuns

- Retry em tarefa não-idempotente → duplicação.
- Uma falha derrubando o pipeline todo (sem isolamento de ramos).
- Sem atomicidade → estado parcial após crash.
- Assumir upstream sempre pronto (sem sensor/SLA).
- Dados ruins travando o fluxo inteiro (sem dead letter).

## Boas práticas

- Idempotência + atomicidade + checkpoints como base.
- Retries para transitórios; isole ramos; dead letter para dados ruins.
- Sensors/SLAs para dependências; alerte em falha/atraso.
- Aproveite a tolerância nativa das engines (Spark lineage, Kafka replicação).

## Relação com outros conceitos

- [Checkpoints/idempotência](../04-checkpoints-idempotency/README.md),
  [handling failures](../../09-etl-elt/11-handling-failures/README.md).
- [Sistemas distribuídos](../../01-foundations/05-distributed-systems-fundamentals/README.md),
  [Spark](../../16-distributed-processing/README.md), [Kafka](../../18-message-brokers/README.md).
- [Observability](../08-pipeline-observability/README.md),
  [incident response](../../24-observability/07-incident-response/README.md).

## Exercícios

1. Projete retries + isolamento de ramos para um DAG onde uma fonte opcional pode falhar.
2. Explique como o Spark recupera uma partição perdida sem recomeçar o job inteiro.
3. Descreva uma estratégia de degradação graciosa para quando uma das 3 fontes está fora.
4. Justifique por que idempotência é pré-requisito de toda tolerância a falhas.

## Referências

- Google SRE Book — confiabilidade e tolerância a falhas.
- Kleppmann, M. *DDIA* — caps. 8–9, 11.
- Documentação de Spark (resiliência) e Airflow (retries).
