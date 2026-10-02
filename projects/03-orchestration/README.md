# Projeto 03 — Orquestração com Apache Airflow

> 🔵 Nível: intermediário · Módulos: [10 Data Pipelines](../../10-data-pipelines/README.md),
> [11 Orquestração](../../11-orchestration/README.md), [09 ETL/ELT](../../09-etl-elt/README.md) ·
> Anterior: [Projeto 02](../02-analytics-warehouse/README.md) · Próximo: [Projeto 04](../04-data-quality/README.md)

## Objetivo

Colocar um pipeline sob **orquestração real**: um DAG diário **idempotente**, **particionado pela data
lógica**, com **retries**, **gate de qualidade**, **checks pós-carga** e **backfill** — rodando em Airflow 3
(LocalExecutor) com PostgreSQL. O foco é o que um orquestrador realmente resolve (dependências, retries,
agendamento, backfill, observabilidade) e o que **não** deve fazer (transformar dados).

## Arquitetura

```text
                       ┌──────────────── Airflow 3 (api-server · scheduler · dag-processor) ────────────────┐
   data lógica D  ───► │ extract ─► validate ─► load ─► quality_checks ─► publish_summary                     │
 (intervalo [D, D+1))  └──┬─────────┬───────────┬──────────┬──────────────────┬────────────────────────────┘
                          │         │           │          │                  │
                  data/raw/orders/  gate:       DELETE+INSERT   4 checks SQL   upsert
                  dt=D/orders.csv   rejeição>10% da partição D  (falham o DAG)  daily_summary
                  (atômico)         ⇒ FALHA     (1 transação)
                                    (sem retry)                          PostgreSQL ("warehouse"): orders_daily · daily_summary · pipeline_runs
```

| Peça | Responsabilidade |
| --- | --- |
| [`dags/orders_daily.py`](dags/orders_daily.py) | **só orquestra**: ordem, retries, parâmetros, data lógica |
| [`include/orders_lib.py`](include/orders_lib.py) | **toda a lógica** (geração, validação, escrita atômica, resumo) — **pura**, testada sem Airflow |
| [`sql/init_warehouse.sql`](sql/init_warehouse.sql) | tabelas do warehouse (criadas na subida do Postgres) |
| `docker-compose.yml` | Postgres + Airflow (`api-server`, `scheduler`, `dag-processor`) |

## Requisitos

Docker + Compose. (Os testes da biblioteca rodam no host com `pytest`; os do DAG rodam no contêiner.)

## Estrutura

```text
03-orchestration/
├── docker-compose.yml · Dockerfile · .env.example
├── dags/orders_daily.py          # o DAG (TaskFlow API, Airflow 3 SDK)
├── include/orders_lib.py         # lógica pura e testável
├── sql/init_warehouse.sql
└── tests/                        # test_orders_lib.py (host) · test_dag_integrity.py (contêiner)
```

## Execução

```bash
cd projects/03-orchestration
mkdir -p data                              # volume dos arquivos de partição (evita criação como root)
export AIRFLOW_UID=$(id -u)                # o contêiner escreve com o seu UID
# (se a 8080 estiver ocupada: export AIRFLOW_PORT=8089)
docker compose up -d --build
# UI: http://localhost:8080  (auth simplificada, só local) — aguarde ~30s

# rodar o DAG para UMA data lógica, direto no terminal (sem depender do scheduler):
docker compose exec airflow-scheduler airflow dags test orders_daily 2024-01-15

# idempotência: rode de novo — o resultado é idêntico
docker compose exec airflow-scheduler airflow dags test orders_daily 2024-01-15

# o gate de qualidade: 50% de linhas sujas ⇒ o DAG FALHA e NADA é carregado
docker compose exec airflow-scheduler airflow dags test orders_daily 2024-01-20 \
  --conf '{"dirty_rate": 0.5}'

# BACKFILL (o scheduler executa os runs; max_active_runs=1 limita a concorrência)
docker compose exec airflow-scheduler airflow dags unpause orders_daily
docker compose exec airflow-scheduler airflow backfill create \
  --dag-id orders_daily --from-date 2024-03-01 --to-date 2024-03-04

# conferir o warehouse
docker compose exec postgres psql -U de -d warehouse \
  -c "select order_date, count(*) from orders_daily group by 1 order by 1;" \
  -c "select * from daily_summary order by 1;"

docker compose down -v                     # limpa tudo
```

Saída verificada (dados sintéticos determinísticos):

```text
extract:  200 linhas em .../raw/orders/dt=2024-01-15/orders.csv
validate: {'rows_read': 200, 'rows_valid': 195, 'rows_rejected': 5} (taxa=2.5%)
load:     partição 2024-01-15 recarregada com 195 linhas      ← idêntico na 2ª execução
quality[tem_linhas|chave_unica|sem_valor_negativo|contagem_bate_com_a_carga]: OK
summary:  {'order_date': '2024-01-15', 'orders': 195, 'revenue': 52097.2}

dirty_rate=0.5  ⇒  AirflowFailException: taxa de rejeição 46.5% > 10%   →  0 linhas carregadas
backfill 03-01..03-04 ⇒ 4 partições (03-01 … 03-04), todas `success`
```

## Testes

```bash
# lógica pura — no host, sem Airflow, sem banco (9 testes)
python -m venv .venv && source .venv/bin/activate && pip install pytest
pytest -q

# integridade do DAG — dentro do contêiner (importa sem erro, estrutura e ordem das dependências)
docker compose exec airflow-scheduler python -m pytest /opt/airflow/tests -q
# (também: docker compose exec airflow-scheduler airflow dags list-import-errors)
```

