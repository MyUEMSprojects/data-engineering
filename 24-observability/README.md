# 24 — Observability

> 🟣 Nível 7 — Production · Pré: [10 — Pipelines](../10-data-pipelines/README.md),
> [12 — Data Quality](../12-data-quality/README.md) · Próximo: [25 — Governance](../25-data-governance/README.md)

**Observabilidade** é a capacidade de **entender o estado interno de um sistema a partir de suas saídas**
(logs, métricas, traces). Em dados, vai além do software: além de "o pipeline rodou?", precisa responder
"**os dados estão corretos, completos e atualizados?**". Sem observabilidade, você descobre problemas
quando o usuário reclama.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Logging](01-logging/README.md) | Eventos estruturados e centralizados |
| 02 | [Métricas](02-metrics/README.md) | Séries temporais, Prometheus |
| 03 | [Tracing](03-tracing/README.md) | Seguir uma execução entre componentes |
| 04 | [Alertas](04-alerting/README.md) | Notificar o que é acionável |
| 05 | [SLI, SLO e SLA](05-sli-slo-sla/README.md) | Definir e medir confiabilidade |
| 06 | [Data freshness e saúde dos dados](06-data-freshness/README.md) | Frescor, volume, schema, distribuição |
| 07 | [Incident response](07-incident-response/README.md) | Responder, resolver e aprender |

## Dependências internas

```text
Logging · Métricas · Tracing (os 3 pilares)
        │
        ▼
Alertas ◄── SLI/SLO/SLA ◄── Data freshness/saúde dos dados
        │
        ▼
Incident response (e pós-mortem)
```

## Checkpoint

- [ ] Diferenciar monitoring de observabilidade e explicar os 3 pilares.
- [ ] Produzir logs estruturados com contexto de pipeline (`run_id`, partição).
- [ ] Definir métricas úteis e instrumentá-las (contadores, gauges, histogramas).
- [ ] Entender tracing distribuído e quando importa em dados.
- [ ] Criar alertas acionáveis e evitar alert fatigue.
- [ ] Definir SLIs/SLOs/SLAs para dados (frescor, completude).
- [ ] Monitorar frescor/volume/schema/distribuição; conduzir resposta a incidentes e pós-mortem.

## Referências do módulo

- Beyer, B. et al. *Site Reliability Engineering* (Google SRE Book — gratuito).
- Majors, C. et al. *Observability Engineering*. O'Reilly.
- Documentação de OpenTelemetry, Prometheus, Grafana.
