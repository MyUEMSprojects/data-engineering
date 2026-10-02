# Projeto 10 — Capstone: do dado bruto ao dashboard, com engenharia de verdade

> 🟣 Nível: avançado · Combina **todos** os módulos — em especial [15 Lakehouse](../../15-lakehouse/README.md),
> [13 Warehouse/ELT](../../13-data-warehouse/README.md), [11 Orquestração](../../11-orchestration/README.md),
> [12 Data Quality](../../12-data-quality/README.md), [24 Observabilidade](../../24-observability/README.md),
> [23 CI/CD & DataOps](../../23-cicd-dataops/README.md) · Anterior: [Projeto 09](../09-cloud/README.md)

## Objetivo

Reunir, num único pipeline que **roda de ponta a ponta**, o que os nove projetos anteriores mostraram isoladamente:

```text
 fonte (API simulada) ─► raw imutável ─► BRONZE (Delta) ─► GATE de qualidade ─► SILVER (Delta, MERGE ACID) ─► GOLD (ELT em SQL/DuckDB)
                                              │ quarentena (Delta)        │ bloqueia o lote inteiro               │
                                              ▼                           ▼                                       ▼
                              _ops/reports/<ds>.json          métricas Prometheus + 5 alertas ──► CI/CD (lint · testes · imagem · demo · promtool · DAG)
                                 orquestrado por um DAG do Airflow 3 (ingest → gate → silver → gold → observe)
```

| Etapa do enunciado | Onde está | Prova (verificada) |
| --- | --- | --- |
| **Ingestão** | `steps.ingest` — landing zone **imutável** (`raw/…/extract-<sha>.jsonl`) + bronze Delta particionada por `ds` | reexecutar não duplica e não reescreve o arquivo |
| **Lakehouse** | tabelas **Delta Lake** (`deltalake`/delta-rs): ACID, *schema enforcement*, **time travel**, **restore** | `MERGE` idempotente; schema errado é **recusado**; rollback testado |
| **ELT** | `steps.gold` — SQL (DuckDB) sobre a silver → 3 tabelas gold (Delta) | receita gold == receita esperada (gabarito independente) |
| **Orquestração** | `dags/capstone_daily.py` (Airflow 3, TaskFlow) | **parseado** no Airflow 3.0: 5 tasks, `max_active_runs=1`, `observe` com `all_done` |
| **Qualidade** | `quality.py` — 3 checks *hard* + 2 *soft*, quarentena com motivo | dia com 13% de lixo **bloqueado** (exit 2) e silver/gold intactos |
| **Observabilidade** | `metrics.py` + `monitoring/alerts.yml` | `promtool` OK; lote bloqueado dispara `GateBlocked`, `RejectRateHigh`, `RunFailed` no Prometheus |
| **CI/CD** | `.github/workflows/capstone.yml` + `projects.yml` + `Makefile` + `Dockerfile` | `actionlint` limpo; `make lint test alerts` e a imagem rodam local |

> O capstone **não** reimplementa tudo do zero: reaproveita os *padrões* (gate e quarentena do Projeto 04, idempotência e
> MERGE dos 01/05, orquestração do 03, métricas do 04, IaC do 09). Para a versão em nuvem, o `LAKE` aponta para `s3://…`
> (ver [Projeto 09](../09-cloud/README.md)); para escala, a silver/gold viram jobs Spark ([Projeto 06](../06-spark/README.md)).

## Arquitetura em detalhe

| Camada | Tabela | Chave / partição | Regra |
| --- | --- | --- | --- |
| landing | `raw/orders/ds=D/extract-<sha>.jsonl` | por dia | **nunca** sobrescrita; o hash do conteúdo no nome |
| bronze | Delta `bronze/orders` | `_ingest_ds` | linha **crua** + `_source_file`, `_line_no`, `_ingested_at`; `replaceWhere` por partição ⇒ reexecução idempotente |
| quarentena | Delta `quarantine/orders` | `ds` | linha original + **motivo** + arquivo/linha de origem |
| silver | Delta `silver/orders` | `order_id` | `MERGE … WHEN MATCHED AND s.updated_at > t.updated_at` — **só avança**; reentrega e evento tardio são inofensivos |
| gold | Delta `gold/{daily_revenue, customer_ltv, order_status_funnel}` | — | *full refresh* (pequenas); cancelados fora da receita |
| operação | `_ops/{reports,runs,metrics}` | por `ds` | relatório do gate (JSON), duração dos passos, `capstone.prom` |

