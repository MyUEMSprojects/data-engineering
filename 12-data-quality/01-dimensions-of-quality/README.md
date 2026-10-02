# Dimensões de qualidade

> 🔵 Pipelines · Parte de [12 — Data Quality](../README.md)

## O que é

"Qualidade de dados" é vago até você decompô-lo em **dimensões** mensuráveis. Cada dimensão
responde a uma pergunta específica sobre os dados e pode virar um **teste** concreto. Pensar em
dimensões transforma "os dados parecem ruins" em verificações objetivas.

## As dimensões principais

### Completude (completeness)

Os dados esperados estão **presentes**? Há valores faltando onde não deveria?

- Testes: % de nulos em colunas obrigatórias; nº de linhas vs esperado; "todas as lojas
  reportaram hoje?".

### Acurácia (accuracy)

Os dados **refletem a realidade**? (É a mais difícil de medir — exige uma fonte de verdade.)

- Testes: reconciliação com a fonte (soma no warehouse == na origem); comparação com sistema
  de referência; faixas plausíveis.

### Consistência (consistency)

Os dados são **coerentes** entre si e entre sistemas? O mesmo fato dá o mesmo valor em lugares
diferentes?

- Testes: `total == soma dos itens`; o faturamento no relatório A == no relatório B; integridade
  referencial ([FK existe](../../05-sql/09-constraints/README.md)).

### Validade (validity)

Os valores estão no **formato/domínio** correto?

- Testes: `status in ('pago','cancelado',...)`; e-mail com formato válido; data plausível;
  `valor >= 0`.

### Unicidade (uniqueness)

Não há **duplicatas** indevidas?

- Testes: chave primária/natural única ([dedupe](../../09-etl-elt/09-deduplication/README.md)).

### Pontualidade / frescor (timeliness / freshness)

Os dados estão **atualizados** e chegaram **no prazo**?

- Testes: última carga há < X horas; dados do dia prontos até Y (ver
  [freshness](../../24-observability/06-data-freshness/README.md),
  [SLA](../../24-observability/05-sli-slo-sla/README.md)).

### Outras dimensões citadas

- **Integridade (integrity)** — relacionamentos válidos (FKs).
- **Precisão (precision)** — granularidade/casas decimais adequadas.

## Resumo (dimensão → pergunta → teste)

| Dimensão | Pergunta | Exemplo de teste |
| --- | --- | --- |
| Completude | está tudo lá? | `not_null`, contagem de linhas |
| Acurácia | reflete a realidade? | reconciliação com a fonte |
| Consistência | é coerente? | `total = Σ itens`, FK íntegra |
| Validade | formato/domínio ok? | `accepted_values`, regex, faixa |
| Unicidade | sem duplicatas? | `unique` na chave |
| Frescor | está atualizado? | idade da última carga < X |

## Qualidade é relativa ao uso

"Qualidade boa" depende do **propósito**: um dado aproximado pode servir para uma tendência mas
não para um relatório fiscal. Defina as expectativas **com os consumidores** — vira a base de
[data contracts](../02-data-contracts/README.md) e de SLAs de dados.

## Prevenir, detectar, corrigir

- **Prevenir** — [constraints](../../05-sql/09-constraints/README.md), validação na
  [ingestão](../../09-etl-elt/10-data-validation/README.md), contratos, idempotência.
- **Detectar** — [testes de dados](../04-expectation-testing/README.md), monitoramento de
  [anomalias](../07-anomaly-detection/README.md),
  [observabilidade](../../10-data-pipelines/08-pipeline-observability/README.md).
- **Corrigir** — quarentena, reprocessamento/[backfill](../../09-etl-elt/08-backfill/README.md),
  correção na fonte.

Prevenir é mais barato que detectar, que é mais barato que corrigir depois do estrago.

## Como medir e acompanhar

Transforme dimensões em **métricas** acompanhadas no tempo (ex.: % de nulos, nº de duplicatas,
frescor) e exiba num dashboard de qualidade (ver
[observabilidade de pipeline](../../10-data-pipelines/08-pipeline-observability/README.md)).
Qualidade que não é medida regride.

## Erros comuns

- Tratar qualidade como sensação vaga em vez de dimensões testáveis.
- Focar só em schema/completude e ignorar consistência/frescor.
- Definir "qualidade" sem os consumidores (expectativas erradas).
- Medir uma vez e nunca mais (qualidade regride com o tempo).

## Boas práticas

- Decomponha em dimensões; crie um teste por dimensão relevante.
- Defina expectativas com os consumidores (contratos/SLAs).
- Previna na origem; detecte com testes/monitoramento; tenha plano de correção.
- Acompanhe métricas de qualidade ao longo do tempo.

## Relação com outros conceitos

- Implementadas por [schema validation](../03-schema-validation/README.md),
  [expectation testing](../04-expectation-testing/README.md),
  [dbt tests](../06-dbt-tests/README.md),
  [Great Expectations](../05-great-expectations/README.md).
- [Validação no pipeline](../../09-etl-elt/10-data-validation/README.md),
  [contracts](../02-data-contracts/README.md), [governança](../../25-data-governance/README.md).

## Exercícios

1. Para uma tabela de pedidos, escreva um teste concreto para cada dimensão de qualidade.
2. Dê um exemplo de dado que é "bom o suficiente" para um uso e "ruim" para outro.
3. Classifique 5 problemas de dados reais nas dimensões correspondentes.
4. Defina 3 métricas de qualidade para acompanhar no tempo.

## Referências

- Moses, B. et al. *Data Quality Fundamentals*. O'Reilly.
- DAMA-DMBOK — dimensões de qualidade de dados.
- Reis & Housley, *Fundamentals of Data Engineering*.
