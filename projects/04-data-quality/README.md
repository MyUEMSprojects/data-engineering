# Projeto 04 — Data Quality (contrato + validação + quarentena + observabilidade)

> 🔵 Nível: intermediário · Módulos: [12 Data Quality](../../12-data-quality/README.md),
> [29 Data Contracts](../../29-data-contracts/README.md), [24 Observability](../../24-observability/README.md),
> [09 ETL/ELT (validação)](../../09-etl-elt/10-data-validation/README.md) · Anterior:
> [Projeto 03](../03-orchestration/README.md) · Próximo: [Projeto 05](../05-data-lake/README.md)

## Objetivo

Construir o "porteiro" de qualidade de um pipeline: um **contrato de dados executável (YAML)** que valida cada
lote, **quarentena** as linhas ruins, **bloqueia** o lote inteiro quando algo está errado na origem,
**detecta anomalias** contra o histórico e expõe **métricas + alertas** (Prometheus). O que se aprende:

- qualidade como **gate** (não como relatório depois do estrago);
- diferença entre checks de **linha** (quarentenar) e de **dataset** (bloquear), e entre **hard** e **soft**;
- **observabilidade de dados**: frescor, volume, schema, distribuição e *dead man's switch*;
- um bloqueio **nunca** apaga a última publicação boa.

## Arquitetura

```text
 lote CSV ─► carga (tudo VARCHAR) ─► schema vs contrato ─► tipagem (TRY_CAST) ─► checks ─► DECISÃO
                                          │                                   │
                                  incompatível ⇒ BLOQUEIA            linha: quarentena · dataset: bloqueia
                                                                      soft: avisa
        ┌──────────────────────────┬──────────────────────────┬──────────────────────────────┐
        ▼ publicado                ▼ quarentena (com motivos) ▼ relatório (md/json)           ▼ métricas
  publish/orders/dt=…/part.parquet  quarantine/…/rejected.parquet  reports/…/report.{md,json}   metrics/dq.prom
  (só linhas válidas, tipadas)      (original + _dq_reasons)                                      │
        │                                                                           exporter ─► Prometheus ─► alertas
        └─► estatísticas do lote entram no HISTÓRICO (baseline das anomalias)  ◄── só lotes PUBLICADOS
```

### A regra de decisão (gate)

| Situação | Resultado |
| --- | --- |
| schema incompatível (coluna obrigatória ausente / coluna não prevista) | 🔴 **bloqueia** (e nem avalia o resto) |
| lote vazio | 🔴 bloqueia |
| check de **dataset** `hard` falhou (unicidade, volume, frescor…) | 🔴 bloqueia |
| linhas ruins > `max_quarantine_rate` (5%) | 🔴 bloqueia — o problema é a origem, não "umas linhas" |
| linhas ruins ≤ 5% | 🟢 publica o resto; ruins → **quarentena** |
| check `soft` falhou (nulos em `uf`, anomalia de média…) | 🟢 publica com ⚠ **aviso** |
| histórico insuficiente para anomalia | ⏭ check **pulado** (nunca "aprovado às cegas") |

## Estrutura

```text
04-data-quality/
├── contracts/orders.yaml        # CONTRATO: schema, checks (nível/severidade), limites, SLA
├── src/dqpipe/
│   ├── contract.py              # carrega e VALIDA o contrato (contrato inválido falha cedo)
│   ├── checks.py                # checks de linha e de dataset (SQL em DuckDB) -> CheckResult estruturado
│   ├── anomaly.py               # z-score ROBUSTO (mediana/MAD) vs histórico
│   ├── runner.py                # orquestra o lote, decide, grava publish/quarentena/relatório/histórico
│   ├── metrics.py · exporter.py # métricas Prometheus + servidor /metrics (stdlib)
│   ├── synth.py                 # gerador sintético com 9 cenários de falha
│   └── cli.py                   # synth | run | demo | exporter
├── monitoring/                  # prometheus.yml + alerts.yml (6 regras)
├── docker-compose.yml           # exporter + Prometheus
└── tests/                       # 36 testes (contrato, anomalia, 1 por cenário, idempotência, métricas…)
```

## Requisitos

Python ≥ 3.11 (`duckdb`, `pyyaml`) · Docker (só para o Prometheus). **Nenhum banco** é necessário: o motor
de checks é o DuckDB em memória.

## Execução

