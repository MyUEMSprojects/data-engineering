# Scheduling

> 🔵 Pipelines · Parte de [10 — Data Pipelines](../README.md)

## O que é

**Scheduling** (agendamento) é decidir **quando** um pipeline executa. Pode ser por tempo
(todo dia às 2h), por evento (chegou um arquivo), ou por condição (dado upstream pronto).
Parece simples, mas esconde conceitos sutis — sobretudo a **execution date** — que confundem
muita gente.

## Tipos de trigger

| Tipo | Dispara quando | Exemplo |
| --- | --- | --- |
| **Time-driven** | chega o horário | diário às 02:00 ([cron](../../02-linux-shell-environment/06-cron/README.md)) |
| **Event-driven** | um evento ocorre | arquivo chega no S3; mensagem no [Kafka](../../18-message-brokers/README.md) |
| **Sensor/poke** | uma condição é satisfeita | tabela upstream atualizada |
| **Data-aware** | um *dataset/asset* muda | Airflow datasets / Dagster assets |
| **Manual** | alguém aciona | backfill, reprocessamento |

## O conceito crucial: execution date / logical date

Este é o ponto que mais confunde. Em orquestração batch, cada execução está associada a um
**intervalo de dados** (a *data lógica*), que **não é** necessariamente o momento em que o
job roda.

```text
Pipeline diário que processa "o dia anterior":
  roda em 16/jan 02:00  →  processa os dados de 15/jan
  logical_date = 15/jan (o período dos dados), não 16/jan (o relógio)
```

Por quê: o job que roda hoje processa dados de **ontem** (que já estão completos). A *logical
date* identifica **qual partição** está sendo processada — é o que torna o pipeline
**parametrizado por data** e, portanto, **reprocessável** (ver
[backfill](../../09-etl-elt/08-backfill/README.md)).

> No Airflow, isso é `logical_date`/`data_interval`. **Nunca** use `now()` dentro da lógica;
> use a data lógica passada pelo orquestrador — senão backfill e reexecução ficam errados.

## Intervalos e janelas

- O schedule define a **cadência** (diário, horário, `*/15` min) — ver sintaxe em
  [cron](../../02-linux-shell-environment/06-cron/README.md).
- Cada execução cobre um **intervalo** de dados (`[início, fim)`), o que define o que filtrar
  na fonte (`WHERE ts >= início AND ts < fim`).
- **Lookback window** — reprocessar os últimos N intervalos para capturar
  [dados tardios](../../09-etl-elt/05-full-vs-incremental/README.md).

## Catchup e backfill

- **Catchup** — ao ativar um DAG com data de início no passado, o orquestrador pode executar
  todos os intervalos pendentes ("correr atrás"). Ligue/desligue conscientemente (catchup
  acidental pode disparar centenas de runs).
- **Backfill** — reprocessar intervalos passados sob demanda (ver
  [backfill](../../09-etl-elt/08-backfill/README.md)).

## Dependências de tempo vs de dados (prefira dados)

Agendar o pipeline de marts para "3h, porque a ingestão é 2h" é frágil (e se a ingestão
atrasar?). Prefira dependências **de dados/evento**: o de marts roda **quando** a ingestão
terminar com sucesso (sensor/dataset/trigger). Ver
[DAGs/dependências](../02-dags-dependencies/README.md).

## Fuso horário

Defina explicitamente o timezone do schedule (e cuidado com horário de verão). Processe/
armazene em UTC e só apresente em local (ver
[datetime](../../04-python-for-data-engineering/05-stdlib-for-de/README.md)). Ambiguidade de
fuso causa execuções duplicadas/faltantes na virada do DST.

## SLA e atrasos

Defina **SLAs** (ex.: "dados do dia prontos até 6h") e alerte quando um run não terminar no
prazo (ver [SLI/SLO/SLA](../../24-observability/05-sli-slo-sla/README.md)). Um pipeline que
atrasa silenciosamente é tão ruim quanto um que falha.

## Concorrência e sobreposição

Se um run pode durar mais que o intervalo, dois runs podem se sobrepor. Controle com limites
de concorrência (`max_active_runs`) e exclusão mútua (como [flock](../../02-linux-shell-environment/06-cron/README.md)
no cron) — e garanta [idempotência](../04-checkpoints-idempotency/README.md).

## Erros comuns

- Usar `now()` em vez da *logical date* → backfill/reexecução errados.
- Catchup acidental disparando centenas de runs.
- Dependência por horário em vez de por dado (corrida com upstream).
- Ignorar fuso/DST → runs duplicados ou faltantes.
- Runs sobrepostos sem controle de concorrência.
- Sem SLA/alerta de atraso.

## Boas práticas

- Parametrize por *logical date*; processe por intervalo `[início, fim)`.
- Prefira triggers data-aware/sensor a horário fixo para dependências.
- Defina timezone explícito (UTC); controle catchup e concorrência.
- Estabeleça SLAs e alertas de atraso; lookback para dados tardios.

## Relação com outros conceitos

- Base: [cron](../../02-linux-shell-environment/06-cron/README.md);
  executado por [orquestradores](../../11-orchestration/README.md).
- [DAGs/dependências](../02-dags-dependencies/README.md),
  [backfill](../../09-etl-elt/08-backfill/README.md),
  [idempotência](../04-checkpoints-idempotency/README.md).

## Exercícios

1. Explique, com um exemplo, a diferença entre o horário de execução e a *logical date*.
2. Projete o schedule de um pipeline diário que processa o dia anterior, com lookback de 2
   dias.
3. Converta uma dependência "roda às 3h" em uma dependência por sucesso/dataset.
4. Descreva os riscos de catchup e como controlá-los.

## Referências

- Documentação do Airflow — scheduling, `logical_date`, catchup, datasets.
- Dagster — schedules, sensors, auto-materialize.
