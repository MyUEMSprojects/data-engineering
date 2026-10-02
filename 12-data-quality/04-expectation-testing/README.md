# Expectation testing

> 🔵 Pipelines · Parte de [12 — Data Quality](../README.md)

## O que é

**Expectation testing** (teste baseado em expectativas) é declarar **afirmações verificáveis
sobre os dados** ("espero que a coluna `id` seja única e não-nula", "espero que `valor >= 0`",
"espero entre 10k e 20k linhas por dia") e verificá-las automaticamente a cada execução. É a
forma mais prática de operacionalizar as [dimensões de qualidade](../01-dimensions-of-quality/README.md).

Diferente de [testar código](../../10-data-pipelines/07-pipeline-testing/README.md) (que roda
em CI sobre dados de exemplo), expectation testing roda **em runtime sobre os dados reais** —
pega o "o dado de hoje veio ruim".

## Anatomia de uma expectativa

Uma expectativa tem: **alvo** (coluna/tabela), **regra** (condição) e **ação em falha**
(bloquear/alertar/quarentenar).

```text
expect: coluna "id"        seja única          → senão: bloquear
expect: coluna "valor"     >= 0                 → senão: quarentenar linhas
expect: contagem de linhas entre 10k e 20k      → senão: alertar
expect: coluna "status"    in ('pago','cancelado') → senão: bloquear
```

## Tipos de expectativa (do básico ao estatístico)

| Categoria | Exemplos |
| --- | --- |
| **Not-null / completude** | coluna sem nulos; % de nulos < X |
| **Unicidade** | PK/natural key única |
| **Faixa / domínio** | `valor BETWEEN 0 AND 1e6`; `status IN (...)` |
| **Formato** | e-mail/CPF casam regex; data válida |
| **Referência** | toda FK existe na dimensão |
| **Volume** | nº de linhas dentro do esperado |
| **Frescor** | dado mais recente que X |
| **Distribuição** | média/desvio/percentil dentro de limites (estatístico) |
| **Relacional** | `total == Σ itens` (consistência entre colunas) |

As estatísticas (distribuição, volume) aproximam a fronteira com
[anomaly detection](../07-anomaly-detection/README.md).

## Onde as expectativas rodam

Modeladas como um **gate** no [DAG](../../10-data-pipelines/02-dags-dependencies/README.md): a
etapa seguinte só prossegue se as expectativas passarem (ver
[validação](../../09-etl-elt/10-data-validation/README.md)).

```text
transform ─► [verificar expectativas] ─✓─► publicar marts
                       └─✗─► bloquear / alertar / quarentena
```

## Ferramentas

- **[Great Expectations](../05-great-expectations/README.md)** — framework dedicado, com
  catálogo grande de *expectations*, *data docs* e relatórios.
- **[dbt tests](../06-dbt-tests/README.md)** — expectativas declaradas no YAML do modelo
  (`unique`, `not_null`, `accepted_values`, `relationships`) + pacote `dbt_expectations`.
- **Pandera** — expectativas sobre DataFrames.
- **Soda** (SodaCL) — expectativas em YAML, voltado a monitoramento.
- **Asserts** em código — o mais simples (ver
  [validação](../../09-etl-elt/10-data-validation/README.md)).

## Hard vs soft expectations

- **Hard** (críticas) → **bloqueiam** o pipeline (ex.: PK duplicada, schema quebrado).
- **Soft** (avisos) → **alertam/quarentenam** mas deixam seguir (ex.: % de nulos subiu um
  pouco).

Classificar cada expectativa por severidade evita tanto travar tudo por um detalhe quanto
ignorar um problema grave.

## Expectativas como documentação viva

Um conjunto de expectativas **documenta** o que o dado deveria ser — é a forma executável de um
[data contract](../02-data-contracts/README.md). Novos membros do time entendem as regras
lendo as expectativas.

## Erros comuns

- Nenhuma expectativa → dados ruins passam silenciosamente.
- Só expectativas básicas (not-null) e esquecer volume/distribuição/consistência.
- Tudo como *hard* (um detalhe trava o pipeline) ou tudo *soft* (problemas graves ignorados).
- Expectativas que ninguém mantém (ficam desatualizadas e geram ruído/falsos positivos).

## Boas práticas

- Cubra as [dimensões](../01-dimensions-of-quality/README.md) relevantes com expectativas.
- Classifique por severidade (hard/soft) e defina a ação.
- Rode como gate no DAG; registre resultados (observabilidade).
- Trate expectativas como código versionado; revise-as quando o negócio muda.

## Relação com outros conceitos

- Implementa [dimensões de qualidade](../01-dimensions-of-quality/README.md) e
  [contratos](../02-data-contracts/README.md).
- Ferramentas: [Great Expectations](../05-great-expectations/README.md),
  [dbt tests](../06-dbt-tests/README.md).
- [Validação no pipeline](../../09-etl-elt/10-data-validation/README.md),
  [anomaly detection](../07-anomaly-detection/README.md).

## Exercícios

1. Escreva um conjunto de expectativas (not-null, unique, faixa, referência, volume) para uma
   tabela de pedidos.
2. Classifique cada uma como hard ou soft e defina a ação em falha.
3. Implemente-as como gate num pipeline (bloquear vs quarentenar).
4. Explique por que expectativas de volume/distribuição pegam problemas que not-null não pega.

## Referências

- Documentação de Great Expectations, dbt tests (`dbt_expectations`), Soda, Pandera.
- Moses, B. et al. *Data Quality Fundamentals*.
