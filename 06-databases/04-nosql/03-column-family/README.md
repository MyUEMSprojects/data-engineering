# Column-family (wide-column) stores

> 🔵 Core · Parte de [NoSQL](../README.md)

## O que é

Bancos **wide-column** (ou *column-family*) organizam dados por linhas identificadas por
uma chave, onde cada linha pode ter um conjunto esparso e variável de colunas,
agrupadas em "famílias de colunas". Inspirados no **Bigtable** (Google). Exemplos:
**Apache Cassandra**, **HBase**, **Google Bigtable**, **ScyllaDB**.

> **Atenção à confusão de nomes:** "column-family/wide-column" **não** é o mesmo que
> "[armazenamento colunar](../../../08-data-formats/08-row-vs-columnar/README.md)" de
> warehouses (Parquet/BigQuery). Wide-column é um modelo de dados distribuído orientado
> a escrita; colunar analítico é um layout físico para leitura de poucas colunas em
> massa. Nomes parecidos, propósitos diferentes.

## Por que existe / que problema resolve

Projetado para **escala de escrita massiva**, **alta disponibilidade** e distribuição
geográfica, sobre hardware comum. Resolve casos onde você ingere um volume enorme e
contínuo de dados (telemetria, eventos, séries temporais) e precisa que o sistema
**nunca** fique indisponível, aceitando [consistência eventual](../../08-concurrency-consistency/README.md).

## Como funciona (Cassandra como referência)

- **Arquitetura sem líder (masterless)** — todos os nós são iguais; dados
  [replicados](../../07-replication/README.md) e
  [particionados](../../06-partitioning-sharding/README.md) por hash da *partition key*.
- **LSM-tree** como storage engine — escritas vão para um *commit log* + *memtable* em
  memória e depois são descarregadas em *SSTables* imutáveis (ótimo para escrita;
  leituras exigem *compaction* — ver [indexação/LSM](../../05-indexing/README.md)).
- **Consistência ajustável (tunable)** — você escolhe por operação quantas réplicas
  precisam confirmar (`ONE`, `QUORUM`, `ALL`), equilibrando consistência × latência ×
  disponibilidade (um exemplo prático do [CAP/PACELC](../../../01-foundations/05-distributed-systems-fundamentals/README.md)).
- **CQL** — linguagem parecida com SQL, mas **sem joins** e com forte restrição: você só
  consulta eficientemente pelo que a chave permite.

## Modelagem: query-first (a parte crucial)

Em Cassandra você modela **a partir das queries**, não das entidades. A *primary key*
tem duas partes:

- **Partition key** — determina em qual nó o dado vive (distribui a carga).
- **Clustering columns** — ordenam os dados dentro da partição.

```sql
CREATE TABLE eventos_por_dispositivo (
  device_id text,
  ts        timestamp,
  valor     double,
  PRIMARY KEY ((device_id), ts)      -- partição por device, ordenado por tempo
) WITH CLUSTERING ORDER BY (ts DESC);
-- consulta eficiente: "últimas leituras de um device"
SELECT * FROM eventos_por_dispositivo WHERE device_id = 'd1' LIMIT 100;
```

Você **desnormaliza e duplica**: cria uma tabela por padrão de acesso. Não há joins; a
"junção" é feita na escrita.

## Vantagens

- Escrita altíssima e linearmente escalável.
- Alta disponibilidade (sem ponto único), multi-datacenter.
- Ótimo para séries temporais e dados *append-heavy*.
- Consistência ajustável por operação.

## Limitações / trade-offs

- **Modelagem rígida por query** — consultar por um atributo não previsto é caro/
  impossível (sem índice secundário eficiente).
- **Sem joins**; analytics ad-hoc é inviável no próprio banco.
- Consistência eventual exige cuidado; *tombstones* (deletes) e *compaction* complicam.
- Anti-padrões (partições gigantes, *hot partitions*) degradam tudo.

## Quando usar / quando NÃO usar

- **Use** para ingestão massiva de eventos/telemetria/IoT, séries temporais em escala,
  logs, e sistemas que exigem disponibilidade contínua e geodistribuição.
- **NÃO use** para dados muito relacionais, consultas ad-hoc variadas, ou quando o
  volume não justifica a complexidade (um Postgres/TimescaleDB pode bastar).

## O ângulo do DE

- Column-family é tipicamente **fonte** de alto volume. Você ingere para o lake/
  warehouse para fazer analytics (que não roda bem no próprio Cassandra).
- Entender a *partition key* ajuda a extrair sem criar *hot spots*.
- *Tombstones* e consistência eventual afetam a fidelidade de uma extração pontual.

## Erros comuns

- Modelar como relacional (e depois não conseguir consultar).
- Partições muito grandes ou *hot partitions* (chave mal escolhida).
- Esperar joins/queries ad-hoc.
- Tentar rodar analytics direto no Cassandra em vez de exportar.

## Boas práticas

- Modele uma tabela por query; escolha a partition key para distribuir e limitar o
  tamanho da partição.
- Use o nível de consistência adequado por operação.
- Ingira para um ambiente analítico para relatórios.

## Relação com outros conceitos

- LSM-tree: [indexação](../../05-indexing/README.md).
- Consistência ajustável: [concorrência/consistência](../../08-concurrency-consistency/README.md),
  [CAP](../../../01-foundations/05-distributed-systems-fundamentals/README.md).
- Séries temporais também em [TimescaleDB/Postgres](../../02-postgresql/README.md).

## Exercícios

1. Modele em Cassandra duas tabelas para os acessos "eventos por device por tempo" e
   "eventos por tipo por dia".
2. Explique por que não dá para consultar por um atributo fora da chave e o que fazer.
3. Compare níveis de consistência `ONE` vs `QUORUM` em latência e garantia.
4. Diferencie "wide-column" de "armazenamento colunar analítico".

## Referências

- Chang et al. "Bigtable", 2006.
- Documentação do Apache Cassandra (cassandra.apache.org) — data modeling, CQL.
- Petrov, A. *Database Internals* — LSM-trees.