```bash
cd projects/04-data-quality
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
export PYTHONPATH=src

# DEMO: 10 lotes saudáveis (constroem o histórico) + 8 cenários de falha, um por dia
python -m dqpipe demo
```

Saída verificada:

```text
--- 2024-01-11  cenário: dirty_rows ---
🟢 PUBLICADO  orders dt=2024-01-11  lidas=1019 publicadas=989 quarentena=30
--- 2024-01-12  cenário: heavy_dirty ---
🔴 BLOQUEADO  ...  quarentena=125
   ✖ quarentena 11.9% > limite 5.0%
--- 2024-01-13  cenário: duplicates ---
🔴 BLOQUEADO
   ✖ pk_unique: 20 linhas repetem a chave ("order_id")
--- 2024-01-14  cenário: schema_drift ---
🔴 BLOQUEADO
   ✖ schema incompatível: colunas obrigatórias ausentes: ['amount']; colunas não previstas no contrato: ['total_amount', 'channel']
--- 2024-01-15  cenário: volume_drop ---
🔴 BLOQUEADO  lidas=155
   ✖ volume_in_range: 155
   ⚠ volume_anomaly: z=-25.3 vs 11 lotes publicados
--- 2024-01-16  cenário: stale ---
🔴 BLOQUEADO
   ✖ freshness: dado mais recente tem 54.0h
--- 2024-01-17  cenário: null_uf ---
🟢 PUBLICADO  ⚠ uf_null_rate: 19.94% nulos em uf
--- 2024-01-18  cenário: mean_shift ---
🟢 PUBLICADO  ⚠ amount_mean_anomaly: z=+196.5 vs 12 lotes publicados
```

Usando como um *job* real (o `--partition` vem do orquestrador; código de saída **2 = bloqueado** → a task falha):

```bash
python -m dqpipe synth --day 2024-02-01 --scenario duplicates --out in/orders.csv
python -m dqpipe run --input in/orders.csv --partition 2024-02-01 --out out \
       --contract contracts/orders.yaml          # ou --as-of 2024-02-02T06:00:00+00:00 (determinismo)
echo $?                                           # 0 publicado · 2 bloqueado
cat out/reports/orders/dt=2024-02-01/report.md    # relatório legível

# inspecionar a quarentena (cada linha com os checks que reprovaram)
python -c "import duckdb; print(duckdb.sql(\"select _dq_reasons, count(*) from 'out/quarantine/orders/dt=*/rejected.parquet' group by 1\"))"
```

### Observabilidade (Prometheus + alertas)

```bash
python -m dqpipe demo                       # gera out/metrics/dq.prom
docker compose up -d                        # (portas ocupadas? EXPORTER_PORT=9208 PROMETHEUS_PORT=9190)
# Prometheus: http://localhost:9090  ·  Alerts: /alerts  ·  métricas cruas: http://localhost:9108/metrics
curl -s 'localhost:9090/api/v1/query?query=dq_gate_blocked'
docker compose down -v
```

Métricas expostas (`dq_*`): `check_passed{check,level,severity}` · `check_observed` · `rows{state=read|published|quarantined}`
· `gate_blocked` · `warnings` · `data_age_seconds` · `last_run_timestamp_seconds` · `contract_info{version,owner}`.

Alertas ([`monitoring/alerts.yml`](monitoring/alerts.yml), validados com `promtool`; disparo conferido num lote `stale`):
`DQGateBlocked` · `DQHardCheckFailed` · `DQSoftCheckFailed` · `DQQuarantineRateHigh` · `DQDataStale` · `DQPipelineNotRunning`.
(No demo os relógios são **simulados em 2024**, então `DQPipelineNotRunning` dispara — esperado.)

## Testes

```bash
pytest -q          # 36 testes, ~10s, sem infraestrutura externa
```

| Grupo | O que garante |
| --- | --- |
| **Contrato** | contrato inválido falha cedo e com mensagem clara (6 casos + tipo não suportado) |
| **Anomalia** | z robusto resiste a outlier no histórico; histórico insuficiente ⇒ *pula*; série constante não divide por zero |
| **Cenários (1 por falha)** | decisão **e motivo** corretos; `válidas + quarentena = lidas` (nada some); schema drift para antes de avaliar o resto |
| **Idempotência** | reexecutar a mesma partição não duplica linhas nem histórico |
| **Segurança operacional** | lote **bloqueado não apaga** a última publicação boa nem **polui o baseline** de anomalias |
| **Saídas** | tipos do contrato no Parquet; relatório md/json; métricas no formato Prometheus; exporter HTTP; exit code do CLI |

