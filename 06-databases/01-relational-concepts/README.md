# Conceitos relacionais

> 🔵 Core · Parte de [06 — Databases](../README.md)

## O que é

Um **banco de dados relacional** organiza os dados em **tabelas** (relações) de
linhas e colunas, com um schema definido, e usa [SQL](../../05-sql/README.md) para
consultá-los. É baseado no modelo relacional de Edgar Codd (1970) e é a tecnologia
de dados mais madura e difundida — a base do mundo [OLTP](../../01-foundations/07-oltp-vs-olap/README.md).

## Por que existe / que problema resolve

Antes do modelo relacional, dados viviam presos à forma como a aplicação os
armazenava. Codd propôs separar a **lógica** (o que os dados representam) da **física**
(como são guardados), com fundamentos matemáticos (álgebra relacional). Benefícios:

- **Integridade** via [constraints](../../05-sql/09-constraints/README.md) e
  [transações ACID](../../05-sql/08-transactions-isolation/README.md).
- **Flexibilidade de consulta** — SQL declarativo responde perguntas não previstas.
- **Independência de dados** — mudar o armazenamento sem reescrever a aplicação.

## Conceitos fundamentais

- **Relação/tabela** — conjunto de tuplas (linhas) com atributos (colunas) tipados.
- **Schema** — a estrutura (tabelas, colunas, tipos, constraints). Relacionais são
  **schema-on-write**: o dado é validado ao entrar (ver
  [schema-on-read/write](../../14-data-lake/04-schema-on-read-write/README.md)).
- **Chaves** — [primária](../../05-sql/09-constraints/README.md) (identidade) e
  estrangeira (relacionamento).
- **Normalização** — organizar para reduzir redundância (ver
  [normalização](../../07-data-modeling/02-normalization-denormalization/README.md)).
- **ACID** — garantias transacionais (ver
  [transações](../../05-sql/08-transactions-isolation/README.md)).

## Como funciona por dentro (visão do DE)

Entender a arquitetura interna explica performance e comportamento.

### Storage engine

Componente que de fato lê/escreve dados em disco. Dois paradigmas:

- **Baseado em páginas / B-tree** (Postgres, InnoDB do MySQL) — ótimo para leitura e
  updates pontuais; o padrão OLTP (ver [indexação](../05-indexing/README.md)).
- **LSM-tree** (muitos NoSQL) — otimizado para escrita intensiva.

### Write-Ahead Log (WAL)

Antes de alterar os dados, o banco grava a mudança num **log sequencial (WAL)**. Isso
garante **durabilidade** (o D de ACID) e permite *recovery* após falha: ao reiniciar,
o banco "replica" o WAL para chegar a um estado consistente. O WAL é também a base de:

- **Replicação** (enviar o log a réplicas — ver [replicação](../07-replication/README.md)).
- **Point-in-time recovery** (ver [backup/DR](../09-backup-recovery-dr/README.md)).
- **[CDC](../../09-etl-elt/06-cdc/README.md)** — ferramentas como Debezium leem o WAL
  para capturar mudanças (crucial para ingestão incremental!).

### Buffer pool / cache

Páginas lidas ficam em memória (buffer pool). A performance depende muito de o
*working set* caber em RAM — leituras do disco são ordens de grandeza mais lentas.

### MVCC

Muitos relacionais usam [MVCC](../08-concurrency-consistency/README.md) para permitir
leituras sem bloquear escritas (mantendo versões das linhas).

## Vantagens

- Integridade forte, transações ACID, consultas ad-hoc poderosas.
- Maturidade, ferramental e ecossistema enormes.
- Resolve a imensa maioria dos casos (inclusive muito "big data" imaginário).

## Limitações / trade-offs

- **Escala de escrita horizontal** é mais difícil (um nó primário) — daí
  [sharding](../06-partitioning-sharding/README.md).
- Schema rígido pode atritar com dados muito variáveis/semiestruturados (embora
  `jsonb` ajude).
- Para cargas [analíticas massivas](../../01-foundations/07-oltp-vs-olap/README.md),
  um [warehouse colunar](../../13-data-warehouse/README.md) supera o relacional de
  linha.

## Quando usar / quando NÃO usar

- **Use** como banco operacional (OLTP), para dados com relacionamentos e integridade,
  e como fonte de verdade transacional. Para a maioria dos projetos, **comece aqui**.
- **Evite** como motor de analytics em escala (use warehouse) e quando o modelo é
  fundamentalmente não-relacional (grafos enormes, documentos muito heterogêneos,
  escala de escrita extrema) — ver [NoSQL](../04-nosql/README.md).

## O ângulo do Data Engineer

Relacionais são as **fontes** mais comuns de dados. Você precisa:

- Extrair sem impactar produção (réplicas de leitura, [CDC via WAL](../../09-etl-elt/06-cdc/README.md)).
- Entender o schema e as constraints para modelar o destino.
- Lidar com a diferença OLTP (origem) × OLAP (destino).

## Erros comuns

- Rodar analytics pesado direto no banco OLTP de produção.
- Achar que "não escala" e migrar para NoSQL cedo demais (um Postgres aguenta muito).
- Ignorar o WAL como fonte para CDC (reinventar ingestão incremental frágil).

## Boas práticas

- Modele com constraints e normalização adequada na origem.
- Use réplicas/CDC para extração analítica.
- Monitore o buffer pool/cache e o tamanho do *working set*.

## Relação com outros conceitos

- Implementações: [PostgreSQL](../02-postgresql/README.md),
  [MySQL](../03-mysql/README.md).
- Alternativas: [NoSQL](../04-nosql/README.md).
- WAL → [CDC](../../09-etl-elt/06-cdc/README.md),
  [replicação](../07-replication/README.md).

## Exercícios

1. Explique como o WAL garante durabilidade e como habilita replicação e CDC.
2. Dê um exemplo em que um relacional é a escolha certa e outro em que não é.
3. Descreva como extrair dados de um Postgres de produção para analytics sem
   degradá-lo.

## Referências

- Codd, E. F. "A Relational Model of Data for Large Shared Data Banks", 1970.
- Petrov, A. *Database Internals* — storage engines, WAL.
- Documentação do PostgreSQL — "Internals", "WAL".
