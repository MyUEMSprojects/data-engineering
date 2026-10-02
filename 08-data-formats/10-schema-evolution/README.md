# Schema evolution

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

**Schema evolution** é a capacidade de **mudar o schema** dos dados ao longo do tempo
(adicionar/remover/alterar campos) **sem quebrar** produtores e consumidores existentes.
É um dos problemas mais subestimados — e mais causadores de incidentes — em Data
Engineering.

## Por que importa

Dados vivem por anos; schemas mudam. Uma fonte adiciona um campo, renomeia uma coluna,
muda um tipo. Se o pipeline/consumidor não lida com isso graciosamente, ele **quebra** (ou,
pior, **processa errado em silêncio**). Em sistemas desacoplados (streaming, lake,
microsserviços), produtor e consumidor evoluem em ritmos diferentes — a compatibilidade de
schema é o que mantém tudo funcionando.

## Tipos de compatibilidade

Definem quem pode ler o quê (vocabulário do Schema Registry de
[Avro](../05-avro/README.md)/Kafka):

| Tipo | Significado | Mudança permitida |
| --- | --- | --- |
| **Backward** | consumidor **novo** lê dados **antigos** | remover campo; adicionar campo **com default** |
| **Forward** | consumidor **antigo** lê dados **novos** | adicionar campo; remover campo **com default** |
| **Full** | ambas | só mudanças que satisfaçam as duas |
| **None** | sem garantia | qualquer (perigoso) |

> "Backward" é o padrão mais comum: você atualiza os consumidores e eles continuam lendo o
> histórico.

## Mudanças seguras vs perigosas

```text
SEGURO (geralmente compatível):
  + adicionar campo OPCIONAL / com default
  + remover campo que tinha default
  + adicionar valor a um enum (com cuidado)
  + ampliar tipo compatível (int32 → int64, em alguns formatos)

PERIGOSO (quebra):
  - renomear campo (sem alias)
  - mudar o TIPO de um campo (string → int)
  - remover campo obrigatório
  - tornar opcional → obrigatório
  - reutilizar/alterar número de campo (Protobuf)
```

## Como cada formato lida

- **[Avro](../05-avro/README.md)** — excelente: *writer schema* vs *reader schema* +
  **defaults** + **aliases** resolvem a diferença automaticamente. Base do Schema Registry.
- **[Protobuf](../07-protobuf/README.md)** — por **número de campo**: adicionar é seguro;
  **nunca** reutilizar/alterar números; `reserved` ao remover.
- **[Parquet](../04-parquet/README.md)** — suporta adicionar colunas e (em engines/lakehouse)
  alguma evolução; mudanças de tipo e renomeações são mais delicadas.
- **[JSON](../02-json-jsonl/README.md)/[CSV](../01-csv/README.md)** — **nenhuma** garantia
  nativa; a "evolução" é o consumidor lidar defensivamente (campos ausentes, extras) —
  fonte de bugs. Valide com JSON Schema/Pydantic.
- **[Lakehouse](../../15-lakehouse/README.md)** (Delta/Iceberg) — têm **schema evolution**
  gerenciada na tabela (adicionar/renomear colunas, *schema enforcement*).

## Estratégias práticas

1. **Schema Registry** (Avro/Protobuf no Kafka) — valida compatibilidade **antes** de
   aceitar um schema novo; rejeita mudanças que quebrariam. Ver
   [data contracts](../../29-data-contracts/README.md).
2. **Defaults** em campos novos — a técnica mais importante para backward/forward.
3. **Adicionar, não mutar** — prefira adicionar um campo novo a mudar o significado/tipo de
   um existente. Para "renomear", adicione o novo e deprecie o antigo.
4. **Versionar o schema/contrato** (SemVer — ver
   [versionamento](../../03-git-software-engineering/04-conventional-commits-versioning/README.md)):
   mudança incompatível = major.
5. **Schema enforcement + evolution no lake** — rejeitar dados que não batem (enforcement)
   e evoluir a tabela deliberadamente (evolution), como no lakehouse.
6. **Tratar o desconhecido** — consumidores devem ignorar campos extras e tolerar campos
   ausentes (dentro do contrato).

## Schema-on-write vs schema-on-read

A evolução interage com **quando** o schema é aplicado (ver
[schema-on-read/write](../../14-data-lake/04-schema-on-read-write/README.md)):

- **On-write** (warehouse, Avro, lakehouse) — valida na entrada; evolução controlada,
  qualidade garantida cedo.
- **On-read** (lake cru de JSON/CSV) — interpreta na leitura; flexível, mas a mudança de
  schema vira problema do consumidor.

## O impacto de negócio

Uma mudança de schema não tratada pode: quebrar o pipeline (melhor caso — você percebe), ou
**processar silenciosamente errado** (pior caso — um campo renomeado vira nulo, e o
relatório fica errado por meses). Por isso, **detecção de mudança de schema** é parte de
[data quality](../../12-data-quality/03-schema-validation/README.md) e
[observabilidade](../../24-observability/README.md).

## Erros comuns

- Renomear/mudar tipo de campo em uso → quebra consumidores.
- Campos novos **obrigatórios** sem default → quebra dados antigos/produtores antigos.
- Confiar em JSON/CSV sem validação e "descobrir" a mudança em produção.
- Reutilizar número de campo em Protobuf.
- Não versionar o schema/contrato.

## Boas práticas

- Schema Registry + compatibilidade **backward/full** no streaming.
- Adicione campos com **default**; evite mutações; nunca renomeie sem alias.
- Versione schemas/contratos; trate mudança incompatível como *breaking change*.
- Detecte mudanças de schema na ingestão (qualidade/observabilidade).

## Relação com outros conceitos

- [Avro](../05-avro/README.md)/[Protobuf](../07-protobuf/README.md)/[Parquet](../04-parquet/README.md).
- [Data contracts](../../29-data-contracts/README.md),
  [schema validation](../../12-data-quality/03-schema-validation/README.md),
  [lakehouse](../../15-lakehouse/README.md).
- [Versionamento](../../03-git-software-engineering/04-conventional-commits-versioning/README.md).

## Exercícios

1. Classifique como compatível (backward/forward) ou não: (a) adicionar campo com default;
   (b) renomear coluna; (c) mudar int→string; (d) remover campo opcional.
2. Em Avro, adicione um campo com default e leia dados antigos com o novo schema.
3. Explique por que um campo renomeado em JSON pode causar "processar errado em silêncio".
4. Descreva como um Schema Registry impede uma mudança incompatível de chegar à produção.

## Referências

- Kleppmann, M. *DDIA* — cap. 4 (evolution e compatibilidade).
- Confluent Schema Registry — compatibility types.
- Documentação de schema evolution de Avro, Protobuf, Delta Lake, Iceberg.
