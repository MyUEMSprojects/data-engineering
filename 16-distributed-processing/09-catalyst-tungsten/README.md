# Catalyst e Tungsten

> 🟣 Distributed Systems · Parte de [16 — Distributed Processing](../README.md)

## O que são

Os dois motores internos que tornam o [Spark SQL/DataFrame](../06-spark-sql/README.md) rápido:

- **Catalyst** — o **otimizador de queries** do Spark: transforma seu
  [DataFrame](../08-rdd-dataframe/README.md)/SQL num plano de execução eficiente.
- **Tungsten** — o motor de **execução** de baixo nível: gerencia memória binária, cache de CPU e
  geração de código para rodar o plano rápido.

Você não os programa diretamente, mas entendê-los explica **por que** DataFrame/SQL são muito mais
rápidos que RDD e por que certas práticas (funções nativas, evitar UDF Python) importam.

## Catalyst: o otimizador

O Catalyst pega seu plano e o reescreve em etapas:

```text
Query/DataFrame
   │
Plano LÓGICO não resolvido ─► resolve (colunas/tipos via catálogo)
   │
Plano LÓGICO otimizado ─► aplica regras: predicate pushdown, projection pruning,
   │                      constant folding, reordenar filtros, simplificações
Planos FÍSICOS candidatos ─► escolhe por CUSTO (ex.: broadcast vs sort-merge join)
   │
Plano FÍSICO selecionado ─► Tungsten executa
```

Otimizações-chave que ele aplica:

- **Predicate pushdown** — empurra filtros para a leitura da fonte (ex.: só lê row groups do
  [Parquet](../../08-data-formats/04-parquet/README.md) que casam) → menos I/O.
- **Projection pruning** — lê só as colunas usadas (colunar).
- **Partition pruning** — lê só as partições filtradas.
- **Join selection** — escolhe [broadcast](../10-caching-broadcast/README.md) vs sort-merge conforme
  tamanhos/estatísticas.
- **Reordenação/simplificação** — move filtros para antes de joins, elimina colunas/subexpressões.

Por isso **SQL e DataFrame têm a mesma performance** (passam pelo mesmo Catalyst), e por que a lógica
precisa ser "visível" ao otimizador — uma **UDF Python** é uma caixa-preta que o Catalyst **não
otimiza** (daí serem lentas — ver [PySpark](../07-pyspark/README.md)).

## AQE (Adaptive Query Execution)

Desde o Spark 3, o Catalyst ganhou otimização **adaptativa em runtime**: ele ajusta o plano **durante**
a execução, usando estatísticas reais das stages já concluídas. Faz:

- **Coalesce** de partições pós-shuffle pequenas (evita [small files](../../14-data-lake/06-small-files-compaction/README.md)/overhead).
- **Skew join handling** — detecta e divide partições enlistadas ([skew](../04-distributed-joins-skew/README.md)).
- **Troca de estratégia de join** em runtime (ex.: para broadcast ao descobrir que um lado é pequeno).

> **Mantenha o AQE ligado** (`spark.sql.adaptive.enabled=true`, padrão no Spark 3+) — resolve muitos
> problemas automaticamente.

## Tungsten: a execução eficiente

Tungsten otimiza o uso de **CPU e memória**:

- **Gerenciamento de memória off-heap / binário** — representa dados em um formato binário compacto
  (não objetos JVM), reduzindo overhead de garbage collection.
- **Cache-aware** — layouts que aproveitam o cache da CPU.
- **Whole-stage code generation** — gera, em tempo de execução, **código Java especializado** para uma
  stage inteira, fundindo operadores (filter+map+...) num loop único e rápido (em vez de chamar
  funções genéricas por linha).
- Usa [Apache Arrow](../../04-python-for-data-engineering/13-pyarrow/README.md) para transferência
  eficiente Python↔JVM (pandas UDFs).

É o que faz o DataFrame executar perto da velocidade de código nativo, mesmo sendo escrito em
[Python](../07-pyspark/README.md).

## Lendo o plano (explain)

```python
df.explain(True)   # mostra planos lógico, otimizado e físico
```

Procure no plano físico:

- `PushedFilters`/`ColumnPruning` → pushdown funcionando.
- `BroadcastHashJoin` vs `SortMergeJoin` → qual join foi escolhido.
- `Exchange` → [shuffle](../03-partitioning-shuffle/README.md) (custo).
- `AQEShuffleRead`/`*coalesced*` → AQE atuando.

## Implicações práticas (o que você faz com isso)

- **Use funções nativas** (visíveis ao Catalyst), não UDFs Python opacas.
- **Filtre/projete cedo** para o pushdown trabalhar; use Parquet/particionado.
- **Deixe o AQE ligado**; confie na seleção de join (mas verifique broadcast de tabelas pequenas).
- **Leia o `explain()`** para entender o que o otimizador fez.

## Erros comuns

- UDFs Python que cegam o Catalyst (sem otimização).
- Desligar o AQE (perde skew/coalesce automáticos).
- Não aproveitar pushdown (ler CSV sem schema, `SELECT *`, não particionar).
- Otimizar no escuro sem olhar o `explain()`.

## Boas práticas

- Funções nativas + DataFrame/SQL (deixe o Catalyst otimizar).
- AQE ligado; Parquet + partição para pushdown/pruning.
- Leia o plano físico; confirme pushdown, join e shuffles.

## Relação com outros conceitos

- Otimiza [Spark SQL/DataFrame](../06-spark-sql/README.md); contraste com
  [RDD](../08-rdd-dataframe/README.md) (sem otimizador).
- [Shuffle](../03-partitioning-shuffle/README.md), [broadcast](../10-caching-broadcast/README.md),
  [skew](../04-distributed-joins-skew/README.md), [tuning](../11-performance-tuning/README.md).
- Pushdown ⇄ [Parquet](../../08-data-formats/04-parquet/README.md); Arrow ⇄
  [PyArrow](../../04-python-for-data-engineering/13-pyarrow/README.md).

## Exercícios

1. Rode `df.explain(True)` numa query com filtro e join; identifique pushdown e o tipo de join
   escolhido.
2. Explique por que uma UDF Python impede a otimização do Catalyst.
3. Descreva 3 coisas que o AQE faz em runtime e por que mantê-lo ligado.
4. Explique o que é whole-stage codegen e por que acelera a execução.

## Referências

- Armbrust et al. "Spark SQL: Relational Data Processing in Spark" (SIGMOD 2015) — Catalyst.
- Documentação do Spark — AQE, Tungsten, SQL performance.
