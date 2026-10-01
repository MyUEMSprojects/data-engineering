# Distributed joins e skew

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## O que é

**Joins distribuídos** são a operação de juntar duas tabelas em um cluster — e uma das mais caras,
porque geralmente exigem [shuffle](../03-partitioning-shuffle/README.md). **Skew** (distorção) é a
situação em que os dados se distribuem de forma **desigual** entre as partições, fazendo um nó
trabalhar muito mais que os outros — o gargalo nº 1 de jobs distribuídos lentos.

## Estratégias de join distribuído

### Shuffle hash / sort-merge join (o caso geral)

Para juntar duas tabelas grandes por uma chave, ambas precisam ser **reparticionadas pela chave de
join** (shuffle) para que linhas com a mesma chave fiquem no mesmo nó. Caro, mas necessário quando as
duas são grandes.

```text
tabela A (grande) ──shuffle por chave──┐
                                       ├─► mesmo nó junta por chave
tabela B (grande) ──shuffle por chave──┘
```

O Spark usa **sort-merge join** por padrão para grandes tabelas (ordena ambas pela chave e mescla).

### Broadcast join (quando uma tabela é pequena)

Se uma das tabelas é **pequena** (cabe na memória de cada executor), o Spark a **replica (broadcast)**
para todos os nós. Aí a tabela grande **não precisa ser embaralhada** — cada nó junta sua partição
com a cópia local da pequena. Muito mais rápido (sem shuffle da grande). Ver
[broadcast](../10-caching-broadcast/README.md).

```text
tabela pequena ──broadcast p/ todos os nós──► cada nó junta localmente (sem shuffle da grande)
```

Esse é o motivo de [dimensões](../../07-data-modeling/08-dimension-tables/README.md) pequenas num
[star schema](../../07-data-modeling/05-star-schema/README.md) serem baratas de juntar com o fato.

## Data skew: o problema

Se uma **chave** aparece muito mais que as outras (ex.: 40% dos pedidos são de um cliente gigante, ou
muitos registros com chave `NULL`), a partição dessa chave fica **enorme**. No join/agregação por essa
chave, **um nó** processa a maior parte dos dados enquanto os outros terminam e esperam:

```text
Sem skew:  nó1 ▓▓  nó2 ▓▓  nó3 ▓▓   (balanceado, termina junto)
Com skew:  nó1 ▓   nó2 ▓   nó3 ▓▓▓▓▓▓▓▓▓▓  (nó3 é o gargalo; os outros ociosos)
```

Sintomas: uma task que demora muito mais que as outras (visível na Spark UI), *spilling*, ou OOM num
executor específico.

## Causas comuns de skew

- **Chaves "quentes"** — valores muito frequentes (cliente/produto dominante).
- **NULLs** na chave de join/group (todos vão para a mesma partição).
- **Distribuição naturalmente desigual** (ex.: eventos concentrados num período).

## Mitigando skew

- **Salting (salgar a chave)** — adicionar um sufixo aleatório à chave quente para espalhá-la em
  várias partições, e ajustar o join de acordo (quebra a concentração).
- **Tratar NULLs** — filtrar/substituir NULLs da chave antes do join (ou tratá-los à parte).
- **Broadcast** — se o lado pequeno couber, elimina o shuffle (e o skew) da grande.
- **AQE (Adaptive Query Execution)** — o Spark 3+ **detecta e divide partições enlistadas (skewed)
  automaticamente** (`spark.sql.adaptive.skewJoin.enabled`). Ligue o AQE.
- **Separar a chave quente** — processar a chave dominante num caminho e o resto em outro, e unir.
- **Pré-agregar** antes do join reduz o volume.

## Escolhendo a estratégia

```text
um lado é pequeno?            → broadcast join (sem shuffle da grande) ✅
ambos grandes, sem skew?      → sort-merge/shuffle hash join
ambos grandes, com skew?      → AQE skew join + salting/tratar NULL
```

## Em warehouses MPP (Redshift)

O conceito aparece como **distribution key**: co-localizar as linhas que serão juntadas (mesma dist
key) evita o shuffle no join; `ALL` replica uma dimensão pequena (equivalente ao broadcast). Skew de
distribuição degrada tudo (ver [Redshift](../../13-data-warehouse/07-redshift/README.md)).

## Erros comuns

- Join de tabela grande com pequena **sem** broadcast (shuffle desnecessário).
- Ignorar skew → uma task eterna / OOM num executor (job "trava" perto do fim).
- NULLs na chave concentrando tudo numa partição.
- AQE desligado (perde mitigação automática de skew e coalescing).

## Boas práticas

- Broadcast tabelas pequenas; filtre/pré-agregue antes do join.
- **Ligue o AQE** (skew join + coalesce partitions).
- Diagnostique skew na Spark UI (task "fora da curva"); aplique salting/tratamento de NULL.
- Em MPP, escolha dist/sort keys pensando nos joins.

## Relação com outros conceitos

- [Shuffle](../03-partitioning-shuffle/README.md), [broadcast/cache](../10-caching-broadcast/README.md),
  [tuning](../11-performance-tuning/README.md).
- [Joins SQL](../../05-sql/03-joins/README.md); [Redshift dist keys](../../13-data-warehouse/07-redshift/README.md).
- [Skew em particionamento](../../06-databases/06-partitioning-sharding/README.md).

## Exercícios

1. Explique por que juntar duas tabelas grandes exige shuffle, mas uma grande + uma pequena pode ser
   broadcast.
2. Descreva como NULLs na chave de join causam skew e como tratar.
3. Explique a técnica de salting para uma chave quente.
4. Na Spark UI, que sinal indicaria skew num join? Como o AQE ajuda?

## Referências

- Chambers & Zaharia, *Spark: The Definitive Guide* — joins.
- Documentação do Spark — AQE (skew join handling).
