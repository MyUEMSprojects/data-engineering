# dbt tests

> 🔵 Pipelines · Parte de [12 — Data Quality](../README.md)

## O que é

**dbt tests** são verificações de qualidade declaradas junto dos modelos no
[dbt](../../28-dbt/README.md), executadas como consultas SQL no warehouse. São a forma mais
simples e integrada de validar dados em um stack ELT moderno — qualidade **como parte do código
de transformação**.

> Este tópico foca nos **testes**; o dbt como um todo está no
> [módulo 28 — dbt](../../28-dbt/README.md).

## Por que são tão usados

- **Integrados ao modelo** — o teste vive ao lado da transformação, versionado em Git.
- **Simples** — testes comuns são uma linha de YAML.
- **Rodam no warehouse** — usam o poder do SQL; `dbt test`/`dbt build` executa tudo.
- **Documentação viva** — os testes declaram as regras do modelo (viram um
  [contrato](../02-data-contracts/README.md) de facto).

## Testes genéricos (built-in)

Declarados no YAML do modelo, em colunas:

```yaml
models:
  - name: fct_vendas
    columns:
      - name: id
        tests:
          - unique
          - not_null
      - name: status
        tests:
          - accepted_values:
              values: ['pago', 'cancelado', 'aberto']
      - name: cliente_sk
        tests:
          - relationships:              # integridade referencial
              to: ref('dim_cliente')
              field: cliente_sk
```

Os 4 testes built-in cobrem as dimensões mais comuns (ver
[dimensões](../01-dimensions-of-quality/README.md)):

| Teste | Dimensão |
| --- | --- |
| `unique` | unicidade |
| `not_null` | completude |
| `accepted_values` | validade (domínio) |
| `relationships` | integridade referencial / consistência |

## Testes singulares (singular tests)

Para regras customizadas, escreva uma query SQL em `tests/` que **retorna as linhas que
violam** a regra — se retornar linhas, o teste falha.

```sql
-- tests/assert_total_bate_com_itens.sql
select v.id
from {{ ref('fct_vendas') }} v
join (select pedido_id, sum(preco*qtd) as total_itens
      from {{ ref('stg_itens') }} group by 1) i on i.pedido_id = v.id
where abs(v.total - i.total_itens) > 0.01   -- inconsistência
```

## dbt_expectations e dbt_utils (pacotes)

Para testes mais ricos (volume, distribuição, frescor, formato), o pacote **`dbt_expectations`**
(inspirado em [Great Expectations](../05-great-expectations/README.md)) e o **`dbt_utils`**
adicionam dezenas de testes:

```yaml
tests:
  - dbt_expectations.expect_column_values_to_be_between:
      min_value: 0
  - dbt_utils.expression_is_true:
      expression: "valor >= desconto"
```

## Severidade: error vs warn

```yaml
tests:
  - not_null:
      config:
        severity: warn        # alerta mas não falha o build
        warn_if: ">10"
        error_if: ">100"
```

Isso mapeia a distinção **hard vs soft** (ver
[expectation testing](../04-expectation-testing/README.md)): `error` bloqueia, `warn` alerta.

## Frescor de fontes (source freshness)

dbt verifica se as **fontes** estão atualizadas:

```yaml
sources:
  - name: raw
    tables:
      - name: pedidos
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
        loaded_at_field: _ingested_at
```

`dbt source freshness` detecta dados velhos (ver
[freshness](../../24-observability/06-data-freshness/README.md)).

## Como roda no pipeline

- `dbt test` — roda só os testes.
- `dbt build` — roda modelos **e** seus testes na ordem do DAG (se um modelo falha nos testes, os
  dependentes não são construídos). É o modo recomendado.
- No [CI](../../23-cicd-dataops/README.md): rodar `dbt build` contra um ambiente de teste a cada
  PR; em produção, como gate do [pipeline](../../10-data-pipelines/README.md).

## dbt tests vs Great Expectations

- **dbt tests** — simples, dentro do warehouse/dbt, ótimo para validações SQL dos modelos.
- **[Great Expectations](../05-great-expectations/README.md)** — framework mais rico, estatístico,
  com Data Docs, e funciona fora do warehouse (pandas/Spark).

Use dbt tests como base no warehouse; adicione GX/`dbt_expectations` para regras estatísticas/
mais ricas. Complementares.

## Erros comuns

- Modelos sem **nenhum** teste (chave sem `unique`/`not_null`).
- Rodar `dbt run` (sem testes) em produção em vez de `dbt build`.
- Tudo como `error` (um warn trava o build) ou tudo `warn` (erros graves passam).
- Não testar frescor das fontes.

## Boas práticas

- Teste toda chave (`unique` + `not_null`) e domínios (`accepted_values`); use `relationships`.
- Severidade adequada (hard=error, soft=warn).
- `dbt build` em CI e em produção (testes como gate).
- Adicione `dbt_expectations` para volume/distribuição/frescor; teste `source freshness`.

## Relação com outros conceitos

- Parte do [dbt](../../28-dbt/README.md) (ver [dbt tests no módulo 28](../../28-dbt/05-tests/README.md)).
- Implementa [expectation testing](../04-expectation-testing/README.md) e
  [dimensões](../01-dimensions-of-quality/README.md).
- Alternativa/complemento: [Great Expectations](../05-great-expectations/README.md).

## Exercícios

1. Adicione testes `unique`, `not_null`, `accepted_values` e `relationships` a um modelo dbt.
2. Escreva um teste singular que verifica `total == Σ itens`.
3. Configure um teste com severidade `warn` até certo limite e `error` acima dele.
4. Configure `source freshness` para alertar quando a fonte atrasar.

## Referências

- Documentação do dbt — Tests, Severity, Source freshness.
- Pacotes `dbt_utils` e `dbt_expectations` (dbt Hub).
