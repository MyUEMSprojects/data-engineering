# Schema validation

> 🔵 Pipelines · Parte de [12 — Data Quality](../README.md)

## O que é

**Schema validation** é verificar que os dados têm a **estrutura e os tipos esperados**: as
colunas certas existem, com os tipos certos, obrigatoriedade correta. É a primeira e mais
básica barreira de qualidade — pega o problema mais comum: **a origem mudou o schema**.

## Por que é a primeira linha de defesa

A maioria dos incidentes "o pipeline quebrou / os números estão errados" começa com uma
**mudança de schema** não detectada (coluna renomeada, tipo mudado, campo removido). Validar o
schema na entrada transforma esse problema de um bug silencioso em um erro claro e precoce (ver
[schema evolution](../../08-data-formats/10-schema-evolution/README.md)).

## O que validar

- **Colunas esperadas existem** (e não há colunas inesperadas, se o contrato for estrito).
- **Tipos** corretos (`valor` é numérico, `data` é date/timestamp).
- **Obrigatoriedade** (campos not-null presentes).
- **Nomes** consistentes (sem renomeações silenciosas).

## schema-on-write vs schema-on-read

Onde a validação acontece depende da arquitetura (ver
[schema-on-read/write](../../14-data-lake/04-schema-on-read-write/README.md)):

- **On-write** (warehouse, [Avro](../../08-data-formats/05-avro/README.md), lakehouse) — valida
  na **gravação**; dados inválidos nem entram. Qualidade garantida cedo.
- **On-read** (lake cru de JSON/CSV) — valida na **leitura**; flexível, mas o problema aparece
  tarde (no consumo).

Boa prática: validar schema **na fronteira de ingestão**, o mais cedo possível.

## Como validar (ferramentas)

### Em runtime, por registro — Pydantic

Para dados de API/JSON na ingestão (ver
[typing/Pydantic](../../04-python-for-data-engineering/03-typing/README.md)):

```python
from pydantic import BaseModel
class Pedido(BaseModel):
    id: int
    valor: float
    uf: str | None = None

Pedido(**registro)   # levanta erro se tipo/campo não bater
```

### Em DataFrames — Pandera

Valida schema e regras de um DataFrame (pandas/polars):

```python
import pandera as pa
schema = pa.DataFrameSchema({
    "id": pa.Column(int, nullable=False, unique=True),
    "valor": pa.Column(float, pa.Check.ge(0)),
    "uf": pa.Column(str, pa.Check.isin(["SP","RJ","MG"]), nullable=True),
})
schema.validate(df)   # erro se não conformar
```

### No warehouse — dbt / contracts

[dbt](../../28-dbt/README.md) permite declarar o schema esperado de um modelo (model
`contracts`) e testar colunas; o warehouse impõe tipos na materialização. Ver
[dbt tests](../06-dbt-tests/README.md).

### Em streaming — Schema Registry

[Avro](../../08-data-formats/05-avro/README.md) + Schema Registry valida compatibilidade de
schema **antes** de aceitar mensagens (ver [data contracts](../02-data-contracts/README.md)).

### Formatos autodescritos

[Parquet](../../08-data-formats/04-parquet/README.md)/Avro carregam o schema embutido — ler já
revela divergências de tipo; lakehouse ([Delta/Iceberg](../../15-lakehouse/README.md)) faz
*schema enforcement* na escrita.

## O que fazer ao falhar

Como em toda [validação](../../09-etl-elt/10-data-validation/README.md): **bloquear**
(fail-fast) para mudanças graves, ou **quarentenar + alertar**. Mudança de schema é geralmente
grave o suficiente para bloquear e investigar.

## Detectar vs impor

- **Impor (enforce)** — rejeitar dados fora do schema (schema-on-write, contracts).
- **Detectar (drift)** — notar que o schema mudou e **alertar**, mesmo que você aceite o dado
  (útil em lakes flexíveis) — parte de
  [observabilidade](../../10-data-pipelines/08-pipeline-observability/README.md) e
  [anomaly detection](../07-anomaly-detection/README.md).

## Erros comuns

- Não validar schema → mudança da origem vira número errado silencioso.
- Validar só no consumo (tarde demais).
- Aceitar colunas extras/ausentes sem sequer alertar (schema drift invisível).
- Confiar que [constraints de warehouse](../../05-sql/09-constraints/README.md) impõem schema
  (muitas são só informativas).

## Boas práticas

- Valide schema na **ingestão** (fronteira), o mais cedo possível.
- Use a ferramenta certa por camada: Pydantic (registro), Pandera (DataFrame), dbt contracts
  (warehouse), Schema Registry (streaming).
- Detecte *schema drift* e alerte, mesmo quando aceitar o dado.
- Trate mudança de schema como evento grave (bloquear/investigar).

## Relação com outros conceitos

- [Schema evolution](../../08-data-formats/10-schema-evolution/README.md),
  [validação no pipeline](../../09-etl-elt/10-data-validation/README.md),
  [data contracts](../02-data-contracts/README.md).
- [Expectation testing](../04-expectation-testing/README.md),
  [dbt tests](../06-dbt-tests/README.md).

## Exercícios

1. Valide um registro JSON de API com Pydantic e um DataFrame com Pandera.
2. Explique on-write vs on-read e onde você colocaria a validação de schema.
3. Simule uma coluna renomeada na origem e mostre como a validação a pega.
4. Diferencie "impor schema" de "detectar schema drift" e dê um caso de cada.

## Referências

- Documentação de Pydantic, Pandera, dbt model contracts, Confluent Schema Registry.
- Kleppmann, M. *DDIA* — cap. 4.
