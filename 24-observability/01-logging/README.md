# Logging

> 🟣 Production · Parte de [24 — Observability](../README.md)

## O que é

**Logs** são registros de **eventos discretos** ocorridos num sistema, com timestamp e contexto. São o
pilar mais antigo e o primeiro recurso para **entender o que aconteceu** numa execução específica. (A
mecânica em Python está em [erros e logging](../../04-python-for-data-engineering/04-errors-and-logging/README.md);
aqui, a visão de **plataforma**: estrutura, centralização e uso operacional.)

## Logs vs métricas vs traces

| Pilar | Responde | Forma |
| --- | --- | --- |
| **Logs** | **o que** aconteceu (detalhe de um evento) | texto/JSON com timestamp |
| **[Métricas](../02-metrics/README.md)** | **quanto/quão rápido** (tendência agregada) | números ao longo do tempo |
| **[Traces](../03-tracing/README.md)** | **onde** o tempo/erro ocorreu entre componentes | spans encadeados |

Complementares: métrica avisa *que* algo mudou; log explica *o quê*; trace mostra *onde*.

## Logs estruturados (essencial)

Texto livre é difícil de pesquisar/agregar. Use **JSON** com campos consistentes:

```json
{"ts":"2024-01-15T02:03:11Z","level":"INFO","service":"etl-vendas","event":"load_done",
 "run_id":"2024-01-15T02:00","table":"fct_vendas","partition":"2024-01-14",
 "rows_in":125340,"rows_out":125298,"rejected":42,"duration_s":87.3}
```

Campos úteis em pipelines: `run_id`, `dag/task`, `logical_date`/partição, `table`, **contagens**
(lidas/escritas/rejeitadas), **duração**, `environment`, versão do código/imagem, `trace_id`. Isso permite
filtrar "tudo da execução X" e calcular métricas a partir de logs.

## Níveis (use com critério)

`DEBUG` (diagnóstico, desligado em prod), `INFO` (progresso normal), `WARNING` (algo estranho, segue),
`ERROR` (falha de operação), `CRITICAL` (sistema não segue). Evite poluir `INFO` e **nunca** `ERROR` para
coisas esperadas.

## O que logar em pipelines de dados

- Início/fim de cada etapa com **duração e contagens**.
- Decisões de qualidade (linhas rejeitadas/quarentenadas, dedupe, schema drift detectado).
- Parâmetros da execução (data lógica, ambiente, versão).
- Erros com **contexto reproduzível** (stack trace, entrada que falhou — sem PII).
- Chamadas externas (API/DB) com latência/status e retries ([HTTP clients](../../04-python-for-data-engineering/08-http-clients/README.md)).

## O que **não** logar

- **Segredos/credenciais/tokens**.
- **PII/dados sensíveis** (CPF, e-mail, cartão) — use IDs/hashes/mascaramento
  ([masking](../../26-security/07-data-masking-pii/README.md), [LGPD](../../26-security/08-lgpd/README.md)).
- Payloads gigantes (custo e ruído) — logue amostra/tamanho.

## Centralização (aggregation)

Em containers/[Kubernetes](../../21-kubernetes/08-observability/README.md) os logs somem com o Pod. Envie a um
sistema central:

```text
app (stdout JSON) ─► coletor (Fluent Bit / Vector / OTel Collector) ─► armazenamento (Loki / Elasticsearch / CloudWatch / Cloud Logging) ─► busca/dashboards/alertas
```

Stacks: **ELK/EFK** (Elasticsearch+Logstash/Fluentd+Kibana), **Grafana Loki**, serviços cloud
([CloudWatch Logs / Cloud Logging / Azure Monitor](../../19-cloud/07-monitoring-autoscaling/README.md)),
Datadog/Splunk. Defina **retenção** por criticidade (custo × auditoria — ver
[retenção](../../25-data-governance/06-retention-auditing/README.md)).

## Correlação

Propague **`run_id`/`correlation_id`/`trace_id`** entre componentes (orquestrador → job → API) para
reconstruir uma execução de ponta a ponta. Sem IDs de correlação, depurar fluxos distribuídos é arqueologia.

## Do log ao insight

- **Busca** por `run_id`/erro; **agregações** (erros por tabela/hora); **alertas baseados em logs** (ex.:
  "ERROR com `event=load_failed`").
- **Métricas derivadas de logs** (contagem de linhas rejeitadas por run) — mas prefira
  [métricas nativas](../02-metrics/README.md) para o que é numérico e frequente.

## Custo e volume

Logs são caros em escala (ingestão + armazenamento). Controle com **níveis**, **amostragem**, retenção
em camadas (quente/frio), e evitando logs em *loops* quentes (uma linha por registro em milhões de linhas).

## Erros comuns

- Logs em texto livre sem estrutura/contexto.
- Segredos/PII nos logs.
- Sem `run_id`/correlação.
- Logar por registro em jobs de milhões de linhas (custo/ruído).
- Logs só locais/efêmeros (somem com o container).
- `except: pass` sem logar (falha silenciosa).

## Boas práticas

- JSON estruturado com contexto de pipeline; níveis corretos; sem segredos/PII.
- Centralizar, com retenção definida e controle de custo.
- IDs de correlação; logs acionáveis (dizem o quê, onde e por quê).
- Emitir contagens/durações para virar métricas e SLOs.

## Relação com outros conceitos

- [Métricas](../02-metrics/README.md), [tracing](../03-tracing/README.md), [alertas](../04-alerting/README.md),
  [pipeline observability](../../10-data-pipelines/08-pipeline-observability/README.md),
  [Python logging](../../04-python-for-data-engineering/04-errors-and-logging/README.md).

## Exercícios

1. Defina o schema de log JSON ideal para uma tarefa de ingestão diária.
2. Reescreva 3 logs ruins ("erro", "falhou", "ok") como eventos estruturados acionáveis.
3. Desenhe o caminho do log de um Pod de pipeline até um dashboard/alerta.
4. Liste dados que **nunca** devem aparecer em logs e como mascará-los.

## Referências

- Google SRE Book — Monitoring; Twelve-Factor App (logs como streams); docs de Loki/ELK/OpenTelemetry Logs.
