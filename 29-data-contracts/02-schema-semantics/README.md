# Schema e semântica

> 🟣 Advanced · Parte de [29 — Data Contracts](../README.md)

## Dois níveis do contrato

- **Schema (sintaxe)** — a **estrutura**: quais campos, tipos, obrigatoriedade, formatos. Verificável
  mecanicamente.
- **Semântica (significado)** — o que os campos **querem dizer**: unidade, fuso, grão, regras de negócio,
  domínio de valores, relações. Mais difícil de verificar, mas **é onde nascem os bugs mais caros** (dados
  "válidos" mas **errados** — ex.: valor em centavos vs reais).

> Um contrato só de schema garante que o pipeline **não quebra**; só com semântica garante que os números
> **estão certos**.

## Schema

### O que especificar

- **Campos** e **tipos** (`string`, `int64`, `decimal(12,2)`, `timestamp`, arrays/structs).
- **Nulabilidade/obrigatoriedade** (`required`), valores default.
- **Chaves**: primária/natural, unicidade, estrangeiras (integridade referencial).
- **Formato**: encoding, padrão (regex, ISO-8601), enums, comprimento.
- **Estrutura aninhada** e cardinalidade de arrays.
- **Formato físico** quando relevante: [Avro](../../08-data-formats/05-avro/README.md)/Protobuf/JSON Schema/
  [Parquet](../../08-data-formats/04-parquet/README.md).

### Linguagens/esquemas de definição

| Opção | Bom para |
| --- | --- |
| **Avro / Protobuf** (com Schema Registry) | eventos/streaming; compatibilidade nativa |
| **JSON Schema** | APIs/JSON; validação de payloads |
| **DDL SQL / dbt model contracts** | tabelas no warehouse (colunas/tipos impostos) |
| **Pydantic / Pandera** | validação em Python ([typing](../../04-python-for-data-engineering/03-typing/README.md)) |
| **ODCS / Data Contract Spec (YAML)** | contrato **completo** (schema + qualidade + SLA + dono), independente de formato |

### Tipos: cuidados que viram bugs

- **Dinheiro**: `decimal` com escala definida, **não** `float`; documente a **moeda** e se é **centavos ou
  unidade**.
- **Timestamps**: **fuso (UTC)** e precisão; `date` vs `timestamp`; evento vs processamento
  ([event time](../../17-streaming/03-time-and-windows/README.md)).
- **IDs**: string vs int; formato (UUID); estabilidade/unicidade entre sistemas.
- **Booleanos/enums**: conjunto fechado e **como tratar novos valores** (consumidores devem tolerar?).
- **Nulos**: diferença entre `null`, vazio e "desconhecido".
- **Strings**: encoding UTF-8, normalização.

## Semântica

### O que documentar

- **Definição de negócio** de cada campo ("`amount`: valor total do pedido **com impostos e sem frete**, em
  BRL").
- **Unidades e escala** (R$ vs centavos, kg vs g, UTC vs local).
- **Grão do dataset**: "uma linha por **pedido confirmado**" (ver [grão](../../07-data-modeling/04-dimensional-modeling/README.md)).
- **Domínio de valores e significado de enums** (o que é `PAID` vs `SHIPPED`; transições válidas).
- **Regras de derivação/cálculo** e dependências ("`net_amount = amount - discount`").
- **Ciclo de vida do registro**: criação, atualização, soft delete, correções retroativas, **dados tardios**.
- **Semântica de mudança**: o dataset é **snapshot**, **log de eventos (append-only)**, ou **estado atual
  (mutável)**? Como representar deletes? ([CDC](../../09-etl-elt/06-cdc/README.md), [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md))
- **Relações** com outros datasets/entidades; **glossário** de negócio.
- **Limitações conhecidas** e casos de borda.

### Como tornar a semântica verificável

Nem tudo é automatizável, mas muito é: transforme regras em **checagens**:

```yaml
quality:
  - rule: amount >= 0
  - rule: status IN ('CREATED','PAID','SHIPPED','CANCELED')
  - rule: order_id is unique
  - rule: customer_id exists in customers.customer_id        # integridade referencial
  - rule: created_at <= current_timestamp
  - rule: net_amount = amount - discount
  - rule: row_count between 0.8 * avg_7d and 1.2 * avg_7d    # volume sazonal
```

Implementadas com [dbt tests](../../28-dbt/05-tests/README.md), [Great Expectations/Soda](../../12-data-quality/README.md)
ou pelo próprio runtime de contratos ([implementação](../06-implementation/README.md)).

## Qualidade e SLAs dentro do contrato

Inclua as garantias do produtor ([dimensões de qualidade](../../12-data-quality/01-dimensions-of-quality/README.md)):
completude, unicidade, validade, **frescor** ("dados do dia anterior até 06:00") e **disponibilidade**,
com métricas e janelas ([SLI/SLO](../../24-observability/05-sli-slo-sla/README.md)).

## Privacidade e segurança no contrato

Para cada campo: **classificação/sensibilidade**, se é **PII**, **base legal/finalidade**, **mascaramento
exigido**, **retenção** e quem pode acessar ([classificação](../../25-data-governance/05-access-control-classification/README.md),
[LGPD](../../26-security/08-lgpd/README.md)). Evita que um campo sensível "vaze" para um consumidor sem
direito.

## Granularidade do contrato

- **Por dataset/tópico/tabela** (o padrão): define o produto de dados.
- **Por campo**: semântica/PII/qualidade específica.
- **Por interface de entrega**: o mesmo dado pode ter contratos para formatos diferentes (tópico Kafka vs
  tabela do warehouse), derivados de uma definição comum.

## Erros comuns

- Contrato só de schema (consumidor ainda erra a semântica).
- Semântica ambígua ("`valor`" sem unidade/moeda/impostos).
- Tipos imprecisos (float para dinheiro; timestamp sem fuso).
- Não documentar o **grão** nem o tratamento de updates/deletes/dados tardios.
- Enums abertos sem política para novos valores (quebra consumidores).
- Regras de qualidade só em prosa (não verificáveis).

## Boas práticas

- Definições de negócio claras, unidade/fuso/moeda explícitos, grão declarado.
- Regras de qualidade **executáveis**; PII/classificação por campo.
- Tipos precisos; enums com política de extensão; tratar nulos explicitamente.
- Gere o contrato/schema a partir da **fonte única** (código do produtor/registry) para evitar divergência.

## Relação com outros conceitos

- [Conceito](../01-concept/README.md), [compatibilidade](../04-compatibility-versioning/README.md),
  [contract testing](../05-contract-testing/README.md), [schema evolution](../../08-data-formats/10-schema-evolution/README.md),
  [data quality](../../12-data-quality/README.md), [modelagem](../../07-data-modeling/README.md).

## Exercícios

1. Escreva o schema e a semântica (definições, unidades, grão) de um dataset `payments`.
2. Transforme 5 regras de negócio em checagens executáveis (SQL/dbt/GX).
3. Identifique 4 ambiguidades semânticas típicas que passam em validação de schema.
4. Defina a política para novos valores de um enum `status` (consumidores devem tolerar?).

## Referências

- Data Contract Specification / ODCS (campos, qualidade, SLA); Avro/Protobuf/JSON Schema specs;
  Kimball, *The Data Warehouse Toolkit* (grão); dbt model contracts.
