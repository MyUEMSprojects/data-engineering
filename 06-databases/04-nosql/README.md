# NoSQL

> 🔵 Core · Parte de [06 — Databases](../README.md)

## O que é

**NoSQL** ("Not Only SQL") agrupa bancos que fogem do modelo relacional estrito,
surgidos para atender necessidades que os relacionais atendiam mal: **escala
horizontal extrema**, **alta disponibilidade**, **schema flexível** e **modelos de
dados específicos** (documentos, grafos). Não é "melhor que SQL" — é diferente, com
trade-offs diferentes.

## Por que surgiu

No fim dos anos 2000, aplicações web gigantes (Amazon, Google, Facebook) precisavam
escalar escrita/leitura por centenas de servidores com disponibilidade contínua.
Relacionais tradicionais eram difíceis de [shardar](../06-partitioning-sharding/README.md)
e priorizam consistência forte. Papers como *Dynamo* (Amazon) e *Bigtable* (Google)
inspiraram uma geração de bancos que relaxam garantias (ex.: aceitam
[consistência eventual](../08-concurrency-consistency/README.md)) em troca de escala e
disponibilidade — o trade-off do [CAP](../../01-foundations/05-distributed-systems-fundamentals/README.md).

## Os quatro modelos

| Modelo | Estrutura | Exemplos | Caso típico |
| --- | --- | --- | --- |
| [Key-value](01-key-value/README.md) | chave → valor opaco | Redis, DynamoDB | cache, sessões, contadores |
| [Document](02-document/README.md) | documentos (JSON) | MongoDB, Couchbase | catálogos, perfis, conteúdo |
| [Column-family](03-column-family/README.md) | linhas esparsas por família de colunas | Cassandra, HBase, Bigtable | séries temporais, write-heavy |
| [Graph](04-graph/README.md) | nós e arestas | Neo4j, Neptune | relacionamentos (fraude, social) |

## O trade-off central: schema e consistência

- **Schema flexível (schema-on-read)** — grava-se qualquer formato; a estrutura é
  interpretada na leitura. Flexível, mas joga a responsabilidade de qualidade para o
  consumidor (ver [schema-on-read/write](../../14-data-lake/04-schema-on-read-write/README.md)).
- **Consistência** — muitos NoSQL oferecem **consistência eventual** (ou ajustável)
  para ganhar disponibilidade e escala. Entenda a garantia antes de confiar em leituras.

```text
Relacional:  schema rígido  + consistência forte + escala vertical/sharding difícil
NoSQL (vários): schema flexível + consistência (frequentemente) eventual + escala horizontal
```

> Importante: **relacionais modernos também escalam e têm JSON** (ver
> [Postgres jsonb](../02-postgresql/README.md)). A fronteira não é tão nítida quanto o
> marketing sugere. Escolha pelo **modelo de acesso**, não pela moda.

## Modelagem em NoSQL é diferente

Em relacional você normaliza e junta na leitura. Em muitos NoSQL você **modela em
torno das queries** (desnormaliza, duplica dados, projeta a chave para o padrão de
acesso). "Query-first modeling": sem joins baratos, você pré-junta na escrita.

## Quando usar / quando NÃO usar

- **Use** quando o modelo de acesso casa com o do banco (lookups por chave, documentos
  autocontidos, grafos, write-heavy em escala) e quando precisa de escala/
  disponibilidade que o relacional não dá facilmente.
- **NÃO use** como "relacional melhor" por padrão. Se você precisa de joins ad-hoc,
  transações multi-entidade e integridade forte, o relacional vence. Muita gente adota
  NoSQL e depois sofre para fazer analytics nele.

## O ângulo do Data Engineer

- NoSQL costuma ser **fonte** (dados operacionais) que você ingere para o warehouse/
  lake, onde o SQL analítico volta a reinar.
- Extrair de NoSQL exige lidar com **schema variável** e **sem joins** — você
  normaliza/achata na ingestão.
- Consistência eventual na origem significa que "o que você lê agora" pode estar
  desatualizado — cuidado em pipelines que dependem de ordem/atualidade.

## Erros comuns

- Adotar NoSQL por hype e recriar um relacional ruim em cima dele.
- Esperar joins/consultas ad-hoc eficientes onde o modelo não suporta.
- Confiar em leituras sem entender a garantia de consistência.
- Ignorar que analytics sobre NoSQL geralmente exige exportar para um warehouse.

## Boas práticas

- Escolha o modelo pelo **padrão de acesso**.
- Modele para as queries (desnormalize conscientemente).
- Documente a garantia de consistência usada.
- Para analytics, ingira o NoSQL num ambiente SQL/colunar.

## Relação com outros conceitos

- Trade-offs vêm de [sistemas distribuídos/CAP](../../01-foundations/05-distributed-systems-fundamentals/README.md).
- Comparar com [relacionais](../01-relational-concepts/README.md).
- [Consistência](../08-concurrency-consistency/README.md),
  [sharding](../06-partitioning-sharding/README.md),
  [replicação](../07-replication/README.md).

## Exercícios

1. Para cada modelo NoSQL, dê um caso de uso real e explique por que o relacional seria
   pior ali.
2. Modele um "carrinho de compras" em key-value e em document; compare.
3. Explique "query-first modeling" e por que a desnormalização é comum em NoSQL.
4. Descreva os desafios de fazer analytics diretamente sobre um MongoDB de produção.

## Referências

- DeCandia et al. "Dynamo: Amazon's Highly Available Key-value Store", 2007.
- Chang et al. "Bigtable", 2006.
- Kleppmann, M. *DDIA* — cap. 2 (modelos de dados).