### O gate (decisão por lote)

| Check | Nível | Falha quando… |
| --- | --- | --- |
| `not_empty` | **hard** | lote vazio |
| `reject_rate` | **hard** | > 5% das linhas inválidas (problema na origem, não "umas linhas") |
| `freshness` | **hard** | dado mais novo do lote tem > 36 h |
| `duplicate_rate` | soft | > 10% repetem `order_id` |
| `volume_anomaly` | soft | `z` robusto (mediana/MAD) do volume vs. histórico **publicado**; **pula** com < 3 dias de histórico |

**Contrato entre passos:** `silver` **se recusa a rodar** sem um relatório de gate `published` para aquele `ds`
(`GateNotPassed`) — mesmo que alguém chame o passo "na mão" ou o orquestrador tenha um bug de dependência.

## Requisitos

Python ≥ 3.11 (`deltalake`, `duckdb`, `pyarrow`) **ou** só Docker. Para a stack de observabilidade: Docker Compose.

## Estrutura

```text
10-capstone/
├── src/capstone/   synth · quality (parse + gate) · lakehouse (Delta) · steps · metrics · cli
├── dags/capstone_daily.py          # Airflow 3 (imports preguiçosos: o scheduler não precisa de deltalake)
├── monitoring/     alerts.yml (5 regras) · prometheus.yml
├── Dockerfile · docker-compose.yml · Makefile
├── tests/          22 testes (Delta real em diretório temporário)
└── ../../.github/workflows/{capstone,projects}.yml      # CI/CD
```

## Execução

```bash
cd projects/10-capstone
python3 -m venv .venv && source .venv/bin/activate && make install
export PYTHONPATH=src

python -m capstone demo                      # 5 dias (clean, clean, dirty, HEAVY_DIRTY, clean) + idempotência + time travel + rollback
python -m capstone run --ds 2024-03-10       # um dia, na mão (código de saída: 0 ok · 2 bloqueado pelo gate)
python -m capstone ops history               # histórico do Delta (versão, operação, métricas)
python -m capstone ops version --version 2   # time travel: linhas na versão 2
python -m capstone ops optimize              # compactação de arquivos pequenos
python -m capstone ops restore --version 2   # rollback da silver

# em contêiner + observabilidade (Prometheus raspa /metrics; alertas avaliados de verdade)
export METRICS_PORT=9109 PROMETHEUS_PORT=9090
docker compose --profile job run --rm pipeline demo
docker compose --profile job run --rm pipeline run --ds 2024-03-06 --scenario heavy_dirty   # → exit 2
docker compose up -d metrics prometheus      # http://localhost:9090/alerts
docker compose down -v

make ci                                       # o que o GitHub Actions roda: lint · testes · promtool · imagem+demo · DAG
```

Saída verificada do `demo` (resumo):

```text
=== 2024-03-03  cenário: dirty ===
  gate     lidas=364 válidas=354 rejeitadas=10 (2.7%) → 🟢 aprovado        ← lixo tolerado vai para a QUARENTENA
  silver   MERGE: +300 novos · 48 atualizados (de 348 pedidos do lote)
=== 2024-03-04  cenário: heavy_dirty ===
  gate     lidas=410 válidas=357 rejeitadas=53 (12.9%) → 🔴 BLOQUEADO       ← silver e gold NÃO rodam
           ✖ reject_rate: 12.9% (limite 5%)
=== reexecução do último dia ===
  ingest   351 linhas → raw (já existia)        silver  MERGE: +0 novos · 0 atualizados
  silver: versão 3 → 3 (MERGE sem mudanças não altera as linhas: 1223 → 1223)
=== lakehouse: histórico (time travel) ===    v0 WRITE · v1 MERGE · v2 MERGE · v3 MERGE   linhas por versão: {0: 300, 1: 600, 2: 900, 3: 1223}
=== rollback ===  restore → v2: 900 linhas (antes do restore: 1223)  → reaplicar o dia restaura o estado
=== verificações ===
  ✔ exit codes por dia = [0,0,0,2,0] (dia 4 bloqueado)
  ✔ silver == gabarito independente (todos os pedidos, status e valor)
  ✔ nenhuma linha da silver veio do arquivo do dia BLOQUEADO
  ✔ gold.daily_revenue soma == receita esperada (sem cancelados)
  ✔ quarentena tem os dias 03 e 04 (dirty e heavy_dirty)
  ✔ reexecução não alterou as linhas da silver
  ✔ restore voltou a silver a um estado anterior (menos linhas)
  ✔ reaplicar o dia restaurou a silver ao gabarito
```

