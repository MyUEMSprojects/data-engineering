# MapReduce

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## O que é

**MapReduce** é um modelo de programação (e o framework original do Google/Hadoop) para processar
grandes volumes de dados de forma distribuída, em três fases: **map**, **shuffle** e **reduce**.
Embora o framework Hadoop MapReduce esteja em desuso (substituído por
[Spark](../05-apache-spark/README.md)), o **modelo** é fundamental — Spark, warehouses e engines de
stream ainda operam sobre essas ideias.

## Por que estudar algo "antigo"

MapReduce é o avô do processamento distribuído moderno. Entendê-lo revela *por que* o
[shuffle](../03-partitioning-shuffle/README.md) existe e é caro, e dá o vocabulário para raciocinar
sobre qualquer engine distribuída. É um modelo mental, não (só) uma ferramenta.

## As três fases

```text
Entrada particionada
      │
   MAP: cada partição → gera pares (chave, valor)      [paralelo, local]
      │
 SHUFFLE: agrupa todos os valores por chave,            [rede, caro!]
          movendo dados entre nós
      │
 REDUCE: para cada chave, agrega seus valores           [paralelo, por chave]
      │
   Saída
```

### Map

Aplica uma função a cada registro de entrada, **independentemente** (embarrassingly parallel),
emitindo pares `(chave, valor)`. Roda localmente em cada partição.

### Shuffle

Reagrupa os pares para que **todos os valores da mesma chave** fiquem juntos no mesmo *reducer*. Isso
exige **mover dados pela rede** entre nós — é a fase cara (ver
[shuffle](../03-partitioning-shuffle/README.md)).

### Reduce

Para cada chave, processa a lista de valores agregando-os (soma, contagem, etc.), emitindo o
resultado.

## Exemplo clássico: word count

```text
Texto: "a rosa é uma rosa"

MAP:     (a,1) (rosa,1) (é,1) (uma,1) (rosa,1)
SHUFFLE: a→[1]  rosa→[1,1]  é→[1]  uma→[1]
REDUCE:  a=1    rosa=2       é=1    uma=1
```

Em pseudocódigo:

```python
def map(linha):
    for palavra in linha.split():
        emit(palavra, 1)

def reduce(palavra, contagens):
    emit(palavra, sum(contagens))
```

## Por que foi revolucionário

- **Abstração** — o programador escreve só `map` e `reduce`; o framework cuida de
  distribuição, paralelismo, **tolerância a falhas** (re-executar tasks perdidas) e shuffle.
- **Escala em hardware comum** — rodava em milhares de máquinas baratas.
- **Tolerância a falhas** — tasks que falham são reexecutadas (dados intermediários persistidos em
  disco).

## Mapeando SQL/operações para MapReduce

- `GROUP BY ... SUM()` → map emite `(grupo, valor)`; reduce soma por grupo.
- `JOIN` → map emite `(chave_join, registro)` de ambas as tabelas; reduce junta por chave (um
  *reduce-side join*, que causa shuffle de ambas).
- `DISTINCT`/`COUNT DISTINCT` → chave = valor; reduce deduplica.

Ou seja, agregações e joins **inevitavelmente** passam por shuffle — a raiz do custo dessas operações
em qualquer sistema distribuído.

## Limitações do Hadoop MapReduce (por que Spark venceu)

- **Disco entre fases** — escreve resultados intermediários em disco (HDFS) a cada map/reduce →
  lento, especialmente para pipelines iterativos (ML, grafos).
- **Rígido** — só map e reduce; pipelines complexos viram muitos jobs encadeados.
- **Verboso** — muito código boilerplate.

[Spark](../05-apache-spark/README.md) resolveu isso processando **em memória** (quando possível),
com um modelo mais rico (DAG de operações, não só map/reduce) e APIs de alto nível
([DataFrame/SQL](../08-rdd-dataframe/README.md)) — mas por baixo, o shuffle e o modelo map/reduce
continuam lá.

## Erros comuns

- Achar que MapReduce é obsoleto e irrelevante (o **modelo** sustenta tudo hoje).
- Não perceber que todo `GROUP BY`/`JOIN` distribuído implica shuffle (herança do reduce).
- Confundir o framework Hadoop MapReduce (em desuso) com o modelo (atual).

## Boas práticas (do modelo)

- Faça o máximo no **map** (local) e minimize o que vai para o **reduce** (shuffle) — ex.:
  pré-agregar no map (*combiner*) reduz o volume do shuffle.
- Pense em termos de chaves: uma chave mal escolhida causa [skew](../04-distributed-joins-skew/README.md)
  no reduce.

## Relação com outros conceitos

- Origem do [shuffle](../03-partitioning-shuffle/README.md) e dos
  [distributed joins](../04-distributed-joins-skew/README.md).
- Evoluiu para [Spark](../05-apache-spark/README.md).
- Base de [batch processing](../../01-foundations/06-batch-vs-streaming/README.md).

## Exercícios

1. Escreva map/reduce (pseudocódigo) para contar pedidos por UF.
2. Expresse um `JOIN` entre pedidos e clientes como map/reduce e aponte onde ocorre o shuffle.
3. Explique por que escrever em disco entre fases tornava o Hadoop MapReduce lento para ML iterativo.
4. Mostre como um *combiner* (pré-agregação no map) reduz o volume do shuffle no word count.

## Referências

- Dean, J.; Ghemawat, S. "MapReduce: Simplified Data Processing on Large Clusters", OSDI 2004.
- Kleppmann, M. *DDIA* — cap. 10 (batch processing / MapReduce).
