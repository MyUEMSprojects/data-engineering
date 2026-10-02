# Protocol Buffers (Protobuf)

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

**Protocol Buffers (Protobuf)** é um formato de serialização **binário**, orientado a
linha, criado pelo Google, com schema definido em arquivos `.proto`. É muito usado em
**RPC** (especialmente **gRPC**), comunicação entre microsserviços e, às vezes, em
mensageria. Prioriza **velocidade, tamanho compacto e contratos fortes**.

## Por que existe / que problema resolve

Para comunicação máquina-a-máquina de alta performance, JSON é lento e grande (texto,
nomes de campos repetidos). Protobuf serializa para bytes compactos usando **números de
campo** em vez de nomes, com (de)serialização rápida e um **contrato de schema** compilado
em código de várias linguagens — ideal para APIs internas tipadas.

## O arquivo .proto

```protobuf
syntax = "proto3";
package exemplo;

message Pedido {
  int64  id    = 1;      // o NÚMERO do campo (tag) é o que importa na serialização
  double valor = 2;
  string uf    = 3;
  repeated string itens = 4;   // lista
}
```

O `.proto` é **compilado** (`protoc`) para gerar classes em Python, Java, Go, etc. Os
dados binários referenciam os **números de campo** (1, 2, 3...), não os nomes — por isso
são compactos e por isso **nunca se deve reutilizar/alterar um número de campo**.

## Como funciona a serialização

- Cada campo é codificado como `(field_number, wire_type) + valor` (varint para inteiros,
  etc.). Campos ausentes simplesmente não aparecem → muito compacto.
- O schema (gerado do `.proto`) é necessário para interpretar os bytes (não é
  autoexplicativo como Avro file).

## Schema evolution em Protobuf

Regras (ver [schema evolution](../10-schema-evolution/README.md)):

- **Adicionar** um campo novo (com número novo) → compatível; leitores antigos ignoram.
- **Nunca mudar o número** de um campo existente nem reusar números de campos removidos
  (marque como `reserved`).
- Em proto3, campos são opcionais por padrão (com valores default); isso facilita
  compatibilidade.
- **Não renomear** quebra nada na serialização (ela usa números), mas muda o código
  gerado.

```protobuf
message Pedido {
  reserved 3;              // número aposentado, nunca reutilizar
  reserved "uf";
  int64 id = 1;
  double valor = 2;
  string canal = 5;        // campo novo
}
```

## gRPC

Protobuf é a base do **gRPC**, framework de RPC de alta performance: você define serviços
e mensagens no `.proto`, e o gRPC gera cliente/servidor. Comum entre microsserviços; em
dados, aparece em serviços de **serving de modelos/features** e APIs internas de baixa
latência (ver [model serving](../../31-data-engineering-and-ml/05-model-serving/README.md),
[feature stores](../../31-data-engineering-and-ml/03-feature-stores-online-offline/README.md)).

## Protobuf vs Avro vs JSON

| | Protobuf | [Avro](../05-avro/README.md) | [JSON](../02-json-jsonl/README.md) |
| --- | --- | --- | --- |
| Formato | binário | binário | texto |
| Schema | `.proto` compilado | JSON (writer/reader) | nenhum |
| Autoexplicativo | não (precisa do schema) | Avro file sim | sim |
| Foco | RPC/gRPC, contratos | streaming/Kafka | APIs web, humanos |
| Evolução | por número de campo | por writer/reader + default | nenhuma garantia |

- **Protobuf** brilha em RPC/serviços tipados.
- **Avro** brilha em streaming/Kafka + Schema Registry.
- Ambos podem ser usados no Kafka (há suporte a Protobuf no Schema Registry também).

## Em Python

```python
# após: protoc --python_out=. pedido.proto
from pedido_pb2 import Pedido
p = Pedido(id=1, valor=9.9, uf="SP", itens=["x", "y"])
data = p.SerializeToString()        # bytes compactos
p2 = Pedido(); p2.ParseFromString(data)
```

## Quando usar / quando NÃO usar

- **Use** para comunicação entre serviços (gRPC), APIs internas de alta performance,
  serving de ML, contratos fortes tipados.
- **NÃO use** para analytics em massa (use [Parquet](../04-parquet/README.md)), troca com
  humanos (JSON/CSV), ou quando autoexplicabilidade do dado em repouso importa.

## Erros comuns

- **Reutilizar ou alterar números de campo** → corrompe a interpretação dos dados (o
  erro mais grave).
- Esperar ler Protobuf sem o `.proto` (não é autoexplicativo).
- Usar Protobuf para armazenamento analítico colunar.
- Não marcar campos removidos como `reserved` (risco de reuso futuro do número).

## Boas práticas

- Trate o `.proto` como **contrato versionado** ([data contracts](../../29-data-contracts/README.md)).
- Nunca mude/reutilize números; use `reserved` ao remover.
- Protobuf para transporte/RPC; Parquet para armazenamento analítico.
- Versione os `.proto` em Git e gere o código no build/CI.

## Relação com outros conceitos

- Base do gRPC; [serving de modelos/features](../../31-data-engineering-and-ml/05-model-serving/README.md).
- Contraste com [Avro](../05-avro/README.md); conceito de
  [schema evolution](../10-schema-evolution/README.md).
- [Data contracts](../../29-data-contracts/README.md).

## Exercícios

1. Escreva um `.proto`, compile-o e serialize/desserialize uma mensagem em Python.
2. Adicione um campo novo e remova outro (com `reserved`); explique a compatibilidade.
3. Compare o tamanho em bytes da mesma mensagem em Protobuf vs JSON.
4. Explique por que alterar o número de um campo existente é perigoso.

## Referências

- Documentação do Protocol Buffers (protobuf.dev) e do gRPC (grpc.io).
- Kleppmann, M. *DDIA* — cap. 4 (Protobuf/Thrift e evolution).
