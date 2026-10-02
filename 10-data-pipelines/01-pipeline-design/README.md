# Pipeline design

> 🔵 Pipelines · Parte de [10 — Data Pipelines](../README.md)

## O que é

**Pipeline design** é a arte de estruturar o fluxo de dados em **etapas bem definidas,
desacopladas e confiáveis**, da fonte ao consumo. Um bom design torna o pipeline fácil de
entender, testar, operar, reprocessar e evoluir.

## Princípios de um bom pipeline

### 1. Modularidade e separation of concerns

Divida em etapas com **uma responsabilidade** cada: extrair, validar, transformar, carregar.
Etapas desacopladas podem ser testadas, reprocessadas e substituídas isoladamente (ver
[organização](../../03-git-software-engineering/07-project-organization/README.md)).

```text
extract ─► validate ─► transform ─► load   (cada caixa faz uma coisa)
```

### 2. Idempotência

Toda etapa deve poder ser reexecutada sem duplicar/corromper (ver
[idempotência](../../09-etl-elt/07-idempotency-retries/README.md),
[checkpoints](../04-checkpoints-idempotency/README.md)). É o alicerce de retries e backfill.

### 3. Determinismo e parametrização por data

O resultado depende só das entradas e da **data lógica** (parâmetro), não de `now()` ou
estado oculto — essencial para reprocessar o passado (ver
[scheduling](../03-scheduling/README.md), [backfill](../../09-etl-elt/08-backfill/README.md)).

### 4. Preservar o bruto (raw)

Grave o dado como chegou antes de transformar (ver
[medallion](../../14-data-lake/03-medallion-architecture/README.md)) — permite reprocessar
sem re-extrair.

### 5. Camadas de refino

Estruture em camadas (raw → staging → marts) com contratos claros entre elas — cada camada
é mais limpa/modelada que a anterior.

### 6. Observabilidade e qualidade embutidas

Logs, métricas, validação e alertas fazem parte do design, não são "extras" (ver
[observability](../08-pipeline-observability/README.md),
[validação](../../09-etl-elt/10-data-validation/README.md)).

## Topologias de pipeline

- **Linear** — A → B → C (simples, sequencial).
- **Fan-out/fan-in** — uma etapa alimenta várias em paralelo, que depois convergem (ver
  [DAGs](../02-dags-dependencies/README.md)).
- **Branching condicional** — caminhos diferentes conforme condições.
- **Batch vs streaming** — ver [batch vs streaming](../../01-foundations/06-batch-vs-streaming/README.md).

## Push vs pull / event-driven vs scheduled

- **Scheduled (time-driven)** — roda por horário ([cron](../../02-linux-shell-environment/06-cron/README.md)/
  orquestrador). Simples, previsível. Padrão em batch.
- **Event-driven** — dispara quando algo acontece (arquivo chega, evento no
  [Kafka](../../18-message-brokers/README.md)). Menor latência, mais reativo.
- **Sensor/trigger** — espera uma condição (dado pronto) para então rodar.

## Acoplamento e contratos

Reduza o acoplamento entre produtores e consumidores com **contratos** claros (schema,
frescor, garantias — ver [data contracts](../../29-data-contracts/README.md)). Uma mudança
numa etapa não deve quebrar as outras surpreendentemente.

## Design para reprocessamento

Assuma que você **vai** reprocessar (bug, backfill, dados tardios). Projete para isso desde o
início: idempotência + parametrização por data + preservar o raw + overwrite por partição.
Isso é mais barato que "consertar depois".

## Simplicidade primeiro (KISS)

Não comece com Kafka + Spark + lake para um relatório diário de 10 MB. Comece simples
(script + banco, ou dbt + warehouse) e adicione complexidade quando um problema real exigir.
Complexidade prematura é dívida garantida.

## Anti-padrões

- **Script monolítico** que extrai, transforma e carrega tudo num bloco (impossível de
  testar/reprocessar parcialmente).
- **Pipeline não-idempotente** (reexecutar duplica).
- **Lógica acoplada ao I/O** (não testável).
- **Sem observabilidade** (falhas/degradações invisíveis).
- **Over-engineering** (streaming/distribuído sem necessidade).
- **Dependência de ordem implícita** (não declarada no DAG).

## Erros comuns

- Projetar o "caminho feliz" e esquecer falhas/reprocessamento.
- Misturar responsabilidades numa etapa só.
- `now()` embutido impedindo backfill.
- Acoplar etapas sem contrato (mudança quebra tudo).

## Boas práticas

- Modular, idempotente, determinístico, parametrizado por data.
- Camadas (raw→staging→marts); preserve o raw.
- Observabilidade e validação por design.
- Comece simples; evolua conforme a necessidade real.

## Relação com outros conceitos

- Implementa [ETL/ELT](../../09-etl-elt/README.md); orquestrado em
  [orquestração](../../11-orchestration/README.md).
- [DAGs](../02-dags-dependencies/README.md), [idempotência](../04-checkpoints-idempotency/README.md),
  [observability](../08-pipeline-observability/README.md).

## Exercícios

1. Reprojete um script monolítico de ETL em etapas modulares e idempotentes.
2. Desenhe a topologia (linear/fan-out) de um pipeline que ingere 3 fontes e gera 2 marts.
3. Liste as decisões de design que tornam um pipeline "reprocessável".
4. Dê um exemplo de over-engineering e a versão simples adequada.

## Referências

- Reis & Housley, *Fundamentals of Data Engineering* — arquitetura de pipelines.
- Documentação de Dagster (software-defined assets) e Airflow.
