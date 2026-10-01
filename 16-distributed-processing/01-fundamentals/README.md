# Fundamentos de processamento distribuído

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## O que é

Processamento distribuído é dividir uma computação sobre dados entre **vários nós (máquinas)** que
trabalham em **paralelo**, coordenando-se para produzir um resultado único. É a resposta para quando
os dados ou a computação excedem o que uma máquina aguenta (ver
[sistemas distribuídos](../../01-foundations/05-distributed-systems-fundamentals/README.md)).

## Por que distribuir (e o preço)

- **Volume** — processar petabytes não cabe numa máquina.
- **Velocidade** — dividir o trabalho entre N nós pode acelerar ~N vezes (idealmente).
- **Escala horizontal** — adicionar máquinas (*scale out*) em vez de uma máquina gigante (*scale up*,
  limitada).

O preço: **complexidade** — coordenação, falhas parciais, e o custo de **mover dados** entre nós (a
rede é ordens de grandeza mais lenta que a memória). A arte do processamento distribuído é
**maximizar paralelismo e minimizar movimento de dados**.

## Conceitos centrais

### Particionamento (partitions)

Os dados são divididos em **partições**, cada uma processada por uma *task* em um nó. O número de
partições define o grau de paralelismo. Ver
[partitioning/shuffle](../03-partitioning-shuffle/README.md).

```text
dataset ─► [partição 1][partição 2]...[partição N] ─► N tasks em paralelo
```

### Data locality (levar o código até o dado)

Mover **código** (pequeno) para onde o **dado** está (grande) é muito mais barato que mover o dado
para o código. Sistemas distribuídos tentam agendar cada task **no nó que já tem a partição** →
*data locality*. Quebrar a localidade (ler pela rede) é um gargalo comum.

### Paralelismo: embarrassingly parallel vs com coordenação

- **Embarrassingly parallel** — cada partição é processada **independentemente** (ex.: um `map`,
  filtrar/transformar linha a linha). Escala lindamente, sem comunicação entre nós.
- **Com coordenação** — operações que precisam juntar dados de **várias** partições (`GROUP BY`,
  `JOIN`, `sort`) exigem **mover dados** entre nós (*shuffle*) — o caro. Ver
  [shuffle](../03-partitioning-shuffle/README.md).

```text
map/filter (local, barato) ───► shuffle (rede, caro) ───► reduce/agg (local, barato)
```

### Tolerância a falhas

Com muitos nós, falhas são a norma (ver
[fault tolerance](../../10-data-pipelines/05-fault-tolerance/README.md)). Sistemas distribuídos
recuperam sem recomeçar tudo: o Spark, por exemplo, recomputa só as partições perdidas a partir da
*lineage* (histórico de como foram derivadas) — ver [RDD](../08-rdd-dataframe/README.md).

### Lazy evaluation (avaliação preguiçosa)

Muitos frameworks (Spark, [polars](../../04-python-for-data-engineering/12-polars/README.md)) não
executam cada operação na hora: constroem um **plano** e só executam quando o resultado é pedido
(*action*). Isso permite **otimizar** o plano inteiro (reordenar filtros, combinar passos, minimizar
shuffle) antes de rodar — ver [Catalyst](../09-catalyst-tungsten/README.md).

## Escalabilidade: o que atrapalha

- **Shuffle/rede** — mover dados entre nós (o maior custo).
- **[Skew](../04-distributed-joins-skew/README.md)** — partições desbalanceadas (um nó faz todo o
  trabalho enquanto os outros esperam).
- **Overhead de coordenação** — sincronização, pequenos jobs com muito overhead.
- **Small files** / partições minúsculas — overhead domina (ver
  [small files](../../14-data-lake/06-small-files-compaction/README.md)).

> Lei de Amdahl, na prática: a parte **não paralelizável** (shuffle, coordenação) limita o ganho de
> adicionar mais nós.

## Modelos de processamento

- **Batch** — processar um conjunto delimitado (ver [batch](../../01-foundations/06-batch-vs-streaming/README.md),
  [MapReduce](../02-mapreduce/README.md), Spark batch).
- **Stream** — processar fluxo contínuo (ver [streaming](../../17-streaming/README.md)).
- **MPP** — warehouses distribuídos (ver [warehouse](../../13-data-warehouse/01-concepts-architecture/README.md)).

## Quando (não) distribuir

- **Distribua** quando os dados não cabem numa máquina ou o processamento single-node é lento demais.
- **Não distribua** por reflexo: para GBs que cabem num servidor,
  [polars](../../04-python-for-data-engineering/12-polars/README.md)/DuckDB são mais simples, rápidos e
  baratos que montar um cluster Spark. O overhead de distribuição só compensa na escala certa.

## Erros comuns

- Distribuir dados que caberiam numa máquina (overhead sem ganho).
- Ignorar o custo do shuffle (escrever código que move dados desnecessariamente).
- Não perceber skew (um nó gargalo).
- Muitas partições minúsculas ou poucas gigantes.

## Boas práticas

- Maximize operações locais (map/filter); minimize shuffle.
- Dimensione partições (nem minúsculas, nem gigantes).
- Aproveite data locality e lazy evaluation/otimizador.
- Só distribua quando a escala exigir.

## Relação com outros conceitos

- Base: [sistemas distribuídos](../../01-foundations/05-distributed-systems-fundamentals/README.md).
- [MapReduce](../02-mapreduce/README.md), [shuffle](../03-partitioning-shuffle/README.md),
  [Spark](../05-apache-spark/README.md).
- Alternativa single-node: [polars](../../04-python-for-data-engineering/12-polars/README.md).

## Exercícios

1. Classifique como embarrassingly parallel ou "precisa de shuffle": filtrar linhas; somar por grupo;
   adicionar uma coluna calculada; ordenar globalmente; join.
2. Explique data locality e por que mover código é melhor que mover dados.
3. Dê um exemplo de dado que **não** justifica Spark e a alternativa adequada.
4. Explique, com a lei de Amdahl, por que dobrar os nós nem sempre dobra a velocidade.

## Referências

- Dean & Ghemawat, "MapReduce", 2004.
- Kleppmann, M. *DDIA* — cap. 10.
- Chambers & Zaharia, *Spark: The Definitive Guide*.
