# Great Expectations

> 🔵 Pipelines · Parte de [12 — Data Quality](../README.md)

## O que é

**Great Expectations (GX)** é o framework de qualidade de dados open source mais conhecido.
Permite declarar **expectations** (ver [expectation testing](../04-expectation-testing/README.md))
sobre datasets, validá-las automaticamente, e gerar **Data Docs** — documentação/relatórios
legíveis do estado de qualidade dos dados.

## Por que existe

Escrever asserts de qualidade espalhados pelo código é frágil e não documenta nada. GX oferece:

- Um **catálogo grande** de expectativas prontas (dezenas de regras comuns).
- **Validação** reutilizável e configurável contra várias fontes (pandas, Spark, SQL).
- **Data Docs** — relatórios HTML de o que passou/falhou, úteis para o time e stakeholders.
- Integração com [orquestradores](../../11-orchestration/README.md) como gate de pipeline.

## Conceitos centrais

| Conceito | O que é |
| --- | --- |
| **Expectation** | uma afirmação verificável (`expect_column_values_to_not_be_null`) |
| **Expectation Suite** | conjunto de expectations para um dataset |
| **Data Source / Asset** | de onde vêm os dados (pandas, Spark, SQL DB) |
| **Batch** | o recorte de dados a validar (ex.: partição do dia) |
| **Checkpoint** | executa uma suite contra um batch e reporta |
| **Data Docs** | documentação/relatórios gerados a partir das validações |

## Exemplo (conceitual)

```python
import great_expectations as gx

ctx = gx.get_context()
batch = ctx.data_sources.pandas_default.read_dataframe(df)

batch.expect_column_values_to_not_be_null("id")
batch.expect_column_values_to_be_unique("id")
batch.expect_column_values_to_be_between("valor", min_value=0)
batch.expect_column_values_to_be_in_set("status", ["pago", "cancelado", "aberto"])
batch.expect_table_row_count_to_be_between(min_value=10_000, max_value=20_000)

results = batch.validate()      # roda e retorna sucesso/falha por expectation
```

> A API do GX mudou bastante entre as versões 0.x e 1.x; confira a documentação da **versão que
> você usa** (não decore assinaturas — os conceitos acima são estáveis).

## Expectations comuns (catálogo)

- `expect_column_values_to_not_be_null`, `_to_be_unique`
- `expect_column_values_to_be_between`, `_to_be_in_set`, `_to_match_regex`
- `expect_column_mean_to_be_between`, `_stdev_`, `_quantile_` (estatísticas)
- `expect_table_row_count_to_be_between`
- `expect_column_to_exist`, `expect_table_columns_to_match_set` (schema)
- `expect_column_values_to_be_in_type_list` (tipos)

Cobre completude, unicidade, validade, volume e distribuição (ver
[dimensões](../01-dimensions-of-quality/README.md)).

## Data Docs

GX gera páginas HTML mostrando, por suite/checkpoint, o que foi validado, o que passou/falhou e
estatísticas — ótimo para dar **visibilidade** de qualidade ao time e stakeholders, não só aos
engenheiros.

## Onde encaixa no pipeline

Um **Checkpoint** vira uma tarefa no [DAG](../../10-data-pipelines/02-dags-dependencies/README.md):
após a transformação, roda a suite; se falhar (expectativas *hard*), bloqueia a publicação; em
qualquer caso, atualiza os Data Docs e alerta. É a [validação](../../09-etl-elt/10-data-validation/README.md)
operacionalizada.

## GX vs dbt tests vs Pandera/Soda

| | Great Expectations | [dbt tests](../06-dbt-tests/README.md) | Pandera / Soda |
| --- | --- | --- | --- |
| Foco | framework rico + docs | testes no warehouse (SQL) | DataFrame / YAML monitor |
| Onde roda | pandas/Spark/SQL | dentro do dbt/warehouse | código / config |
| Pontos fortes | catálogo + Data Docs | simplicidade, integração com modelos | leveza |
| Complexidade | maior | menor | menor |

Muitos times usam **dbt tests** para o warehouse e **GX** para validações mais ricas/estatísticas
ou fora do warehouse. Não são excludentes.

## Trade-offs

- **Poderoso**, mas tem **curva de aprendizado** e boilerplate de configuração.
- Para só algumas regras simples no warehouse, [dbt tests](../06-dbt-tests/README.md) pode ser
  suficiente e mais leve.
- Validar grandes volumes tem custo de compute — rode sobre amostras/partições quando couber.

## Erros comuns

- Adotar GX para 3 regras simples que dbt tests resolveria (overhead).
- Rodar validação pesada sobre a tabela inteira todo dia (custo) em vez de por partição.
- Gerar Data Docs que ninguém olha (sem alerta acionável).
- Não versionar as suites (viram inconsistentes).

## Boas práticas

- Use GX quando precisar de catálogo rico, estatísticas e Data Docs.
- Rode checkpoints como gate no orquestrador; alerte em falhas *hard*.
- Valide por partição/amostra para controlar custo.
- Versione suites como código.

## Relação com outros conceitos

- Implementa [expectation testing](../04-expectation-testing/README.md) e
  [dimensões](../01-dimensions-of-quality/README.md).
- Alternativas: [dbt tests](../06-dbt-tests/README.md).
- Gate no [pipeline](../../10-data-pipelines/README.md)/[orquestrador](../../11-orchestration/README.md).

## Exercícios

1. Crie uma Expectation Suite para uma tabela de pedidos (not-null, unique, faixa, in-set,
   volume).
2. Rode um Checkpoint e inspecione os Data Docs.
3. Integre a validação como gate num pipeline (bloquear em falha hard).
4. Decida, para um caso dado, entre GX e dbt tests e justifique.

## Referências

- Documentação oficial do Great Expectations (docs.greatexpectations.io).
- Moses, B. et al. *Data Quality Fundamentals*.
