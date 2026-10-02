# Alertas

> 🟣 Production · Parte de [24 — Observability](../README.md)

## O que é

**Alertas** são notificações automáticas disparadas quando [métricas](../02-metrics/README.md)/[logs](../01-logging/README.md)/
checagens indicam que algo **precisa de atenção humana**. O objetivo: **a pessoa certa saber a coisa certa
no momento certo** — nem antes (ruído), nem depois (o usuário já percebeu).

## O princípio central: alerte no que é acionável

Um bom alerta é:

- **Acionável** — existe algo concreto a fazer agora.
- **Relevante** — indica (ou prediz) **impacto real** nos usuários/dados, não apenas uma causa possível.
- **Urgente** — justifica interromper alguém (senão vira ticket/relatório).
- **Compreensível** — diz o que está errado, onde e por onde começar (link p/ dashboard/runbook).

> Regra SRE: alerte em **sintomas** (impacto) e use dashboards/logs para **causas**. "CPU 85%" raramente é
> alerta; "dados de vendas atrasados > 2h do SLA" é.

## Alert fatigue (o inimigo)

Alertas demais, ruidosos ou não acionáveis fazem o time **ignorá-los** — e perder o crítico. Sintomas:
alertas que "sempre disparam", silenciados em massa, plantonista que não confia no pager. Combata com:

- **Reduzir ruído**: remova/ajuste alertas que ninguém age; agrupe duplicados.
- **Severidades** claras: *page* (acorda alguém) vs *ticket* (resolve no expediente) vs *informativo*.
- **Limiares sensatos** com **janelas** (`for: 10m`) para ignorar picos transitórios.
- **Inibição/dependência**: se o banco caiu, silencie os 50 alertas derivados.
- **Revisão periódica**: cada alerta precisa de dono e justificativa.

## Tipos de alerta úteis em dados

| Tipo | Exemplo | Gravidade típica |
| --- | --- | --- |
| **Falha de execução** | DAG/job falhou após retries | page se crítico/SLA |
| **Não executou (dead man's switch)** | sem sucesso há > N horas | page |
| **Atraso vs SLA/frescor** | tabela > 6h desatualizada | page/ticket ([freshness](../06-data-freshness/README.md)) |
| **Volume anômalo** | linhas −60% vs média | page/ticket ([anomaly](../../12-data-quality/07-anomaly-detection/README.md)) |
| **Qualidade** | teste `unique`/`not_null` crítico falhou | page se bloqueia gate |
| **Schema drift** | coluna sumiu/mudou tipo | ticket/page |
| **Lag de consumo** | consumer lag > SLO | page ([backpressure](../../18-message-brokers/06-backpressure/README.md)) |
| **Recursos/infra** | disco 90%, OOMKilled repetido | ticket/page |
| **Custo** | gasto > orçamento/anomalia | ticket ([cost](../../19-cloud/08-cost-management/README.md)) |

## Alertas baseados em SLO (burn rate)

Em vez de limiares arbitrários, alerte quando o **orçamento de erro** do [SLO](../05-sli-slo-sla/README.md)
está sendo consumido rápido demais (**burn rate**), com janelas múltiplas (rápida + lenta). Reduz falsos
positivos e prioriza o que ameaça a meta.

## Anatomia de um bom alerta (exemplo Prometheus)

```yaml
groups:
- name: pipeline
  rules:
  - alert: PipelineSemSucessoRecente
    expr: time() - pipeline_last_success_timestamp{pipeline="vendas"} > 26 * 3600
    for: 10m
    labels: { severity: page, team: dados }
    annotations:
      summary: "Pipeline vendas sem sucesso há mais de 26h"
      description: "Última execução OK: {{ $value | humanizeDuration }} atrás."
      runbook_url: "https://wiki.empresa/runbooks/pipeline-vendas"
      dashboard: "https://grafana.empresa/d/pipelines"
```

Observe: `for` evita flapping; `severity` roteia; `runbook_url` acelera a resposta.

## Roteamento e on-call

- **Alertmanager/PagerDuty/Opsgenie** roteiam por severidade/time, agrupam, silenciam, escalonam.
- **Ownership**: todo alerta pertence a um time/dono ([ownership](../../25-data-governance/04-ownership-stewardship/README.md)).
- **Plantão (on-call)** sustentável: rotação, escalonamento, *handoff*, compensação, limite de *pages* por
  turno; cada page inesperado é dívida a eliminar.
- Canais: pager (crítico), Slack/e-mail (não urgente), tickets (backlog).

## Runbooks

Para cada alerta crítico: **o que significa, impacto, como diagnosticar, como mitigar, quem acionar**.
Automatize o que for repetitivo (auto-remediação segura, ex.: reiniciar job idempotente).

## Alertas para dados vs software

Pipelines "verdes" podem produzir dados errados; portanto, além de alertar falhas, alerte **sintomas de
dados** (frescor, volume, qualidade). Ver [observabilidade de pipeline](../../10-data-pipelines/08-pipeline-observability/README.md).

## Erros comuns

- Alertar em causas/ruído (CPU, warnings) em vez de sintomas de impacto.
- Sem `for`/janelas → flapping.
- Alertas sem dono/runbook; "todo mundo recebe tudo".
- Tudo como page (fadiga) ou nada (cegueira).
- Não revisar/limpar alertas obsoletos.
- Ignorar o "não rodou" (só alertar quando falha explícita).

## Boas práticas

- Alerte em sintomas/SLOs; severidades; link para dashboard e runbook.
- `for` + inibição + agrupamento; revisão regular (cada page deve ser acionável).
- Dead man's switch para jobs agendados; alertas de dados (frescor/volume/qualidade).
- Dono explícito; plantão saudável.

## Relação com outros conceitos

- [Métricas](../02-metrics/README.md), [SLI/SLO/SLA](../05-sli-slo-sla/README.md),
  [freshness](../06-data-freshness/README.md), [incident response](../07-incident-response/README.md),
  [pipeline observability](../../10-data-pipelines/08-pipeline-observability/README.md).

## Exercícios

1. Classifique 8 alertas candidatos em page/ticket/descartar e justifique.
2. Escreva uma regra de alerta "dead man's switch" para um pipeline diário.
3. Desenhe um alerta de burn rate para um SLO de frescor de 99%.
4. Escreva um runbook curto para "dados de vendas atrasados".

## Referências

- Google SRE Book — Monitoring, Practical Alerting; *SRE Workbook* — Alerting on SLOs.
- Documentação do Prometheus Alertmanager, PagerDuty/Opsgenie.
