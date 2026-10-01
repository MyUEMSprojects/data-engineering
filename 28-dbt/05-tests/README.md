# Tests (dbt)

> 🔵 Analytics Platforms · Parte de [28 — dbt](../README.md)

## O que é

**dbt tests** são verificações de [qualidade de dados](../../12-data-quality/README.md) declaradas no
projeto e executadas como SQL no [warehouse](../../13-data-warehouse/README.md). São a forma de
garantir que seus [models](../02-models/README.md) produzem dados corretos — qualidade como parte do
código de transformação.

> Este tópico é a visão **dbt** dos testes; a fundamentação de qualidade está em
> [12 — Data Quality / dbt tests](../../12-data-quality/06-dbt-tests/README.md). Aqui focamos na
> prática dentro do projeto dbt.

## Testes genéricos (os 4 built-in)

Declarados no YAML, por coluna:

```yaml
# models/marts/_marts.yml
models:
  - name: fct_vendas
    columns:
      - name: id
        tests: [unique, not_null]
      - name: status
        tests:
          - accepted_values: {values: ['pago','cancelado','aberto']}
      - name: cliente_sk
        tests:
          - relationships: {to: ref('dim_cliente'), field: cliente_sk}
```

| Teste | Garante |
| --- | --- |
| `unique` | sem duplicatas (unicidade) |
| `not_null` | sem nulos (completude) |
| `accepted_values` | valores dentro de um domínio (validade) |
| `relationships` | integridade referencial (toda FK existe) |

## Testes singulares (SQL customizado)

Uma query em `tests/` que **retorna as linhas que violam** a regra — se retornar ≥1 linha, falha.

```sql
-- tests/assert_valor_nao_negativo.sql
select id from {{ ref('fct_vendas') }} where valor < 0
```

Use para regras de negócio específicas (ex.: `total == Σ itens`, consistência entre colunas).

## Testes genéricos customizados (reutilizáveis)

Um teste parametrizável definido como macro (ver [macros/Jinja](../06-macros-jinja/README.md)),
reutilizável em várias colunas/models — DRY para regras recorrentes.

## Pacotes: dbt_utils e dbt_expectations

Para testes mais ricos (volume, distribuição, formato, frescor), instale pacotes do dbt Hub:

```yaml
tests:
  - dbt_utils.expression_is_true: {expression: "valor >= desconto"}
  - dbt_expectations.expect_column_values_to_be_between: {min_value: 0}
  - dbt_expectations.expect_table_row_count_to_be_between: {min_value: 1000}
```

`dbt_expectations` traz o espírito do [Great Expectations](../../12-data-quality/05-great-expectations/README.md)
para o dbt.

## Severidade (hard vs soft)

```yaml
tests:
  - not_null:
      config:
        severity: warn           # avisa, não falha o build
        error_if: ">100"         # vira erro acima de 100 falhas
        warn_if: ">0"
```

Mapeia hard (`error`, bloqueia) vs soft (`warn`, alerta) — ver
[expectation testing](../../12-data-quality/04-expectation-testing/README.md).

## Source freshness (teste de frescor)

Além dos testes de dados, `dbt source freshness` verifica se as [fontes](../03-sources-seeds/README.md)
estão atualizadas (ver [tests de dados/freshness](../../12-data-quality/06-dbt-tests/README.md)).

## Unit tests (lógica de transformação)

Versões recentes do dbt suportam **unit tests**: dado um input fixo, verifica o output de um model —
testa a **lógica SQL** (não os dados em runtime). Complementa os data tests (ver
[pipeline testing](../../10-data-pipelines/07-pipeline-testing/README.md)).

## Como roda

```bash
dbt test                     # roda só os testes
dbt test --select fct_vendas # testes de um model
dbt build                    # run + test na ordem do DAG (RECOMENDADO)
```

`dbt build` constrói e testa na ordem do [DAG](../../10-data-pipelines/02-dags-dependencies/README.md):
se um model falha nos testes, os **dependentes não são construídos** — impedindo que dados ruins
propaguem.

## No pipeline / CI

- **CI** ([CI/CD](../../23-cicd-dataops/README.md)) — `dbt build` contra um ambiente de teste a cada
  PR, bloqueando merge se testes falham.
- **Produção** — `dbt build` como gate; alertar em falhas (ver
  [deployment](../09-deployment/README.md)).

## Erros comuns

- Models sem testes (chave sem `unique`/`not_null`).
- `dbt run` sem testes em produção (em vez de `dbt build`).
- Tudo como `error` (um warn trava) ou tudo `warn` (erros graves passam).
- Não testar sources (freshness) nem relacionamentos.

## Boas práticas

- Teste toda chave (`unique`+`not_null`), domínios (`accepted_values`) e FKs (`relationships`).
- Severidade adequada; `dbt build` em CI e produção.
- Adicione `dbt_expectations` para volume/distribuição; teste `source freshness`.
- Documente as regras (viram [contrato](../../29-data-contracts/README.md) de facto).

## Relação com outros conceitos

- [Data quality / dbt tests](../../12-data-quality/06-dbt-tests/README.md),
  [expectation testing](../../12-data-quality/04-expectation-testing/README.md).
- [Models](../02-models/README.md), [sources](../03-sources-seeds/README.md),
  [deployment](../09-deployment/README.md), [pipeline testing](../../10-data-pipelines/07-pipeline-testing/README.md).

## Exercícios

1. Adicione os 4 testes genéricos aos campos apropriados de um model.
2. Escreva um teste singular que verifica `total == Σ itens`.
3. Configure severidade `warn`/`error` com limites.
4. Rode `dbt build` e observe que um model falho bloqueia seus dependentes.

## Referências

- Documentação do dbt — Tests, Unit tests, Severity.
- Pacotes `dbt_utils`, `dbt_expectations` (dbt Hub).
