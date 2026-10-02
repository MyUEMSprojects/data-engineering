# Data validation

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

**Validação de dados** é verificar, durante o pipeline, se os dados atendem às
**expectativas** (schema, tipos, faixas, unicidade, integridade) **antes** de propagá-los
adiante. É a aplicação prática de [data quality](../../12-data-quality/README.md) dentro do
fluxo de ETL/ELT.

Este tópico foca em **onde e como** validar no pipeline; o catálogo completo de dimensões e
ferramentas de qualidade está no [módulo 12](../../12-data-quality/README.md).

## Por que validar no pipeline

Dados ruins que passam despercebidos causam o pior tipo de incidente: o pipeline "funciona"
mas os **números ficam errados** silenciosamente (ver
[troubleshooting](../../02-linux-shell-environment/08-logs-and-troubleshooting/README.md)).
Validar no pipeline:

- **Para o lixo na entrada** antes que contamine tabelas a jusante.
- **Detecta regressões** cedo (schema mudou, volume despencou).
- **Documenta** o que o dado deveria ser (as regras viram contrato).

## O que validar

| Categoria | Exemplos |
| --- | --- |
| **Schema** | colunas esperadas existem; tipos corretos (ver [schema validation](../../12-data-quality/03-schema-validation/README.md)) |
| **Not-null** | campos obrigatórios preenchidos |
| **Unicidade** | chave primária/natural sem duplicatas |
| **Faixa/domínio** | `valor >= 0`, `status in (...)`, datas plausíveis |
| **Integridade referencial** | toda FK existe na dimensão |
| **Volume** | nº de linhas dentro do esperado (não zerou, não explodiu) |
| **Frescor** | o dado é recente o suficiente ([freshness](../../24-observability/06-data-freshness/README.md)) |
| **Distribuição** | média/percentis dentro de limites (anomalias) |

## Onde validar (as camadas)

```text
ingestão (raw):   schema básico, encoding, "chegou tudo?" (contagem vs origem)
staging (silver): tipos, nulos, unicidade, domínios, integridade referencial
marts (gold):     regras de negócio, consistência de métricas, reconciliação
```

Validar em cada fronteira estabelece **contratos** entre as etapas.

## A decisão crítica: falhar ou quarentenar?

O que fazer quando um registro/lote falha a validação?

- **Fail-fast (bloquear)** — abortar o pipeline. Garante que **nada ruim** chega à produção;
  bom para violações graves (schema quebrado, chave duplicada). Risco: um registro ruim
  trava tudo.
- **Quarentena (segregar)** — mover as linhas inválidas para uma área separada
  (*dead letter*/quarentine table) e seguir com as válidas. Bom quando alguns erros são
  esperados e não devem parar o fluxo. Risco: ignorar silenciosamente problemas grandes.
- **Circuit breaker** — seguir, mas **alertar** e, se a taxa de erro passar de um limite,
  bloquear.

Escolha por severidade: *hard rules* (bloqueiam) vs *soft rules* (alertam/quarentenam). Ver
[tratamento de falhas](../11-handling-failures/README.md).

## Como implementar

### Asserts em código

```python
def validar(df):
    assert df["id"].notnull().all(), "id com nulos"
    assert df["id"].is_unique, "id duplicado"
    assert (df["valor"] >= 0).all(), "valor negativo"
    assert len(df) > 0, "dataset vazio"
```

### Pydantic (por registro, na ingestão)

Valida/coage dados de entrada (JSON de API) — ver
[typing/Pydantic](../../04-python-for-data-engineering/03-typing/README.md).

### Ferramentas declarativas

- **[dbt tests](../../28-dbt/05-tests/README.md)** — `unique`, `not_null`, `accepted_values`,
  `relationships` no warehouse.
- **[Great Expectations](../../12-data-quality/05-great-expectations/README.md)** /
  **Pandera** / **Soda** — suites de expectativas declarativas e relatórios.

## Validação como gate no pipeline

Modele a validação como uma **tarefa** do [DAG](../../10-data-pipelines/02-dags-dependencies/README.md):
a etapa seguinte só roda se a validação passar. Isso transforma qualidade em parte do fluxo,
não um extra opcional — a essência do [DataOps](../../23-cicd-dataops/05-dataops/README.md).

```text
extract ─► stage ─► [validar] ─✓─► load/marts
                        └─✗─► alerta / quarentena / abortar
```

## Reconciliação

Verificação de ponta a ponta: a contagem/soma no destino bate com a origem? (ex.:
`sum(valor)` do dia no warehouse == na fonte). Pega perdas silenciosas de dados.

## Erros comuns

- Não validar → dados ruins propagam e viram números errados.
- Só validar no final (tarde demais; já contaminou).
- Fail-fast em tudo (um registro ruim trava o pipeline) ou quarentenar tudo (ignora
  problemas graves) — sem distinguir severidade.
- Validar e **não alertar** (quarentena vira buraco negro).
- Checar só schema e esquecer volume/frescor/distribuição.

## Boas práticas

- Valide em cada fronteira (raw/staging/marts); contrato por camada.
- Distinga hard rules (bloqueiam) de soft rules (alertam/quarentenam).
- Quarentena **com alerta** e monitoramento da taxa de erro.
- Automatize com ferramentas declarativas no [CI](../../23-cicd-dataops/README.md) e no DAG.
- Reconcilie contagens/somas origem↔destino.

## Relação com outros conceitos

- Catálogo de qualidade: [12 — Data Quality](../../12-data-quality/README.md),
  [schema validation](../../12-data-quality/03-schema-validation/README.md),
  [Great Expectations](../../12-data-quality/05-great-expectations/README.md).
- [Tratamento de falhas](../11-handling-failures/README.md),
  [observabilidade](../../24-observability/README.md),
  [data contracts](../../29-data-contracts/README.md).

## Exercícios

1. Escreva validações (código ou dbt) para uma tabela de pedidos: schema, not-null,
   unicidade, `valor>=0`, FK de cliente.
2. Decida, para cada regra acima, se é hard (bloqueia) ou soft (quarentena) e justifique.
3. Implemente uma etapa de quarentena que segrega linhas inválidas e alerta.
4. Escreva uma reconciliação que compara a soma de receita entre fonte e warehouse.

## Referências

- Documentação de Great Expectations, dbt tests, Pandera, Soda.
- Reis & Housley, *Fundamentals of Data Engineering* — qualidade.
