# Tracing

> 🟣 Production · Parte de [24 — Observability](../README.md)

## O que é

**Tracing distribuído** acompanha **uma requisição/execução** conforme ela atravessa vários componentes
(serviços, filas, bancos), registrando **onde o tempo foi gasto e onde ocorreram erros**. Complementa
[logs](../01-logging/README.md) (o quê) e [métricas](../02-metrics/README.md) (quanto).

## Conceitos

- **Trace** — a jornada completa de uma operação (ex.: uma requisição de feature, um run de pipeline).
- **Span** — uma unidade de trabalho dentro do trace, com início/fim, nome, atributos e relação
  pai→filho.
- **Context propagation** — o `trace_id`/`span_id` viaja entre componentes (headers HTTP, mensagens Kafka)
  para costurar os spans.

```text
trace 7f3a…
 └─ span: API /features (120 ms)
     ├─ span: cache lookup (3 ms)
     ├─ span: query feature store (85 ms)   ← gargalo
     │    └─ span: db.query (80 ms)
     └─ span: serialize (10 ms)
```

Visualização (waterfall/flame graph) mostra o **caminho crítico** e o gargalo.

## OpenTelemetry (OTel)

Padrão aberto (CNCF) e neutro para **instrumentar** logs, métricas e traces, com SDKs por linguagem e um
**Collector** que recebe, processa e exporta para backends (Jaeger, Tempo, Zipkin, Datadog, X-Ray, Cloud
Trace). Instrumente uma vez; troque o backend sem reescrever.

```python
from opentelemetry import trace
tracer = trace.get_tracer("etl-vendas")

with tracer.start_as_current_span("transform", attributes={"table": "fct_vendas"}) as span:
    out = transform(df)
    span.set_attribute("rows_out", len(out))
```

Auto-instrumentação cobre frameworks/clientes comuns (requests, psycopg, Kafka clients, Flask/FastAPI).

## Onde tracing ajuda em dados

- **Serving online** (APIs de features/modelos, feature store online): latência fim-a-fim, gargalos entre
  serviço→cache→DB ([DE + ML](../../31-data-engineering-and-ml/README.md)).
- **Pipelines orientados a eventos/streaming**: seguir um evento do produtor ao consumidor/sink
  ([EDA](../../17-streaming/02-event-driven-architecture/README.md), propagando contexto nos headers do
  Kafka).
- **Orquestração**: relacionar tarefas de um DAG/run e chamadas a sistemas externos.
- **Diagnosticar latência** em consultas encadeadas/microsserviços de dados.

## Onde é menos central

Em **batch puro** (jobs grandes e pouco distribuídos), tracing por requisição rende menos que **logs +
métricas + lineage**. Para "de onde veio este dado?" o instrumento é o
[lineage](../../10-data-pipelines/06-data-lineage/README.md), não o trace. Não confunda:

| | Trace | Lineage |
| --- | --- | --- |
| Rastreia | uma **execução** (tempo/erro) | o **fluxo dos dados** entre datasets |
| Pergunta | "por que esta requisição foi lenta?" | "de onde veio esta coluna/que depende dela?" |

## Amostragem (sampling)

Rastrear 100% das requisições é caro. Estratégias:

- **Head-based** — decide no início (ex.: 5% das requisições).
- **Tail-based** — decide no fim, mantendo traces **lentos ou com erro** (mais útil, exige coletor com
  buffer).
- Sempre amostre **erros** e **outliers**.

## Correlação com logs e métricas

Inclua `trace_id` nos [logs](../01-logging/README.md): do trace lento, pule para os logs exatos daquela
execução; **exemplars** ligam um ponto de métrica a um trace. É a verdadeira observabilidade: navegar
entre os três pilares.

## Custo e privacidade

- Volume de spans pode ser enorme: sampling, filtros, retenção curta.
- **Não** coloque PII/segredos em atributos de span ([masking](../../26-security/07-data-masking-pii/README.md)).

## Erros comuns

- Contexto não propagado (traces quebrados em pedaços) — esquecer headers de mensagem/HTTP.
- 100% de amostragem sem orçamento; ou amostragem que descarta justamente os erros.
- Tentar usar tracing no lugar de lineage (ou vice-versa).
- Spans com PII; atributos de alta cardinalidade sem necessidade.
- Instrumentar tudo sem objetivo (ruído).

## Boas práticas

- OpenTelemetry + Collector; propagar contexto em HTTP e mensageria.
- Sampling tail-based para erros/lentidão; `trace_id` em todos os logs.
- Instrumente as fronteiras (entrada/saída/DB/rede), com atributos úteis e de baixa sensibilidade.
- Use onde há **caminho distribuído** e latência importa (serving, streaming).

## Relação com outros conceitos

- [Logging](../01-logging/README.md), [métricas](../02-metrics/README.md),
  [lineage](../../10-data-pipelines/06-data-lineage/README.md), [streaming/EDA](../../17-streaming/02-event-driven-architecture/README.md),
  [pipeline observability](../../10-data-pipelines/08-pipeline-observability/README.md).

## Exercícios

1. Desenhe um trace (spans) de uma requisição de feature online e identifique o gargalo.
2. Explique como propagar o contexto de trace através de uma mensagem Kafka.
3. Diferencie trace e lineage com um exemplo de pergunta que cada um responde.
4. Defina uma política de sampling que preserve erros e execuções lentas.

## Referências

- Documentação do OpenTelemetry (traces, context propagation, sampling); Jaeger/Tempo.
- Majors, C. et al. *Observability Engineering*.
