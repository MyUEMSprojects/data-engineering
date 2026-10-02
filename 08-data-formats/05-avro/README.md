# Avro

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

**Apache Avro** é um formato de serialização **binário**, **orientado a linha**, com
**schema** definido em JSON. É o formato padrão para **mensagens em streaming** (sobretudo
[Kafka](../../18-message-brokers/README.md)) e para dados que precisam de **schema
evolution** robusta. Complementa o [Parquet](../04-parquet/README.md): Avro para
transporte/escrita linha a linha; Parquet para armazenamento analítico colunar.

## Por que existe / que problema resolve

Em streaming, você serializa **um registro por vez** e envia pela rede — um layout de
**linha** é natural (colunar exigiria acumular muitas linhas). Além disso, produtores e
consumidores evoluem de forma independente, então o formato precisa de **evolução de
schema** compatível e eficiente. Avro foi desenhado exatamente para isso.

## Características-chave

- **Schema em JSON** separado dos dados.
- **Binário e compacto** — os dados **não** repetem os nomes dos campos (diferente de
  JSON); o schema é que dá sentido aos bytes → muito menor que JSON.
- **Schema junto ou à parte** — em *Avro files* (object container) o schema vai no
  cabeçalho; em Kafka, o schema fica num **Schema Registry** e a mensagem carrega só um ID.
- **Schema evolution** forte (ver [schema evolution](../10-schema-evolution/README.md)).
- Tipos ricos, incluindo records aninhados, unions, enums, e **defaults** (chave para
  evolução).

## Exemplo de schema

```json
{
  "type": "record",
  "name": "Pedido",
  "namespace": "com.exemplo",
  "fields": [
    {"name": "id", "type": "long"},
    {"name": "valor", "type": "double"},
    {"name": "uf", "type": ["null", "string"], "default": null},
    {"name": "canal", "type": "string", "default": "web"}
  ]
}
```

O `default` permite que consumidores com schema antigo/novo leiam dados sem quebrar.

## Writer schema vs reader schema (o mecanismo de evolução)

A grande sacada do Avro: os dados são escritos com o **writer schema** e lidos com o
**reader schema**, que podem ser **diferentes**. O Avro resolve a diferença usando regras
e `defaults`:

- **Campo adicionado** (com default) → leitores antigos ignoram; leitores novos usam o
  default em dados antigos. ✅
- **Campo removido** (que tinha default) → compatível. ✅
- **Renomear** → quebra (a menos que use `aliases`).

Isso habilita produtores e consumidores evoluírem de forma desacoplada — essencial em
[streaming](../../17-streaming/README.md).

## Schema Registry (Kafka)

No ecossistema Kafka, o **Schema Registry** (Confluent/Apicurio) armazena os schemas e
valida a **compatibilidade** antes de aceitar um novo. As mensagens carregam só um
**schema ID** (poucos bytes) em vez do schema inteiro → mensagens minúsculas + garantia de
compatibilidade. Ver [data contracts](../../29-data-contracts/README.md).

```text
Producer ──(serializa com schema v2, envia id)──► Kafka ──► Consumer
                      │                                          │
                      └──── Schema Registry (valida compat.) ────┘
```

## Lendo/escrevendo (Python)

```python
import fastavro

schema = fastavro.parse_schema({...})   # dict acima
with open("pedidos.avro", "wb") as f:
    fastavro.writer(f, schema, registros)   # registros = lista de dicts

with open("pedidos.avro", "rb") as f:
    for registro in fastavro.reader(f):     # schema vem do cabeçalho do arquivo
        ...
```

## Avro vs Parquet (complementares, não rivais)

| | Avro | Parquet |
| --- | --- | --- |
| Layout | **linha** | **coluna** |
| Melhor para | escrita/transporte registro a registro, streaming | leitura analítica em massa |
| Schema evolution | excelente | boa (limitada) |
| Compressão | boa | excelente (colunar) |
| Uso típico | Kafka, ingestão | lake/warehouse |

Padrão comum: **ingerir via Avro (Kafka) → gravar em Parquet** no lake para analytics.

## Quando usar / quando NÃO usar

- **Use** para mensagens/eventos em Kafka, dados que evoluem de schema com frequência,
  serialização linha a linha, e quando compatibilidade produtor/consumidor é crítica.
- **NÃO use** como formato de consulta analítica em massa (use Parquet) nem para troca com
  humanos (use JSON/CSV).

## Erros comuns

- Usar Avro para analytics colunar (lento para "somar uma coluna").
- Evoluir schema sem `default`/`aliases` → quebra consumidores.
- Esquecer o Schema Registry no Kafka (mensagens grandes, sem controle de compat.).
- Confundir Avro file (schema no cabeçalho) com Avro no Kafka (schema por ID).

## Boas práticas

- Sempre com schema versionado e **defaults** nos campos novos.
- Schema Registry + política de compatibilidade no Kafka.
- Avro no transporte/ingestão; Parquet no armazenamento analítico.
- Nunca renomear sem `aliases`.

## Relação com outros conceitos

- [Kafka/streaming](../../18-message-brokers/README.md),
  [schema evolution](../10-schema-evolution/README.md),
  [data contracts](../../29-data-contracts/README.md).
- Complementa [Parquet](../04-parquet/README.md); contraste com
  [Protobuf](../07-protobuf/README.md).

## Exercícios

1. Defina um schema Avro para um evento e serialize/desserialize registros com `fastavro`.
2. Adicione um campo novo com `default` e leia dados antigos com o novo schema (prove a
   compatibilidade).
3. Explique o papel do Schema Registry e do schema ID nas mensagens Kafka.
4. Descreva um pipeline "Kafka (Avro) → lake (Parquet)" e por que cada formato está onde
   está.

## Referências

- Documentação do Apache Avro (avro.apache.org) — specification.
- Confluent Schema Registry docs.
- Kleppmann, M. *DDIA* — cap. 4 (Avro e schema evolution).
