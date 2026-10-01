# Métricas

> 🟣 Production · Parte de [24 — Observability](../README.md)

## O que é

**Métricas** são medições **numéricas agregadas ao longo do tempo** (séries temporais): CPU, latência,
linhas processadas por minuto, lag de consumo. São baratas, rápidas de consultar e ideais para **tendência,
dashboards e alertas**.

## Tipos de métrica (modelo Prometheus/OpenTelemetry)

| Tipo | O que é | Exemplo em dados |
| --- | --- | --- |
| **Counter** | valor que **só cresce** (reinicia em 0) | linhas processadas, erros, mensagens consumidas |
| **Gauge** | valor que **sobe e desce** | lag do consumer, tamanho da fila, memória, idade do dado |
| **Histogram** | distribuição de valores em *buckets* | duração de tarefas, latência de queries |
| **Summary** | quantis pré-calculados | (menos usado; prefira histogram) |

Calcule **taxas** de counters (`rate(rows_processed_total[5m])`) e **percentis** de histogramas (p95/p99) —
médias escondem caudas lentas.

## Prometheus + Grafana (o padrão de fato)

```text
App/exporter expõe /metrics ◄── Prometheus (scrape + armazena + PromQL) ──► Grafana (dashboards) / Alertmanager (alertas)
```

- **Pull model**: Prometheus *raspa* endpoints `/metrics`. Jobs batch **efêmeros** usam **Pushgateway** ou
  expõem métricas ao fim (cuidado com semântica).
- **PromQL** para consultas/alertas; **labels** (dimensões) dão granularidade.
- Alternativas gerenciadas: CloudWatch, Cloud Monitoring, Azure Monitor, Datadog; **OpenTelemetry** como
  padrão de instrumentação neutro.

## Instrumentando um pipeline (Python)

```python
from prometheus_client import Counter, Gauge, Histogram, start_http_server

ROWS = Counter("pipeline_rows_total", "Linhas processadas", ["table", "stage"])
REJECTED = Counter("pipeline_rows_rejected_total", "Linhas rejeitadas", ["table"])
DURATION = Histogram("pipeline_stage_seconds", "Duração por etapa", ["stage"])
LAST_OK = Gauge("pipeline_last_success_timestamp", "Epoch do último sucesso", ["pipeline"])

with DURATION.labels("transform").time():
    out = transform(df)
ROWS.labels("fct_vendas", "load").inc(len(out))
LAST_OK.labels("vendas").set_to_current_time()
```

`pipeline_last_success_timestamp` permite alertar "não roda há > 26h" (**dead man's switch**) e medir
[frescor](../06-data-freshness/README.md).

## Métricas essenciais para plataformas de dados

### Infra/serviços

CPU, memória, disco, rede; OOMKills/restarts ([K8s](../../21-kubernetes/08-observability/README.md)); conexões/
IOPS/replication lag de bancos ([managed DBs](../../19-cloud/04-managed-databases/README.md)).

### Pipelines

Taxa de sucesso/falha de runs, **duração** (e tendência), retries, tarefas na fila, atraso vs SLA.

### Dados

**Volume** (linhas/bytes por run), **frescor** (idade do dado), % de nulos, rejeitados, duplicatas,
resultados de testes de qualidade ([data quality](../../12-data-quality/README.md)).

### Streaming/brokers

**Consumer lag**, throughput in/out, tamanho de estado, checkpoint duration, backpressure
([backpressure](../../18-message-brokers/06-backpressure/README.md)).

### Custo

Bytes processados/créditos por pipeline ([cost](../../19-cloud/08-cost-management/README.md)).

## Métodos de organização

- **RED** (serviços): **R**ate, **E**rrors, **D**uration.
- **USE** (recursos): **U**tilization, **S**aturation, **E**rrors.
- **Golden signals** (SRE): latência, tráfego, erros, saturação.
- Para dados, some **frescor, volume e qualidade** ([data health](../06-data-freshness/README.md)).

## Cardinalidade (a armadilha)

Cada combinação única de **labels** vira uma série temporal. Labels de **alta cardinalidade** (`user_id`,
`order_id`, timestamps) **explodem** o armazenamento e derrubam o Prometheus. Use labels de baixa
cardinalidade (`table`, `stage`, `env`); IDs vão para [logs/traces](../01-logging/README.md).

## Dashboards

Poucos e **focados em perguntas** ("os dados de hoje estão prontos? o pipeline está saudável?"): estado atual

- tendência + SLO. Evite painéis infinitos que ninguém olha. Dashboard por **audiência** (engenheiro vs

consumidor de dados).

## Erros comuns

- Labels de alta cardinalidade.
- Olhar só médias (esconde p95/p99).
- Métricas só de infra e nenhuma de **dados**.
- Counters sem `rate` (valor absoluto sem sentido).
- Dashboards enormes sem propósito; métricas sem dono/alerta.
- Jobs efêmeros sem estratégia de exposição de métricas.

## Boas práticas

- Instrumente contagens, durações (histogram) e timestamp de último sucesso.
- Labels de baixa cardinalidade; nomes consistentes (`pipeline_stage_seconds`).
- Use RED/USE/golden signals + métricas de dados; ligue métricas a SLOs e alertas.

## Relação com outros conceitos

- [Logging](../01-logging/README.md), [alertas](../04-alerting/README.md), [SLI/SLO](../05-sli-slo-sla/README.md),
  [freshness](../06-data-freshness/README.md), [pipeline observability](../../10-data-pipelines/08-pipeline-observability/README.md).

## Exercícios

1. Instrumente um job com counter de linhas, histogram de duração e gauge de último sucesso.
2. Escreva (conceitualmente) a query PromQL para "linhas/s nos últimos 5 min" e "p95 de duração".
3. Explique por que `order_id` como label é um erro.
4. Proponha um dashboard de 6 painéis para uma plataforma Kafka→lake→warehouse.

## Referências

- Documentação do Prometheus (data model, instrumentation best practices), Grafana, OpenTelemetry Metrics.
- Google SRE Book — Monitoring Distributed Systems (golden signals).
