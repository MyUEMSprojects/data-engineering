# Document databases

> 🔵 Core · Parte de [NoSQL](../README.md)

## O que é

Armazenam dados como **documentos** autocontidos, tipicamente **JSON/BSON**, agrupados
em coleções. Diferente do key-value, o banco **entende** o conteúdo e permite consultar
e indexar campos internos. Exemplos: **MongoDB** (o mais popular), **Couchbase**,
**Amazon DocumentDB**, **Firestore**.

## Por que existe / que problema resolve

Muitos objetos de aplicação são naturalmente hierárquicos (um pedido com seus itens,
um perfil com preferências). Em relacional, isso vira várias tabelas e joins. Em um
banco de documentos, o objeto inteiro é um documento — **menos impedância** entre o
código e o armazenamento, e schema flexível (cada documento pode variar).

```json
{
  "_id": "p-42",
  "cliente": {"id": 7, "nome": "Ana"},
  "itens": [
    {"produto": "X", "qtd": 2, "preco": 10.0},
    {"produto": "Y", "qtd": 1, "preco": 5.0}
  ],
  "total": 25.0,
  "status": "pago"
}
```

## Como funciona

- **Coleções** de documentos (análogas a tabelas, mas sem schema fixo).
- Consultas por campos (inclusive aninhados) e índices sobre eles.
- Agregações via *aggregation pipeline* (MongoDB): estágios `$match`, `$group`,
  `$lookup` (um "join" limitado), `$project`.

```js
db.pedidos.find({ status: "pago", "cliente.id": 7 })
db.pedidos.aggregate([
  { $match: { status: "pago" } },
  { $group: { _id: "$cliente.id", total: { $sum: "$total" } } }
])
db.pedidos.createIndex({ status: 1, "cliente.id": 1 })
```

## Modelagem: embed vs reference

A grande decisão de design:

- **Embed (aninhar)** — guardar sub-dados dentro do documento (itens dentro do pedido).
  Leitura rápida (um doc = tudo), mas duplica dados e cresce o documento.
- **Reference (referenciar)** — guardar IDs e buscar em outra coleção (como FK). Menos
  duplicação, mas exige múltiplas consultas / `$lookup`.

Regra geral: **embed** o que é lido junto e muda junto; **reference** o que é grande,
compartilhado ou muda independentemente. Há limite de tamanho de documento (16 MB no
MongoDB).

## Transações e consistência

- MongoDB moderno suporta **transações ACID multi-documento** (desde 4.0), mas elas são
  mais custosas — o design idiomático prefere documentos autocontidos para evitar
  precisar delas.
- Consistência configurável via *read/write concern* (de local até *majority*).

## Vantagens

- Schema flexível (bom para dados heterogêneos/evolutivos).
- Mapeamento natural a objetos de aplicação.
- Consultas e índices sobre campos (mais rico que key-value).
- Escala horizontal via [sharding](../../06-partitioning-sharding/README.md).

## Limitações / trade-offs

- **Joins** são limitados e caros (`$lookup`); dados muito relacionais sofrem.
- Schema flexível vira **"schema implícito bagunçado"** sem disciplina — cada documento
  diferente dificulta a ingestão a jusante.
- Duplicação (embed) exige cuidado com atualização (mudar em vários lugares).
- Analytics complexo é melhor num warehouse.

## Document DB vs Postgres jsonb

O [Postgres com `jsonb`](../../02-postgresql/README.md) oferece documentos JSON +
poder relacional (joins, transações, constraints). Para muitos casos, "preciso de
schema flexível" é resolvido com `jsonb` sem abrir mão do relacional. Escolha um
document DB quando o modelo é majoritariamente documental **e** você precisa da escala/
flexibilidade específica dele.

## O ângulo do DE

- Documento é fonte comum (apps que usam MongoDB). Ingerir exige **achatar/normalizar**
  a estrutura aninhada e lidar com **schema variável** entre documentos.
- Estratégias: ler via *change streams* ([CDC](../../../09-etl-elt/06-cdc/README.md)) ou
  export; inferir/validar schema; explodir arrays (`itens`) em linhas no destino.
- Documentos sem schema consistente são um pesadelo de qualidade — negocie
  [data contracts](../../../29-data-contracts/README.md) quando possível.

## Erros comuns

- Usar documento onde o modelo é claramente relacional (muitos joins).
- Documentos crescendo sem limite (embed de arrays ilimitados).
- Falta de disciplina de schema → ingestão a jusante quebra.
- Esperar que analytics complexo rode bem no próprio MongoDB.

## Boas práticas

- Decida embed vs reference por padrão de acesso e volatilidade.
- Imponha um schema lógico (validação do Mongo / contratos).
- Indexe os campos consultados.
- Para análise, exporte/normalize para o warehouse/lake.

## Relação com outros conceitos

- Alternativa relacional: [Postgres jsonb](../../02-postgresql/README.md).
- Ingestão de dados aninhados: [transformação](../../../09-etl-elt/03-transformation/README.md),
  [formatos semiestruturados](../../../08-data-formats/02-json-jsonl/README.md).
- [Sharding](../../06-partitioning-sharding/README.md), [CDC](../../../09-etl-elt/06-cdc/README.md).

## Exercícios

1. Modele um pedido com itens usando embed e usando reference; liste prós/contras.
2. Escreva uma *aggregation pipeline* que soma o total por cliente.
3. Resolva o mesmo caso com Postgres `jsonb` e compare.
4. Descreva como achatar documentos aninhados com schema variável ao ingerir para um
   warehouse.

## Referências

- Documentação do MongoDB (mongodb.com/docs) — Data Modeling, Aggregation.
- Kleppmann, M. *DDIA* — cap. 2.
