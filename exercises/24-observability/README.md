# Exercícios — Módulo 24: Observabilidade

Teoria em [24-observability](../../24-observability/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Logs, métricas e traces

Para cada pergunta, qual pilar responde melhor? (a) "quantos pedidos rejeitados na última hora?"; (b) "por que **este** arquivo falhou?"; (c) "em que etapa a requisição passou mais tempo?".

<details><summary>Gabarito</summary>

(a) **Métricas** (agregadas, baratas, alertáveis). (b) **Logs** (eventos detalhados e estruturados). (c) **Traces** (caminho de uma requisição entre serviços). Ver [logging](../../24-observability/01-logging/README.md), [métricas](../../24-observability/02-metrics/README.md), [tracing](../../24-observability/03-tracing/README.md).
</details>

## 2. 🟢 Implementação — Log estruturado

Reescreva `print(f"erro no arquivo {f}")` como log estruturado (JSON) com nível, `run_id` e campos pesquisáveis.

<details><summary>Gabarito</summary>

```python
import json, logging, sys
log = logging.getLogger("etl")
def emit(level, msg, **fields):
    print(json.dumps({"level": level, "msg": msg, **fields}), file=sys.stdout, flush=True)
emit("ERROR", "falha ao processar arquivo", file=f, run_id=run_id, error=repr(e))
```
JSON permite filtrar por campo (`run_id`, `file`) no agregador de logs; texto livre exige regex frágil. Nunca logue **PII** ou segredos.
</details>

## 3. 🔵 Implementação — Regra de alerta

Escreva uma regra Prometheus que dispara se **nenhuma execução** do pipeline ocorreu nas últimas 26 h (*dead man's switch*) e outra que dispara em lote bloqueado.

<details><summary>Gabarito</summary>

```yaml
groups:
  - name: pipeline
    rules:
      - alert: PipelineNotRunning
        expr: time() - pipeline_last_run_timestamp_seconds > 26 * 3600
        for: 10m
        labels: {severity: page}
      - alert: GateBlocked
        expr: pipeline_gate_blocked == 1
        labels: {severity: page}
```
Valide com `promtool check rules`. Ver [alertas](../../24-observability/04-alerting/README.md) e os arquivos [do capstone](../../projects/10-capstone/monitoring/alerts.yml).
</details>

## 4. 🔵 Conceitual — SLI, SLO, SLA

Defina SLI, SLO e SLA para "o relatório diário está pronto até 08:00" e calcule o **orçamento de erro** de um SLO de 99% em 30 dias.

<details><summary>Gabarito</summary>

**SLI:** fração de dias em que o relatório ficou pronto até 08:00. **SLO:** ≥ 99% dos dias em 30 dias. **SLA:** compromisso contratual (com penalidade) — mais frouxo que o SLO. Orçamento: 1% de 30 dias ≈ **0,3 dia** (≈ 1 falha em 30 dias, com folga de 0,3). Esgotou o orçamento ⇒ priorizar confiabilidade sobre novas features. Ver [SLI/SLO/SLA](../../24-observability/05-sli-slo-sla/README.md).
</details>

## 5. 🟣 Arquitetura — Frescor de dados

Como medir **frescor** de uma tabela de forma confiável? Por que usar o `max(event_time)` e não o horário da última carga?

<details><summary>Gabarito</summary>

Frescor = `agora − max(event_time)` (idade do dado **mais novo**). O horário da carga engana: um job pode rodar "com sucesso" e carregar **dado velho** (a fonte parou). Combine com **volume** e alerta de "sem execução". Ver [frescor](../../24-observability/06-data-freshness/README.md).
</details>

## 6. 🟣 Arquitetura — Runbook e pós-mortem

Escreva o esqueleto de um **runbook** para "gate de qualidade bloqueou o lote" e o formato de um **pós-mortem sem culpados**.

<details><summary>Gabarito</summary>

Runbook: (1) onde ver o relatório do gate; (2) classificar causa (origem × pipeline); (3) impacto (consumidores seguem na última partição boa); (4) ação (corrigir origem → **reexecutar o `ds`** idempotente); (5) escalonamento/contatos. Pós-mortem: linha do tempo, **impacto**, causa raiz, **o que funcionou/falhou na detecção**, ações com dono e prazo — foco em **sistemas**, não em pessoas. Ver [incident response](../../24-observability/07-incident-response/README.md) e o runbook do [Projeto 04](../../projects/04-data-quality/README.md).
</details>
