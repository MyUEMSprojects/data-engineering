# Key-value stores

> 🔵 Core · Parte de [NoSQL](../README.md)

## O que é

O modelo mais simples de NoSQL: um dicionário gigante e distribuído que mapeia uma
**chave** para um **valor** (opaco para o banco). Acesso por chave é extremamente rápido
(O(1)). Exemplos: **Redis**, **Amazon DynamoDB**, **Memcached**, **etcd**.

## Por que existe / que problema resolve

Muitos acessos de dados são simplesmente "me dê o valor desta chave": uma sessão de
usuário, um item de cache, um contador. Para isso, a potência de um relacional é
desnecessária. Key-value stores entregam latência baixíssima e escala horizontal
massiva focando só nesse padrão.

## Como funciona

- Dados são [particionados por hash da chave](../../06-partitioning-sharding/README.md)
  entre nós → escala horizontal.
- Sem joins, sem queries complexas: você acessa por chave (ou faixa de chave em alguns).
- Muitos são *in-memory* (Redis/Memcached) → velocidade; alguns persistem em disco
  (DynamoDB).

```text
GET  user:42:session   → {token: ..., expira: ...}
SET  counter:views     → 10238
INCR counter:views     → 10239
```

## Redis (o canivete suíço in-memory)

Redis vai além de key-value puro: oferece **estruturas de dados** (listas, sets,
hashes, sorted sets, streams, HyperLogLog) e usos como:

- **Cache** (com TTL/expiração).
- **Filas/streams** leves (`LIST`, `Redis Streams`).
- **Rate limiting**, contadores, locks distribuídos.
- **Leaderboards** (sorted sets).

```bash
SET produto:1 '{"nome":"X"}' EX 3600    # com expiração de 1h
HSET user:42 nome "Ana" uf "SP"
ZADD ranking 100 "ana" 90 "bob"         # sorted set
```

Em DE, Redis frequentemente serve como **feature store online** (baixa latência para
servir *features* a modelos — ver
[online features](../../../31-data-engineering-and-ml/03-feature-stores-online-offline/README.md))
e como cache de lookups.

## DynamoDB (key-value gerenciado e escalável)

Serviço da AWS, totalmente gerenciado, com escala "ilimitada" e latência consistente.
Conceitos:

- **Partition key** (obrigatória) + **sort key** (opcional) = chave primária.
- Modelagem *single-table design* (uma tabela modelada para todos os padrões de acesso)
  é comum e peculiar.
- Consistência **eventual** por padrão (leitura forte opcional, mais cara).
- Cobrança por capacidade/uso; cuidado com *hot partitions* (chaves mal distribuídas).

## Vantagens

- Latência mínima e *throughput* altíssimo.
- Escala horizontal simples (hash da chave).
- Modelo mental trivial.

## Limitações / trade-offs

- **Sem queries ad-hoc**: só acessa pelo que a chave permite. Buscar "todos com uf=SP"
  exige modelar isso na chave (ou um índice secundário limitado).
- **Valor opaco**: o banco não entende/filtra o conteúdo (exceto estruturas do Redis).
- **Analytics é inviável** diretamente — exporte para warehouse/lake.
- In-memory (Redis) custa RAM e exige estratégia de persistência/eviction.

## Quando usar / quando NÃO usar

- **Use** para cache, sessões, contadores, *rate limiting*, filas simples, feature
  store online, lookups por chave em escala.
- **NÃO use** para dados que você precisa consultar por múltiplos atributos ad-hoc,
  analytics, ou relacionamentos complexos.

## O ângulo do DE

- Redis como **cache**/feature store online no serving de dados/ML.
- DynamoDB como **fonte**: ingerir via DynamoDB Streams ([CDC](../../../09-etl-elt/06-cdc/README.md))
  ou export para S3, depois normalizar no lake.
- *Hot keys*/hot partitions são a causa nº 1 de problemas de performance.

## Erros comuns

- Usar key-value como banco primário de dados relacionais.
- Chaves mal distribuídas → *hot partitions* (um nó sobrecarregado).
- Esquecer TTL em caches → memória estoura.
- Tentar fazer analytics "por cima" em vez de exportar.

## Boas práticas

- Modele a chave em torno do padrão de acesso; distribua bem (evite hot keys).
- Use TTL/eviction em caches.
- Para DynamoDB, planeje o *single-table design* e os índices secundários cedo.
- Exporte para ambiente SQL/colunar para análise.

## Relação com outros conceitos

- Particionamento por hash: [sharding](../../06-partitioning-sharding/README.md).
- Consistência eventual: [concorrência/consistência](../../08-concurrency-consistency/README.md).
- Online features: [feature stores](../../../31-data-engineering-and-ml/03-feature-stores-online-offline/README.md).

## Exercícios

1. Modele sessões de usuário e um contador de visualizações em Redis (com TTL).
2. Projete a partition/sort key de uma tabela DynamoDB para o acesso "pedidos de um
   cliente por data".
3. Explique o que é uma *hot partition* e como evitá-la.
4. Descreva como ingerir mudanças de um DynamoDB para um data lake.

## Referências

- Documentação do Redis (redis.io) e do Amazon DynamoDB.
- DeCandia et al. "Dynamo", 2007.