## Decisões arquiteturais e trade-offs

- **Contrato executável, em YAML, validado ao carregar** — [data contracts](../../29-data-contracts/README.md):
  documentação que ninguém verifica apodrece; aqui o contrato **é** o teste.
- **Linha vs dataset; hard vs soft** — [expectation testing](../../12-data-quality/04-expectation-testing/README.md):
  nem todo problema merece parar o pipeline, e alguns (schema, unicidade) invalidam o lote inteiro.
- **Limite de quarentena** (`max_quarantine_rate`): "descartar 12% das linhas e seguir" mascara um defeito na
  origem; acima do limite, **para**.
- **Tudo VARCHAR → `TRY_CAST`**: um valor `abc` em `amount` vira linha em quarentena (com o motivo
  `type_cast:amount`) em vez de derrubar a carga inteira com um erro de conversão.
- **Anomalia com mediana/MAD** (não média/desvio): um outlier no histórico não "cega" a detecção seguinte.
  **Só lotes publicados** entram no baseline — lote ruim não ensina o que é "normal".
- **`mean_shift` é *soft*** (publica com aviso): decisão consciente. Um salto de 4× pode ser um bug de unidade
  **ou** uma campanha legítima; promova a *hard* quando houver confiança — é um trade-off entre falso positivo
  e falso negativo, não uma verdade.
- **Frescor medido pelo `max(created_at)` do dado** (event time), não pelo horário de carga — um pipeline pode
  carregar dado velho "recém-chegado". O `as-of` é **injetável**, o que torna os testes determinísticos.
- **Quarentena também de lotes bloqueados** (ex.: `heavy_dirty`): vira material de diagnóstico para o dono da fonte.
- **Estado em JSON** (`state/history.json`): suficiente para o estudo; em produção, uma tabela
  (e as métricas por *push*/OpenTelemetry em vez de arquivo + exporter).
- **Sem Great Expectations/dbt aqui de propósito**: o objetivo é entender o **mecanismo** (checks → resultado
  estruturado → gate → métricas). Depois, mapeie cada `type` para `expect_*` (GE) ou `data_tests` (dbt) — ver
  [dbt tests](../../12-data-quality/06-dbt-tests/README.md) e [Great Expectations](../../12-data-quality/05-great-expectations/README.md).

## Runbook (lote bloqueado)

1. **Abra o relatório** (`out/reports/<dataset>/dt=…/report.md`): a seção *Motivos do bloqueio* diz o quê.
2. **Classifique**: schema/unicidade/volume/frescor ⇒ **problema da origem** (acione o dono do contrato,
   `owner` no YAML); quarentena alta ⇒ veja `_dq_reasons` no Parquet de quarentena.
3. **Consumidores não foram afetados**: seguem na última partição publicada (um bloqueio não apaga nada).
4. **Corrija na origem** e **reexecute a mesma partição** (idempotente) — ou, se a regra estiver errada,
   ajuste o contrato **por PR** (versione `version:`).
5. **Pós-mortem**: o que faltou para detectar antes? Novo check? Novo alerta? ([incident response](../../24-observability/07-incident-response/README.md))

## Possíveis melhorias (exercícios)

1. **Integrar ao DAG do [Projeto 03](../03-orchestration/README.md)**: uma task `quality_gate` que chama
   `dqpipe run` e falha em `exit 2`.
2. **Novos tipos de check**: `referential_integrity` (FK contra uma dimensão), `distribution_drift` (PSI/KS).
3. **Sazonalidade** na anomalia (baseline por dia da semana) para não alertar toda segunda-feira.
4. **Contratos versionados + compatibilidade** (`datacontract breaking`) validados no CI.
5. **Grafana**: dashboard com `dq_gate_blocked`, taxa de quarentena e frescor por dataset.
6. **Migrar os checks** para dbt tests/Great Expectations e comparar esforço e cobertura.
7. **Alertmanager** → Slack/e-mail com o link do relatório e o runbook.

## Referências

- Moses et al., *Data Quality Fundamentals* (O'Reilly) · [módulo 12](../../12-data-quality/README.md) (dimensões, expectativas, anomalias).
- [Open Data Contract Standard](https://github.com/bitol-io/open-data-contract-standard) · [DuckDB docs](https://duckdb.org/docs/) · [Prometheus: alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/).
