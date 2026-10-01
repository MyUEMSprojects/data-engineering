# Pipeline observability

> 🔵 Pipelines · Parte de [10 — Data Pipelines](../README.md)

## O que é

**Observabilidade de pipeline** é a capacidade de **enxergar** o que o pipeline está fazendo:
se rodou, quanto demorou, quantos dados processou, se falhou, e — crucialmente em dados — se
os **dados produzidos estão saudáveis**. (Os fundamentos de observabilidade — logs, métricas,
tracing, SLOs — estão no [módulo 24](../../24-observability/README.md); aqui focamos no que é
específico de pipelines de dados.)

## Por que é diferente de observabilidade de software

Em software tradicional, "está no ar e responde rápido" basta. Em dados, um pipeline pode
estar **verde** (rodou sem erro) e mesmo assim produzir **dados errados** (volume caiu pela
metade, uma coluna virou nula, os números estão defasados). Por isso, observabilidade de
dados tem **duas camadas**:

```text
Operacional:  o pipeline rodou? demorou quanto? falhou?      (como software)
De dados:     os DADOS estão certos? completos? frescos?     (específico de dados)
```

## Observabilidade operacional

Do próprio orquestrador ([Airflow](../../11-orchestration/02-airflow/README.md)/Dagster) e da
infra:

- **Status** de cada run/tarefa (sucesso/falha/retry).
- **Duração** e tendência (está ficando mais lento?).
- **Taxa de sucesso/falha**, nº de retries.
- **Recursos** (CPU/memória/custo) — ver [troubleshooting](../../02-linux-shell-environment/08-logs-and-troubleshooting/README.md).
- **Logs** estruturados por run (ver [logging](../../04-python-for-data-engineering/04-errors-and-logging/README.md)).

## Observabilidade de dados: os "pilares"

Métricas sobre os **dados** que o pipeline produz (base de ferramentas como Monte Carlo,
Soda, Elementary):

| Pilar | Pergunta | Exemplo de sinal |
| --- | --- | --- |
| **Freshness** | o dado está atualizado? | última carga há > 26h → alerta ([freshness](../../24-observability/06-data-freshness/README.md)) |
| **Volume** | chegou a quantidade esperada? | nº de linhas caiu 60% vs média |
| **Schema** | a estrutura mudou? | coluna sumiu/mudou de tipo ([schema](../../08-data-formats/10-schema-evolution/README.md)) |
| **Distribuição** | os valores fazem sentido? | % de nulos subiu; média fora da faixa |
| **Lineage** | o que foi afetado? | ([lineage](../06-data-lineage/README.md)) para impacto |

Esses sinais pegam o "verde mas errado" — a classe de incidente mais perigosa em dados.

## O que instrumentar no pipeline

Emita, a cada run: `run_id`, data lógica, **contagens** (lidas/escritas/rejeitadas),
**duração** por etapa, resultado das **validações**, e marcos (início/fim). Isso alimenta
dashboards e alertas.

```python
log.info("stage_done", extra={
    "run_id": rid, "stage": "load_fato", "logical_date": d,
    "rows_in": n_in, "rows_out": n_out, "rejected": n_bad, "duration_s": dt,
})
```

## Alertas (acionáveis)

- Alerte em **falha** e em **degradação** (atraso/SLA, volume anômalo, frescor).
- Evite *alert fatigue*: alerte no que é acionável; agrupe; defina severidade.
- Direcione ao dono do dado/pipeline (ver [ownership](../../25-data-governance/04-ownership-stewardship/README.md)).

## SLAs/SLOs de dados

Defina e monitore: "dados do dia prontos até 6h", "frescor < 1h", "completude > 99,9%" (ver
[SLI/SLO/SLA](../../24-observability/05-sli-slo-sla/README.md)). Um SLA de dados violado deve
gerar alerta — não ser descoberto pelo usuário do dashboard.

## Dashboards de pipeline

Uma visão consolidada: últimos runs, status, durações, frescor por tabela, testes de dados
passando/falhando. É onde o time "sente o pulso" da plataforma.

## Lineage para diagnóstico

Quando um sinal dispara, o [lineage](../06-data-lineage/README.md) mostra **onde** o problema
surgiu e **o que mais** é afetado a jusante — acelera a resposta a incidentes (ver
[incident response](../../24-observability/07-incident-response/README.md)).

## Erros comuns

- Só observabilidade operacional (pipeline verde) e dados errados passam.
- Sem contagens/métricas por run → impossível detectar anomalias de volume.
- Alertas demais (fadiga) ou de menos (incidentes descobertos pelo usuário).
- Não ter SLA de dados → ninguém sabe o que é "normal".
- Logs sem `run_id`/contexto → impossível correlacionar.

## Boas práticas

- Observe operacional **e** dados (freshness, volume, schema, distribuição).
- Instrumente contagens/duração/validações por run, com `run_id`.
- Alerte no acionável; defina SLAs de dados e monitore-os.
- Integre com [lineage](../06-data-lineage/README.md) para impacto/diagnóstico.

## Relação com outros conceitos

- Fundamentos: [24 — Observability](../../24-observability/README.md),
  [freshness](../../24-observability/06-data-freshness/README.md),
  [SLO](../../24-observability/05-sli-slo-sla/README.md).
- [Lineage](../06-data-lineage/README.md),
  [data quality](../../12-data-quality/README.md),
  [fault tolerance](../05-fault-tolerance/README.md).

## Exercícios

1. Liste as métricas operacionais e de dados que você exporia para um pipeline de vendas.
2. Dê um exemplo de pipeline "verde, mas com dados errados" e qual pilar de observabilidade o
   pegaria.
3. Instrumente uma etapa para emitir contagens e duração com `run_id`.
4. Defina 3 SLAs de dados e os alertas correspondentes.

## Referências

- Reis & Housley, *Fundamentals of Data Engineering* — observabilidade.
- Documentação de Elementary, Soda, Monte Carlo; Google SRE Book.
