# Anomaly detection

> 🔵 Pipelines · Parte de [12 — Data Quality](../README.md)

## O que é

**Detecção de anomalias** em qualidade de dados é identificar **automaticamente** quando os
dados se desviam do comportamento esperado — sem que você precise escrever uma regra explícita
para cada caso. Enquanto [expectation testing](../04-expectation-testing/README.md) verifica
regras que você **conhece** ("valor >= 0"), anomaly detection pega o que você **não antecipou**
("o volume caiu 70% hoje, isso nunca acontece").

## Por que é necessário

Você não consegue escrever uma regra explícita para toda forma de dado dar errado. Anomalias
captam o **inesperado**:

- Volume despencou (uma fonte parou de enviar).
- Frescor atrasou (pipeline travou).
- A média de uma métrica saltou (bug de unidade/moeda).
- % de nulos subiu (coluna quebrou na origem).
- Uma distribuição mudou de forma (mudança silenciosa de schema/semântica).

Esses são os sinais dos piores incidentes: o pipeline fica **verde** mas os dados estão errados.

## O que monitorar (os sinais)

Alinha-se aos pilares de [observabilidade de dados](../../10-data-pipelines/08-pipeline-observability/README.md):

| Sinal | Anomalia típica |
| --- | --- |
| **Volume** | nº de linhas muito acima/abaixo do padrão |
| **Frescor** | dado não atualiza no prazo ([freshness](../../24-observability/06-data-freshness/README.md)) |
| **Distribuição** | média/desvio/percentis fora do histórico |
| **Nulos/completude** | % de nulos foge do normal |
| **Cardinalidade** | nº de valores distintos muda bruscamente |
| **Schema** | coluna aparece/some/muda de tipo ([schema](../03-schema-validation/README.md)) |

## Abordagens (do simples ao sofisticado)

### 1. Limiares estáticos (thresholds)

Regras fixas: "volume entre 10k e 20k". Simples e previsível, mas rígido — não acompanha
sazonalidade/crescimento e gera falsos positivos/negativos. Na prática, é
[expectation testing](../04-expectation-testing/README.md) de volume/distribuição.

### 2. Limiares dinâmicos (estatísticos)

Comparar com o **histórico**: média móvel ± N desvios-padrão, intervalos baseados em
percentis, ou detecção de *outliers* (z-score, IQR). Acompanha tendências melhor que limiares
fixos.

### 3. Baseado em tempo/sazonalidade

Modelos que entendem padrões sazonais (dia da semana, feriados): "segunda de manhã sempre tem
pouco volume" não é anomalia. Ferramentas usam séries temporais para isso.

### 4. ML / detecção automática

Ferramentas comerciais (Monte Carlo, Anomalo, Bigeye) e abertas (Elementary, re_data) aprendem
o comportamento normal de cada tabela/coluna e alertam em desvios — reduzindo a necessidade de
configurar regras manualmente. Útil em escala (milhares de tabelas).

## Thresholds vs anomaly detection

| | Expectativas/thresholds | Anomaly detection |
| --- | --- | --- |
| Pega | o que você **conhece** | o **inesperado** |
| Configuração | manual, explícita | aprende do histórico |
| Falsos positivos | baixos (se bem feitos) | podem ser altos (requer tuning) |
| Escala | trabalhoso em milhares de tabelas | escala melhor |

São **complementares**: use regras explícitas para o crítico e conhecido; anomaly detection
para cobrir o resto e o desconhecido.

## O desafio: falsos positivos e alert fatigue

Detecção sensível demais gera muitos alertas falsos → o time ignora (e perde o alerta real).
Detecção frouxa deixa passar problemas. Calibrar a sensibilidade e **direcionar alertas ao dono
do dado** é essencial (ver [ownership](../../25-data-governance/04-ownership-stewardship/README.md),
[observabilidade](../../10-data-pipelines/08-pipeline-observability/README.md)). Agrupe alertas e
use severidades.

## Onde roda

Como monitoramento contínuo sobre as tabelas de produção (não só no gate do pipeline): coleta
métricas por execução/tabela, compara com o histórico, e **alerta** quando desvia. Combina com
[lineage](../../10-data-pipelines/06-data-lineage/README.md) para mostrar o impacto a jusante.

## Erros comuns

- Só thresholds estáticos (falham com sazonalidade/crescimento).
- Detecção sensível demais → alert fatigue → alertas ignorados.
- Monitorar só volume e esquecer frescor/distribuição/nulos.
- Alertas sem dono (ninguém age).
- Confiar só em anomaly detection e abrir mão das regras explícitas críticas.

## Boas práticas

- Combine regras explícitas (crítico/conhecido) + anomaly detection (inesperado).
- Use limiares dinâmicos/sazonais em vez de só estáticos.
- Calibre a sensibilidade; agrupe alertas; direcione ao dono.
- Monitore vários sinais (volume, frescor, distribuição, nulos, schema).
- Integre com lineage para impacto.

## Relação com outros conceitos

- Complementa [expectation testing](../04-expectation-testing/README.md) e
  [schema validation](../03-schema-validation/README.md).
- [Observabilidade de dados](../../10-data-pipelines/08-pipeline-observability/README.md),
  [freshness](../../24-observability/06-data-freshness/README.md),
  [incident response](../../24-observability/07-incident-response/README.md).

## Exercícios

1. Projete uma detecção de anomalia de volume com limiar dinâmico (média móvel ± Nσ) em vez de
   fixo.
2. Dê 3 exemplos de incidentes que anomaly detection pega mas expectativas explícitas não.
3. Explique o trade-off entre sensibilidade e alert fatigue e como calibrar.
4. Descreva como combinar anomaly detection com lineage para responder a um incidente.

## Referências

- Moses, B. et al. *Data Quality Fundamentals* — data observability e anomalias.
- Documentação de Elementary, re_data; ferramentas Monte Carlo/Soda.