Alertas no Prometheus após o lote bloqueado: `CapstoneGateBlocked`, `CapstoneRejectRateHigh`, `CapstoneRunFailed` **firing**
(alvo `capstone` `up`).

## Testes

```bash
make test        # 22 testes, ~1 s (Delta real, sem Docker)
```

| Grupo | O que garante |
| --- | --- |
| **Parse/gate (puros)** | 8 formas de lixo → **motivo explícito**; gate **bloqueia** por taxa de rejeição, lote vazio e dado velho; *soft* avisa **sem** bloquear; anomalia **pula** sem histórico; `z` robusto resiste a outlier e a série constante |
| **Ingestão** | reexecutar não duplica a bronze e **não reescreve** a landing zone |
| **Contrato entre passos** | `silver` **recusa** rodar com gate bloqueado ou inexistente |
| **ACID/Delta** | `MERGE` idempotente e **nunca regride** a um evento mais antigo; **schema enforcement** recusa colunas inesperadas; **time travel** e **restore** |
| **Fim a fim** | silver == **gabarito independente** em Python puro; quarentena por dia; gold reconcilia com a silver; dia bloqueado deixa silver/gold **intactos** (a bronze guarda o lote para diagnóstico) |
| **Observabilidade** | texto de métricas válido (HELP/TYPE uma vez por métrica); `gate_blocked=1` e `run_success=0` no bloqueio |

> 🐞 **Armadilhas reais deste projeto**
>
> 1. **`terminate called without an active exception` (exit 134) *depois* do trabalho concluído.** Com `deltalake 1.6` + `pyarrow 25`,
>    threads nativas vivas no encerramento do interpretador às vezes abortam o processo — um *flaky* de desligamento (`gc.collect()`
>    reduziu mas não eliminou). Contorno documentado: o CLI e o `pytest` fazem *flush* e saem com `os._exit(<código correto>)`. Um
>    pipeline que "passa e depois quebra" derrubaria o orquestrador — por isso o código de saída precisa ser **confiável**.
> 2. **Dia bloqueado deixa um "buraco"**: os dias seguintes trazem *atualizações* de pedidos do dia bloqueado, que entram na silver como
>    registros **parciais** (sem a criação). É a semântica correta de um MERGE por chave — e o motivo de existir **backfill** do dia
>    bloqueado quando a origem for corrigida (`run --ds <dia>` é idempotente) e de a métrica de frescor/volume importar.
> 3. **Verificar contra um gabarito independente** (e não contra "o mesmo código") foi o que pegou meu teste errado sobre o dia
>    bloqueado: eu esperava *nenhum* pedido do dia 04 na silver, mas o gabarito mostrou as atualizações acima.

## Decisões arquiteturais e trade-offs

- **Delta Lake via `deltalake` (delta-rs), sem Spark**: ACID, `MERGE`, time travel e `restore` em ~10⁶ linhas num laptop, em Python.
  Custo: sem engine distribuída — acima disso, Spark/Trino sobre o **mesmo** formato ([Delta](../../15-lakehouse/04-delta-lake/README.md),
  [Iceberg](../../15-lakehouse/05-apache-iceberg/README.md)). O formato é aberto: trocar o motor não migra dados.
- **Raw em arquivo imutável + bronze "crua" (string)**: o parse acontece **depois** (schema-on-read na bronze, schema-on-write na
  silver) — se a regra de validação mudar, **reprocessa-se** sem pedir nada à fonte ([medalhão](../../14-data-lake/03-medallion-architecture/README.md)).
