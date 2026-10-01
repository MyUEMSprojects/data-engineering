# Data freshness e saúde dos dados

> 🟣 Production · Parte de [24 — Observability](../README.md)

## O que é

**Data freshness (frescor)** mede **quão atualizado** está o dado — a defasagem entre "agora" e o evento/
carga mais recente. É o sinal mais simples e valioso da **observabilidade de dados**: se a tabela não
atualiza, todo o resto (dashboards, ML, decisões) fica errado **sem erro visível**. Este tópico trata do
frescor e dos demais sinais de **saúde dos dados**.

## O problema "verde mas errado"

Um pipeline pode terminar **sem erro** e ainda assim entregar dados **velhos, incompletos ou distorcidos**
(fonte parou de enviar, filtro excluiu tudo, schema mudou). Monitorar só a execução
([operacional](../../10-data-pipelines/08-pipeline-observability/README.md)) não pega isso. É preciso
observar **os próprios dados**.

## Os pilares da saúde dos dados

| Pilar | Pergunta | Sinal |
| --- | --- | --- |
| **Freshness** | está atualizado? | idade do dado mais recente; atraso vs SLA |
| **Volume** | chegou a quantidade esperada? | linhas/bytes por run vs histórico |
| **Schema** | a estrutura mudou? | colunas/tipos adicionados/removidos ([schema drift](../../12-data-quality/03-schema-validation/README.md)) |
| **Distribuição** | os valores fazem sentido? | % nulos, média/percentis, cardinalidade ([anomalias](../../12-data-quality/07-anomaly-detection/README.md)) |
| **Lineage** | o que foi afetado? | impacto a jusante ([lineage](../../10-data-pipelines/06-data-lineage/README.md)) |

## Medindo freshness

### Definições de "idade"

- **Idade da última carga**: `now() − max(loaded_at)` (quando o pipeline escreveu).
- **Idade do evento mais recente**: `now() − max(event_ts)` (quando o dado **realmente** ocorreu — mais
  fiel; um pipeline pode carregar dados velhos "frescos").
- **Latência fim-a-fim**: do evento à disponibilidade no destino.

Prefira **event time** quando existir; combine com *loaded_at*.

### Exemplos

```sql
-- idade do dado mais recente numa tabela
select extract(epoch from (now() - max(event_ts)))/3600 as horas_de_atraso
from fct_vendas;
```

```yaml
# dbt: freshness das fontes
sources:
  - name: raw
    tables:
      - name: pedidos
        loaded_at_field: _ingested_at
        freshness:
          warn_after:  {count: 6,  period: hour}
          error_after: {count: 12, period: hour}
```

`dbt source freshness` ([dbt tests/sources](../../28-dbt/03-sources-seeds/README.md)).

```python
# métrica exposta para alertar (dead man's switch)
LAST_OK.labels("vendas").set_to_current_time()      # ver métricas
# alerta: time() - pipeline_last_success_timestamp > 26h
```

## SLAs de frescor

Defina por dataset ([tiers](../05-sli-slo-sla/README.md)): "tier 1: dados do dia anterior até 06:00";
"streaming: atraso < 5 min". Alerte quando violado ([alertas](../04-alerting/README.md)). Distinga
**atraso esperado** (fim de semana/feriado, fonte batch semanal) de **anormal** — SLAs com **calendário**
evitam falsos positivos.

## Detectando volume e distribuição anômalos

- **Limiares estáticos** ("entre 10k e 20k linhas") — simples.
- **Baselines dinâmicos/sazonais** (média móvel ± Nσ; sazonalidade por dia da semana) — mais robustos
  ([anomaly detection](../../12-data-quality/07-anomaly-detection/README.md)).
- **Comparação com fonte** (reconciliação de contagens/somas origem↔destino) pega perdas silenciosas
  ([validação](../../09-etl-elt/10-data-validation/README.md)).

## Ferramentas

- **dbt** (source freshness, tests, `dbt_expectations`), **Elementary** (observabilidade sobre dbt).
- **Great Expectations / Soda** ([qualidade](../../12-data-quality/README.md)).
- **Plataformas de data observability**: Monte Carlo, Bigeye, Anomalo, Metaplane (anomalias automáticas,
  lineage).
- **Próprias**: métricas + Prometheus/Grafana + alertas; checagens SQL agendadas pelo orquestrador.

## Onde checar

- **Na ingestão** (fonte chegou? volume ok?); **por camada** (bronze→silver→gold) com gates no
  [DAG](../../10-data-pipelines/02-dags-dependencies/README.md); **contínuo** em produção (monitor independente
  do pipeline, pois o próprio pipeline pode estar morto).

> Importante: o **monitor de frescor deve ser independente** do pipeline que monitora — um pipeline que
> não roda não pode alertar que não rodou.

## Impacto e resposta

Combine com **lineage** para saber **quais dashboards/modelos/consumidores** são afetados e **comunicar**
proativamente ("dados de vendas atrasados; previsão 10h"). Marque datasets desatualizados no catálogo
([catalog](../../27-data-catalog-metadata/README.md)). Siga o processo de [incident response](../07-incident-response/README.md).

## Erros comuns

- Monitorar só "o job terminou" (verde mas errado).
- Medir frescor só por *loaded_at* (carga de dado velho parece fresca).
- Limiares estáticos que ignoram sazonalidade (falsos positivos em fim de semana).
- Monitor acoplado ao pipeline (cai junto).
- Sem SLA de frescor por dataset; sem comunicação aos consumidores.
- Sem reconciliação com a fonte.

## Boas práticas

- Frescor por event time + loaded_at; SLAs por tier, com calendário.
- Monitores independentes; volume/schema/distribuição junto; reconciliação.
- Alertas acionáveis ligados a lineage/impacto; comunicação proativa.
- Automatize com dbt/Elementary/GX/ferramentas de data observability.

## Relação com outros conceitos

- [SLI/SLO/SLA](../05-sli-slo-sla/README.md), [alertas](../04-alerting/README.md),
  [anomaly detection](../../12-data-quality/07-anomaly-detection/README.md),
  [pipeline observability](../../10-data-pipelines/08-pipeline-observability/README.md),
  [lineage](../../10-data-pipelines/06-data-lineage/README.md).

## Exercícios

1. Escreva a query e o alerta de frescor para uma tabela de eventos (event time) com SLA de 2h.
2. Explique a diferença entre idade pela última carga e pelo evento mais recente com um exemplo enganoso.
3. Defina o SLA de frescor (com calendário) de uma tabela alimentada por uma fonte que só envia em dias
   úteis.
4. Projete um monitor independente que alerte quando o próprio pipeline não rodou.

## Referências

- Moses, B. et al. *Data Quality Fundamentals* — data observability.
- Documentação do dbt (source freshness), Elementary, Great Expectations, Soda.
