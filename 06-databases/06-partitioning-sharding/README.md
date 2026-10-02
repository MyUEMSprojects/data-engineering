# Particionamento e sharding

> 🔵 Core · Parte de [06 — Databases](../README.md)

## O que é

Dividir dados grandes em pedaços menores:

- **Particionamento** — dividir uma tabela em partes (*partitions*), geralmente **dentro
  do mesmo servidor/cluster**, para gerenciar e consultar melhor.
- **Sharding** — distribuir as partições por **vários servidores (nós)**, para escalar
  além de uma máquina. Sharding é particionamento "horizontal distribuído".

> Os termos se sobrepõem na literatura. Pense assim: particionar = dividir; shardar =
> dividir **e** espalhar por máquinas.

## Por que existe / que problema resolve

- **Escala** — uma tabela de bilhões de linhas não cabe/roda bem num só nó; sharding
  distribui volume e carga.
- **Performance** — consultas leem só as partições relevantes (*partition pruning*),
  evitando varrer tudo.
- **Gerência** — descartar dados antigos é só *drop* de uma partição (rápido), em vez de
  `DELETE` caro.
- **Paralelismo** — engines distribuídas processam partições em paralelo (base do
  [Spark](../../16-distributed-processing/03-partitioning-shuffle/README.md)).

## Estratégias de particionamento

### Por faixa (range)

```sql
-- Postgres: partição por mês
CREATE TABLE eventos (ts timestamptz, ...) PARTITION BY RANGE (ts);
CREATE TABLE eventos_2024_01 PARTITION OF eventos
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

- Bom para intervalos (datas) e para descartar períodos antigos.
- Risco: **hotspot** — se as escritas recentes vão todas para a última partição (comum
  com tempo), um nó/partição fica sobrecarregado.

### Por hash

Aplica uma função de hash à chave e distribui uniformemente.

- Bom para **distribuir carga** por igual.
- Ruim para *range queries* (dados de uma faixa ficam espalhados).

### Por lista (list)

Partição por valores discretos (ex.: por país/região).

### Composta

Combinar estratégias (ex.: hash por cliente + range por data).

## A chave de particionamento é a decisão crítica

A escolha da **partition key** determina distribuição e performance:

- Deve **distribuir uniformemente** (evitar *skew* — partições desbalanceadas) e
- Alinhar-se às **consultas** (para permitir *pruning*).

```text
boa chave:  distribui + casa com as queries   → carga equilibrada, pruning eficiente
má chave:   concentra (hot partition) ou não casa com filtros → gargalo / full scan
```

Ver [skew](../../16-distributed-processing/04-distributed-joins-skew/README.md).

## Sharding (distribuir por nós)

- Cada *shard* é uma partição em um nó distinto; um roteador direciona a query ao shard
  certo pela chave.
- **Rebalanceamento** — ao adicionar nós, dados precisam migrar. *Consistent hashing* e
  *virtual nodes* reduzem o quanto migra.
- **Cross-shard queries/joins** são caras (exigem coordenar vários nós) → modele para
  evitá-las.

Em relacionais, sharding é trabalhoso (feito na aplicação ou com extensões como
**Citus** no Postgres, **Vitess** no MySQL). Muitos NoSQL
([Cassandra](../04-nosql/03-column-family/README.md), DynamoDB) shardam
automaticamente.

## Particionamento × Replicação (não confundir)

- **Particionamento/sharding** — divide os dados (cada parte num lugar) → escala
  **volume/escrita**.
- **[Replicação](../07-replication/README.md)** — copia os dados (várias cópias iguais) →
  **disponibilidade** e escala de **leitura**.

Sistemas reais **combinam** os dois: dados particionados **e** cada partição replicada.

```text
Partição 1 ─► nó A (líder) + nó B (réplica)
Partição 2 ─► nó C (líder) + nó D (réplica)
```

## O ângulo de Data Engineering

- **Particionamento de tabelas** (por data) em bancos e warehouses é prática padrão para
  performance e retenção.
- No **data lake/warehouse**, particionar arquivos por data/chave é essencial para
  *pruning* e custo (BigQuery cobra por bytes lidos!) — ver
  [partitioning no lake](../../14-data-lake/05-partitioning/README.md) e
  [clustering no warehouse](../../13-data-warehouse/03-partitioning-clustering/README.md).
- **Over-partitioning** gera o
  [small files problem](../../14-data-lake/06-small-files-compaction/README.md)
  (muitas partições minúsculas) — tão ruim quanto não particionar.

## Erros comuns

- Partition key que concentra carga (*hot partition*) — ex.: particionar por data e só
  escrever "hoje".
- Chave que não casa com os filtros → sem *pruning* (varre tudo).
- *Over-partitioning* (partições minúsculas demais) → overhead e small files.
- Cross-shard joins frequentes (modelagem ruim).
- Confundir sharding (dividir) com replicação (copiar).

## Boas práticas

- Escolha a chave para **distribuir** e **casar com as queries**.
- Particione por tempo para dados temporais (facilita retenção).
- Dimensione o tamanho da partição (nem gigante, nem minúscula).
- Evite cross-shard; replique + particione conforme a necessidade de HA + escala.

## Relação com outros conceitos

- [Replicação](../07-replication/README.md) (complemento),
  [sistemas distribuídos](../../01-foundations/05-distributed-systems-fundamentals/README.md).
- Paralelismo em [Spark](../../16-distributed-processing/03-partitioning-shuffle/README.md).
- Partição no [lake](../../14-data-lake/05-partitioning/README.md)/
  [warehouse](../../13-data-warehouse/03-partitioning-clustering/README.md).

## Exercícios

1. Particione uma tabela de eventos por mês no Postgres e mostre o *pruning* num
   `EXPLAIN`.
2. Escolha uma partition key para uma tabela de pedidos que distribua bem e permita
   consultar "pedidos por dia".
3. Explique por que particionar por "data de hoje" pode criar *hot partition* e como
   mitigar.
4. Diferencie sharding de replicação e descreva um sistema que usa ambos.

## Referências

- Kleppmann, M. *DDIA* — cap. 6 (particionamento).
- Documentação do PostgreSQL — "Table Partitioning"; Citus; Vitess.