- **`replaceWhere` por partição na bronze, `MERGE` na silver, *full refresh* na gold**: três estratégias para três perfis
  (append particionado × upsert por chave × agregado pequeno). Não existe "a" estratégia correta.
- **Predicado `s.updated_at > t.updated_at`** no `WHEN MATCHED`: o `MERGE` vira **idempotente e monotônico** — reexecutar não cria versão
  nova de dados (só a transação vazia) e evento antigo não regride o estado.
- **Gate a montante, `GateNotPassed` a jusante**: a regra vive no dado (relatório), não só na ordem das tasks.
- **Parser único (`parse_line`)** usado pelo gate e pela silver: duas definições de "válido" divergem; uma só, não.
- **Métricas em *textfile* + servidor mínimo**: o padrão do *node_exporter textfile collector*; em produção, *Pushgateway*/OpenTelemetry.
  Há um **dead man's switch** (`PipelineNotRunning`): o pior alerta é o que nunca dispara porque o job nem rodou.
- **Imports preguiçosos no DAG** e passos como funções puras do pacote: o mesmo código roda no Airflow, no CLI, no contêiner e no CI.
- **CI espelhando o `make ci`**: o que passa local passa no Actions. A imagem roda o **demo autoverificável** — falhou um check, falha o build.
- **Sem dbt aqui**: o ELT usa SQL direto (DuckDB) para manter o capstone leve; o [Projeto 02](../02-analytics-warehouse/README.md) mostra o
  caminho dbt (testes, snapshots/SCD2, documentação) — troque `steps.gold` por `dbt-duckdb` como exercício.
- **O que o capstone NÃO faz** (e produção faria): catálogo/linhagem (OpenMetadata), contratos versionados com *schema registry*,
  segredos em cofre, *deploy* com IaC (Projeto 09) e ambientes dev/staging/prod com promoção.

## Possíveis melhorias (exercícios)

1. **Backfill do dia bloqueado**: corrija a origem do dia 04 (`clean`), rode `run --ds 2024-03-04` e demonstre que a silver converge ao gabarito
   *completo*; quantas linhas parciais viram completas?
2. **dbt-duckdb** para a gold, com testes `unique`/`not_null`/`relationships` e documentação ([Projeto 02](../02-analytics-warehouse/README.md)).
3. **Streaming**: substitua o `ingest` por um consumidor Kafka ([Projeto 07](../07-kafka/README.md)) escrevendo na bronze e compare latência/custo.
4. **S3 de verdade**: `LAKE` em `s3://…` (delta-rs suporta S3 com *locking* via DynamoDB) e a infra do [Projeto 09](../09-cloud/README.md).
5. **SCD2** de `dim_customer` na gold (histórico de país) com `MERGE` ([modelagem](../../07-data-modeling/10-slowly-changing-dimensions/README.md)).
6. **Contrato de dados** em YAML validado no gate e no CI (compatibilidade *backward*) ([módulo 29](../../29-data-contracts/README.md)).
7. **Dashboard Grafana** com as métricas `capstone_*` e *SLO* de frescor com *error budget* ([SLI/SLO](../../24-observability/05-sli-slo-sla/README.md)).
8. **Particionar a silver** por `order_date` e medir o *pruning* do `MERGE` com `target.order_date = source.order_date` no predicado.
9. **Vacuum/retenção**: política de retenção do histórico Delta (`vacuum`) × janela de time travel × custo de storage.
10. **Deploy contínuo**: workflow que publica a imagem no registry e promove `dev → staging → prod` com aprovação ([estratégias](../../23-cicd-dataops/06-deployment-strategies/README.md)).

## Referências

- [Delta Lake — protocolo e delta-rs](https://delta-io.github.io/delta-rs/) · [DuckDB](https://duckdb.org/docs/) ·
  [Airflow 3](https://airflow.apache.org/docs/apache-airflow/stable/) · [Prometheus: textfile & alerting](https://prometheus.io/docs/practices/alerting/).
- Reis & Housley, *Fundamentals of Data Engineering* (ciclo de vida completo); Kleppmann, *DDIA* (cap. 3 e 10);
  módulos [15](../../15-lakehouse/README.md), [12](../../12-data-quality/README.md), [24](../../24-observability/README.md) e [23](../../23-cicd-dataops/README.md).
