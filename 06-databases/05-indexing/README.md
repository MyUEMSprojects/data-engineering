# Indexação (nível de sistema)

> 🔵 Core · Parte de [06 — Databases](../README.md)

Este tópico olha a indexação pela ótica do **sistema de banco de dados** — as
estruturas de dados por trás (B-tree vs LSM-tree) e seus trade-offs de leitura/escrita.
O uso de índices no **nível de query** (criar, índice composto, EXPLAIN) está em
[SQL — índices](../../05-sql/07-indexes/README.md); aqui entendemos *por que* cada
storage engine se comporta como se comporta.

## Por que existe

A velocidade de um banco depende de como ele organiza os dados em disco para busca. As
duas famílias de estruturas — **B-tree** e **LSM-tree** — representam escolhas opostas
no trade-off **leitura × escrita**, e explicam por que você escolhe Postgres para um
caso e Cassandra para outro.

## B-tree (otimizado para leitura e updates in-place)

Árvore balanceada que mantém os dados ordenados por chave em páginas. É a estrutura dos
bancos relacionais (Postgres, InnoDB do MySQL).

```text
            [ 50 ]
           /      \
     [20 40]      [70 90]
     /  |  \       /  |  \
 folhas com ponteiros para as linhas
```

- **Leitura** por chave/faixa: O(log n), poucas leituras de página → rápido.
- **Escrita/update**: altera a página no lugar (*in-place*); pode exigir *split* de
  página. Boas leituras, escrita moderada.
- **Durabilidade** via [WAL](../01-relational-concepts/README.md) (grava o log antes de
  tocar as páginas).

Ideal para **OLTP** (muitas leituras/updates pontuais com baixa latência).

## LSM-tree (otimizado para escrita)

*Log-Structured Merge-tree* — usada por Cassandra, RocksDB, HBase, ScyllaDB.

```text
escrita → commit log + memtable (em RAM, ordenada)
             │ quando enche
             ▼
          flush para SSTable imutável (em disco)
             │ em background
             ▼
         compaction (funde SSTables, remove versões antigas/tombstones)
```

- **Escrita**: vai direto para memória + log sequencial → **escrita altíssima** (sem
  update in-place).
- **Leitura**: pode precisar olhar várias SSTables (mitigado por *bloom filters* e
  índices) → mais cara que B-tree.
- **Compaction**: processo de fundo que reorganiza SSTables (custa I/O e CPU; pode
  causar picos de latência).

Ideal para cargas **write-heavy** (telemetria, eventos, séries temporais — ver
[column-family](../04-nosql/03-column-family/README.md)).

## B-tree vs LSM — o trade-off

| | B-tree | LSM-tree |
| --- | --- | --- |
| Escrita | moderada (in-place) | muito alta (append) |
| Leitura | muito boa | boa (com bloom filters) |
| Amplificação | mais *read*/write amplification variável | *write amplification* por compaction |
| Espaço | fragmentação | SSTables comprimidas, mas versões duplicadas até compactar |
| Uso típico | OLTP relacional | NoSQL write-heavy |

## Índices secundários e tipos (recap de sistema)

Além do índice primário (sobre a chave), bancos oferecem secundários. No Postgres,
além do B-tree padrão: **GIN** (jsonb/arrays/full-text), **GiST/SP-GiST** (espacial/
ranges), **BRIN** (tabelas enormes ordenadas — índice minúsculo), **hash** (igualdade).
Em NoSQL, índices secundários costumam ser **limitados/custosos** (o modelo é pensado
para acesso pela chave primária).

## Índices cobrem o que custa manter

Cada índice acelera certas leituras, mas **toda escrita** precisa atualizá-lo. Em LSM,
isso é relativamente barato (append); em B-tree, encarece updates. Daí a regra
universal: **indexe com intenção**, medindo (ver
[EXPLAIN](../../05-sql/10-query-planning-explain/README.md)).

## O ângulo do DE

- Escolher o banco de **destino operacional** ou entender a **fonte** passa por saber se
  é B-tree (relacional, leituras ricas) ou LSM (NoSQL, ingestão massiva).
- Em [warehouses colunares](../../13-data-warehouse/README.md), o conceito muda: não há
  B-tree; a "indexação" é **particionamento + clustering + estatísticas de arquivo**
  (min/max por *row group* em [Parquet](../../08-data-formats/04-parquet/README.md)) →
  *data skipping*.
- *Compaction* de LSM tem paralelo com o
  [problema de small files/compaction](../../14-data-lake/06-small-files-compaction/README.md)
  em lakes.

## Erros comuns

- Tratar um banco LSM como relacional (esperar leituras ad-hoc baratas por qualquer
  coluna).
- Ignorar o custo de *compaction* ao dimensionar um cluster write-heavy.
- Assumir índices B-tree em warehouses colunares.
- Criar índices demais e penalizar a escrita.

## Boas práticas

- Case o storage engine com a carga (leitura-pesada → B-tree; escrita-pesada → LSM).
- Em colunar, particione/clusterize para *data skipping* em vez de "índices".
- Monitore compaction/bloat; meça o uso de índices.

## Relação com outros conceitos

- Uso no nível de query: [SQL — índices](../../05-sql/07-indexes/README.md).
- Storage engines/WAL: [conceitos relacionais](../01-relational-concepts/README.md).
- *Data skipping* colunar: [partitioning/clustering](../../13-data-warehouse/03-partitioning-clustering/README.md).

## Exercícios

1. Explique, com o fluxo de escrita, por que uma LSM-tree sustenta escrita maior que uma
   B-tree.
2. Dê um caso em que você escolheria um banco B-tree e outro LSM, justificando.
3. Descreva como um warehouse colunar faz "data skipping" sem índices B-tree.
4. Relacione *compaction* de LSM com o problema de *small files* em data lakes.

## Referências

- Petrov, A. *Database Internals* — B-trees e LSM-trees.
- O'Neil et al. "The Log-Structured Merge-Tree (LSM-Tree)", 1996.
- Kleppmann, M. *DDIA* — cap. 3 (storage e retrieval).
