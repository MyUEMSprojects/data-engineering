# Pipeline testing

> 🔵 Pipelines · Parte de [10 — Data Pipelines](../README.md)

## O que é

Testar pipelines é verificar, automaticamente, que o pipeline **funciona** (código correto)
e que os **dados** que ele produz atendem às expectativas. É a combinação de testes de
software ([testes](../../03-git-software-engineering/05-testing/README.md)) com testes de
dados ([data quality](../../12-data-quality/README.md)) aplicada ao contexto de pipeline.

## As duas dimensões (ambas necessárias)

```text
Testar CÓDIGO  →  "a lógica de transformação está correta?"      (determinístico, em CI)
Testar DADOS   →  "os dados reais atendem às expectativas?"      (em runtime, em produção)
```

Um pipeline maduro tem os dois: o código é testado antes do deploy; os dados são validados a
cada execução.

## Pirâmide de testes de pipeline

```text
        ╱ E2E ╲         roda o pipeline inteiro num ambiente controlado (poucos)
      ╱─────────╲
     ╱ integração ╲     etapas contra DB/arquivos reais (efêmeros)
   ╱───────────────╲
  ╱    unitários     ╲  transformações puras isoladas (muitos, rápidos)
```

### Unitários — a transformação pura

Separe a lógica do I/O (ver [transformação](../../09-etl-elt/03-transformation/README.md)) e
teste a função de transformação com dados de exemplo pequenos, incluindo **casos de borda**
(nulos, duplicatas, datas/fuso, strings estranhas).

```python
def test_clean_orders():
    df_in = make_df([{"id": 1}, {"id": 1}, {"id": None}])   # duplicata + nulo
    out = clean_orders(df_in)
    assert out["id"].tolist() == [1]            # dedup + remove nulo
```

### Integração — contra dependências reais

Suba um [PostgreSQL efêmero](../../06-databases/02-postgresql/README.md) (Docker/
`testcontainers`), rode a etapa de carga, verifique o resultado. Mocke serviços externos
(APIs) nas fronteiras (ver [testes em Python](../../04-python-for-data-engineering/09-testing-python/README.md)).

### End-to-end — o pipeline todo

Rode o DAG inteiro com dados de amostra num ambiente de teste e valide a saída final. Caro;
poucos, cobrindo os caminhos críticos.

## Testes essenciais de pipeline

- **Idempotência** — rodar duas vezes dá o mesmo resultado (ver
  [idempotência](../04-checkpoints-idempotency/README.md)).
- **Determinismo** — mesma entrada → mesma saída (controle `now()`/aleatoriedade).
- **Schema contract** — a saída tem o schema esperado (ver
  [schema validation](../../12-data-quality/03-schema-validation/README.md)).
- **Casos de borda** — vazio, nulos, duplicatas, volume anômalo.
- **Reprocessamento/backfill** — reprocessar uma data não duplica.

## Testes de dados (runtime)

Diferente dos testes de código (pré-deploy), os **testes de dados** rodam **a cada execução**
sobre os dados reais: unicidade, not-null, faixas, integridade referencial, frescor,
distribuição. Implementados com [dbt tests](../../28-dbt/05-tests/README.md),
[Great Expectations](../../12-data-quality/05-great-expectations/README.md) ou asserts, e
modelados como **gate** no [DAG](../02-dags-dependencies/README.md) (ver
[validação](../../09-etl-elt/10-data-validation/README.md)). São o que pega "o dado de hoje
veio ruim" — algo que nenhum teste de código pega.

## Dados de teste (fixtures)

- Amostras **pequenas e sintéticas** com casos de borda (em `fixtures/`/`sample_data/` — ver
  [convenções](../../CONVENTIONS.md)).
- **Nunca** dados de produção reais em testes (PII, lentidão) — ver
  [segurança](../../26-security/README.md).
- Dados gerados (Faker) para volume.

## Onde roda

- **CI** ([CI/CD](../../23-cicd-dataops/README.md)) — unitários + integração a cada PR;
  bloqueia merge se falhar.
- **Staging** — E2E e validação com dados realistas antes de produção.
- **Produção** — testes de dados a cada run (gate de qualidade).

## Testando SQL/dbt

- `dbt test` roda os testes declarados (`unique`, `not_null`, `relationships`,
  `accepted_values`) e customizados.
- **Unit tests** de modelos dbt (versões recentes) testam a lógica SQL com inputs/outputs
  fixos.
- Rode `dbt build` (modelos + testes) em CI contra um ambiente de teste.

## Erros comuns

- Testar só o código e esquecer os dados (ou vice-versa).
- Lógica acoplada ao I/O → não testável em unidade.
- Testes dependendo de produção/rede → lentos e instáveis.
- Não testar idempotência/reprocessamento.
- Dados de produção (PII) em fixtures.

## Boas práticas

- Pirâmide: muitos unitários de transformação pura; alguns integração; poucos E2E.
- Teste idempotência, determinismo, schema e casos de borda.
- Testes de dados como gate em runtime; testes de código em CI.
- Fixtures pequenas/sintéticas; mocke fronteiras.

## Relação com outros conceitos

- [Testes](../../03-git-software-engineering/05-testing/README.md),
  [testes em Python](../../04-python-for-data-engineering/09-testing-python/README.md).
- [Data quality](../../12-data-quality/README.md),
  [validação](../../09-etl-elt/10-data-validation/README.md),
  [dbt tests](../../28-dbt/05-tests/README.md).
- Automação: [CI/CD & DataOps](../../23-cicd-dataops/README.md).

## Exercícios

1. Separe a transformação de um pipeline da I/O e escreva testes unitários com casos de
   borda.
2. Escreva um teste de integração que carrega em um Postgres efêmero e verifica o resultado.
3. Escreva um teste de idempotência (rodar 2x = mesmo resultado).
4. Adicione testes de dados (unique/not_null/faixa) como gate no DAG.

## Referências

- Documentação do `pytest`, `testcontainers`, dbt (tests e unit tests).
- Great Expectations; Google *Testing on the Toilet*/SRE.