| Teste | Garante |
| --- | --- |
| geração determinística por data | extract **idempotente** (mesmos bytes ao reexecutar) |
| escrita atômica | arquivo anterior **intacto** se a escrita falha; sem `.tmp` órfão |
| validação | **nenhuma linha some** (`válidas + rejeitadas = lidas`); motivos explícitos; duplicata e data errada |
| integridade do DAG | imports ok, 5 tasks, `max_active_runs=1`, ordem topológica correta |

## Conceitos aplicados (e onde estudar)

- **Data lógica, nunca `now()`** — cada run processa a partição do *seu* intervalo
  ([scheduling](../../10-data-pipelines/03-scheduling/README.md)).
- **Idempotência**: caminho determinístico + escrita atômica; `DELETE`+`INSERT` por partição numa transação;
  resumo por *upsert* ([idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Falha permanente vs transitória**: `AirflowFailException` (dado ruim → retry não ajuda) vs `retries=2`
  (falha de infra) ([handling failures](../../09-etl-elt/11-handling-failures/README.md)).
- **Orquestre, não transforme**; passe **referências** (caminho/contagens) por XCom, nunca dados
  ([Airflow](../../11-orchestration/02-airflow/README.md)).
- **Gate de qualidade** antes e depois da carga ([validação](../../09-etl-elt/10-data-validation/README.md)).

## Decisões arquiteturais e trade-offs

- **`CronDataIntervalTimetable` em vez do `schedule="@daily"` padrão do Airflow 3.** O cron "pontual" padrão
  tem `data_interval_start == data_interval_end`; um run das 00:00 do dia 2 teria partição do dia 2 — **ainda
  sem dados**. Com `CronDataIntervalTimetable("0 0 * * *")` o run das 00:00 do dia 2 processa o **dia 1
  completo** (verificado: o run agendado automático processou "ontem"). *Em runs manuais* (`dags test`) o
  intervalo é pontual e a partição é a data informada.
- **`catchup=False` + `airflow backfill create`**: backfill é uma ação *explícita e controlada*, não efeito
  colateral de ativar o DAG (evita centenas de runs acidentais) — ver [backfill](../../09-etl-elt/08-backfill/README.md).
- **`max_active_runs=1`**: evita sobreposição entre runs/partições; custo: backfill sequencial.
- **Tabela `pipeline_runs` é *append*** (auditoria de cada tentativa), propositalmente não-idempotente; as
  tabelas de dados, sim.
- **LocalExecutor**: simples e suficiente aqui; em produção, CeleryExecutor/KubernetesExecutor
  ([Kubernetes](../../21-kubernetes/README.md)).
- **Autenticação simplificada** (`ALL_ADMINS`) e segredos de exemplo: **somente estudo local**.
- **Dados sintéticos gerados no `extract`** (para ser autocontido). Em produção, o `extract` leria de uma API/
  banco/arquivos e a partição de saída seria o *raw* imutável ([medallion](../../14-data-lake/03-medallion-architecture/README.md)).

## Troubleshooting

- **Tasks presas em `running` e erro `Invalid auth token: The token is not yet valid (iat)`** — o relógio do
  WSL2/VM **saltou** (comum após suspender/hibernar o Windows) e o JWT da *Execution API* foi rejeitado. O
  Compose já usa `AIRFLOW__API_AUTH__JWT_LEEWAY=300`; se persistir: `wsl --shutdown` (no Windows) ou
  `sudo hwclock -s` e `docker compose down -v && docker compose up -d`.
- **`PermissionError` em `data/`** — rode `mkdir -p data` e `export AIRFLOW_UID=$(id -u)` **antes** do
  `docker compose up` (senão o Docker cria o diretório como `root`).
- **Porta 8080 ocupada** — `export AIRFLOW_PORT=8089`.
- **DAG não aparece** — `docker compose exec airflow-scheduler airflow dags list-import-errors`.

## Possíveis melhorias (exercícios)

1. Adicionar um **Sensor** que espera o arquivo da fonte antes do `extract` (e `timeout`/`poke_interval`).
2. **Asset/Dataset-aware scheduling**: um segundo DAG (`orders_marts`) disparado quando `orders_daily` atualiza.
3. **`on_failure_callback`** que notifica (Slack/e-mail) e **SLA** por task ([alertas](../../24-observability/04-alerting/README.md)).
4. Trocar o `extract` por uma **API real** com paginação/retry (reuse o código do [Projeto 01](../01-basic-etl/README.md)).
5. Disparar o **dbt** do [Projeto 02](../02-analytics-warehouse/README.md) após o `load` (`BashOperator`/Cosmos).
6. **KubernetesExecutor** / `KubernetesPodOperator` e *dynamic task mapping* para processar N partições em paralelo.
7. Exportar métricas (Prometheus/StatsD) e montar um dashboard de SLA de frescor
   ([observabilidade de pipelines](../../10-data-pipelines/08-pipeline-observability/README.md)).

## Referências

- [Documentação do Apache Airflow 3](https://airflow.apache.org/docs/apache-airflow/stable/) — Timetables, Backfill, TaskFlow, Task SDK.
- Módulos [10](../../10-data-pipelines/README.md) e [11](../../11-orchestration/README.md); Reis & Housley, *Fundamentals of Data Engineering* (cap. orquestração).
