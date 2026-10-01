# SLI, SLO e SLA

> 🟣 Production · Parte de [24 — Observability](../README.md)

## O que é

Vocabulário (da prática SRE) para **definir e medir confiabilidade de forma objetiva**:

- **SLI (Service Level Indicator)** — uma **métrica** que mede um aspecto do serviço (ex.: % de runs
  concluídos até 06:00; idade do dado).
- **SLO (Service Level Objective)** — a **meta interna** para o SLI (ex.: "99% dos dias, dados prontos até
  06:00").
- **SLA (Service Level Agreement)** — **acordo contratual** com consequências (financeiras/legais) se o
  nível prometido for descumprido (normalmente menos rígido que o SLO).

```text
SLI  = o que medimos       (ex.: % de dias em que a tabela ficou pronta até 06:00)
SLO  = a meta              (≥ 99% em 30 dias)
SLA  = a promessa + penalidade (≥ 95% ou crédito/multa)   [SLA ⊂ menos ambicioso que SLO]
```

## Por que importa

Sem metas explícitas, "confiável" é opinião: alguém reclama, o time corre. Com SLOs, **você sabe o que
significa "bom o bastante"**, decide **o que priorizar** (confiabilidade vs funcionalidades), gera
**alertas relevantes** ([burn rate](../04-alerting/README.md)) e **alinha expectativas** com os consumidores
dos dados.

## Escolhendo bons SLIs

Meça o que **o usuário/consumidor sente**, não o que é fácil. Estrutura: `eventos bons / eventos válidos`.

### SLIs para dados (os mais úteis)

| Dimensão | SLI exemplo |
| --- | --- |
| **Frescor / pontualidade** | % do tempo em que a tabela X tem dado com idade < 2h; % de dias entregues até 06:00 ([freshness](../06-data-freshness/README.md)) |
| **Completude/volume** | % de runs com volume dentro de ±20% do esperado |
| **Correção/qualidade** | % de testes de qualidade críticos passando; % de linhas válidas |
| **Disponibilidade** | % de consultas ao serving que respondem com sucesso |
| **Latência** | p95 da latência de feature online; duração do pipeline |
| **Taxa de sucesso do pipeline** | % de runs bem-sucedidos sem intervenção |

Alinhe às [dimensões de qualidade](../../12-data-quality/01-dimensions-of-quality/README.md).

## Definindo SLOs

- **Baseie em necessidade real** dos consumidores (relatório diário às 08:00 → dados prontos até 06:00),
  não em perfeição. **100% é a meta errada** (custo exponencial; impede mudanças).
- Formato: **meta + janela** ("99% dos dias em 30 dias corridos").
- **Poucos e significativos** por serviço/dataset crítico (priorize tabelas "tier 1").
- Documente: o que mede, como, quem é o dono, o que acontece ao violar.

### Error budget (orçamento de erro)

`orçamento = 100% − SLO`. Um SLO de 99% em 30 dias permite ~7,2 h de "falha". Esse orçamento é
**gasto** com incidentes **e** com mudanças arriscadas:

- Orçamento sobrando → pode entregar mais rápido, arriscar.
- Orçamento esgotado → **congele mudanças** e invista em confiabilidade.

Transforma a tensão "velocidade × estabilidade" numa decisão baseada em dados, e dá base ao **alerta por
burn rate** ([alertas](../04-alerting/README.md)).

## SLA em dados

SLAs para consumidores internos/externos ("dados do dia disponíveis até 08:00 úteis"). Regras:

- **SLA menos rígido que o SLO** (folga entre promessa e meta interna).
- Defina **escopo, medição, exclusões** (manutenção, falha da fonte de terceiros) e consequências.
- **Contratos de dados** ([data contracts](../../29-data-contracts/README.md)) formalizam frescor/qualidade
  como parte do acordo produtor↔consumidor.

## Medindo e acompanhando

- Instrumente os SLIs ([métricas](../02-metrics/README.md), checagens de frescor/qualidade) e calcule o
  atendimento do SLO em janela móvel.
- **Dashboard de SLO**: atual vs meta, orçamento restante, burn rate.
- **Revisão periódica** (mensal/trimestral): os SLOs ainda refletem a necessidade? foram violados? por quê?
- Relacione incidentes a SLOs ([incident response](../07-incident-response/README.md)).

## Exemplo completo

```text
Dataset: fct_vendas (tier 1; consumido pelo dashboard executivo)
SLI:  % de dias úteis em que fct_vendas é atualizada com dados do dia anterior até 06:00
SLO:  ≥ 99% em 30 dias  (orçamento: ~0,3 dia/mês)
SLA:  ≥ 95% por trimestre (contrato com a diretoria; revisão se violado)
Alerta: burn rate rápido (>14× em 1h) → page; lento (>2× em 6h) → ticket
```

## Erros comuns

- SLI que não reflete a experiência do consumidor (ex.: "job rodou" em vez de "dado correto e no prazo").
- Meta de 100% ou arbitrária sem conversar com consumidores.
- Muitos SLOs (ninguém acompanha).
- SLA igual/mais rígido que o SLO interno (sem margem).
- SLOs sem consequência (não orientam decisões).
- Não instrumentar → SLO "de papel".

## Boas práticas

- Poucos SLIs centrados no consumidor; SLOs realistas com janela e dono; error budget como política.
- SLA com folga, escopo claro e medição acordada; contratos de dados.
- Dashboard e revisão periódica; alertas por burn rate.

## Relação com outros conceitos

- [Métricas](../02-metrics/README.md), [alertas](../04-alerting/README.md),
  [freshness](../06-data-freshness/README.md), [data quality](../../12-data-quality/README.md),
  [data contracts](../../29-data-contracts/README.md), [incident response](../07-incident-response/README.md).

## Exercícios

1. Defina SLI, SLO e SLA para a tabela de vendas diária consumida por um dashboard executivo.
2. Calcule o orçamento de erro (em horas) de um SLO de 99,5% em 30 dias.
3. Por que "100% de disponibilidade" é uma meta ruim? O que fazer quando o orçamento acaba?
4. Escolha 3 SLIs para um serviço de features online e para um pipeline batch.

## Referências

- Google SRE Book — Service Level Objectives; *The SRE Workbook* — Implementing SLOs.
- Reis & Housley, *Fundamentals of Data Engineering* — SLAs/SLOs de dados.
