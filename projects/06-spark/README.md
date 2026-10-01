# Projeto 06 — Processamento distribuído com Spark (pipeline + shuffle, skew e tuning MEDIDOS)

> 🟣 Nível: avançado · Módulos: [16 Processamento distribuído](../../16-distributed-processing/README.md),
> [08 Formatos](../../08-data-formats/README.md), [04 Python (PySpark)](../../16-distributed-processing/07-pyspark/README.md) ·
> Anterior: [Projeto 05](../05-data-lake/README.md) · Próximo: [Projeto 07](../07-kafka/README.md)

## Objetivo

Duas coisas, com **código executável e números medidos**:

1. Um **pipeline PySpark** de verdade (raw → silver → gold) com 10 milhões de eventos, que roda **igual em
   modo local e num cluster standalone** (master + 2 workers), com reconciliação entre as camadas.
2. Um **laboratório de performance** com 7 experimentos que *medem* o que os livros afirmam — formato de
   arquivo, estratégia de join, **data skew**, nº de partições de shuffle, cache, UDF Python e layout de
   escrita. Cada experimento mostra **evidência estrutural** (plano, nº de tarefas, razão máx/mediana,
   nº de arquivos), que é o que não varia entre máquinas.

## Arquitetura

```text
 make_events/make_users (Spark gera 10M eventos, 40% de UM usuário "quente")
        │ parquet
        ▼
   /data/lake/events ──► clean_events ──► silver/events (partitionBy event_date)
   /data/lake/users  ──►     │                │
                             └─ enrich (broadcast users) ─► daily_country_metrics ─► gold/daily_country_metrics
                                                    assert: Σ events (gold) == linhas da silver

   Execução:  spark-submit --master local[4]                (1 contêiner)
              spark-submit --master spark://master:7077     (master + 2 workers; mesmo código, mesmo resultado)
```

## Requisitos

Docker + Compose (a imagem `apache/spark:4.0.0` traz Java 17 e PySpark — nada para instalar no host).
~8 GB de RAM livres para os 10M de eventos (ajuste `--events` para menos).

## Estrutura

```text
06-spark/
├── Dockerfile · docker-compose.yml · run.sh · main.py   # imagem, cluster (profile), atalho, entrada do spark-submit
├── src/sparkjobs/
│   ├── session.py      # SparkSession (master vem do spark-submit)
│   ├── datagen.py      # geração sintética DETERMINÍSTICA com skew controlado (hot_share)
│   ├── transforms.py   # clean_events · enrich · daily_country_metrics · detect_hot_keys · salted_join
│   ├── diagnostics.py  # plano (explain), skew de partições, tempos de tarefa via REST API do Spark UI
│   ├── experiments.py  # E1..E7
│   └── cli.py          # generate | pipeline | bench
└── tests/              # 14 testes (PySpark local[2], dentro do contêiner)
```

## Execução

```bash
cd projects/06-spark
docker compose build

# 1) dados: 10M eventos / 200k usuários / 40% dos eventos de um único usuário (volume Docker `data`)
DRIVER_MEM=6g ./run.sh generate --events 10000000
#   events=10,000,000 users=200,000 · shuffle por user_id em 16 partições: máx=4,378,406 linhas vs mediana=375,215 (11.7×)

# 2) pipeline (local[4])
DRIVER_MEM=6g ./run.sh pipeline
#   raw=10,000,000 · silver=10,000,000 · gold=240 linhas   |   reconciliação gold × silver: OK

# 3) laboratório de performance (todos ou alguns: --only e3,e4)
DRIVER_MEM=6g ./run.sh bench

# 4) o MESMO pipeline num cluster standalone (master + 2 workers × 2 cores)
export SPARK_MASTER_UI_PORT=8188                                  # (8080 ocupada? troque)
docker compose --profile cluster up -d --scale worker=2           # UI do master: http://localhost:8188
SPARK_MASTER=spark://master:7077 DRIVER_MEM=2g ./run.sh pipeline  # resultado idêntico ao local
docker compose --profile cluster down -v                          # limpa (inclui o volume de dados)
```

> `./run.sh <cmd>` é um atalho para `docker compose run --rm spark "spark-submit … /app/main.py <cmd>"`.
> Cluster verificado: master `ALIVE` com 2 workers / 4 cores; aplicação `FINISHED` com 4 cores; as 5
> primeiras linhas do *gold* são **idênticas** às da execução local (pipeline determinístico).

## Resultados medidos (10M eventos, `local[4]`, Docker/WSL2)

> ⏱️ Tempos são **indicativos** (melhor de 2 execuções, máquina de estudo). O que vale é a **evidência**.

| Exp. | Variante | Tempo | Evidência (resumo) |
| --- | --- | ---: | --- |
| **E1** formatos | CSV | 1,41 s | 517 MB em disco; lê todo o texto |
| | Parquet | 0,11 s | 189 MB; `ReadSchema: struct<event_type,amount>` (**só 2 colunas**) + `PushedFilters` |
| | Parquet particionado (1 dia) | 0,05 s | `PartitionFilters: event_date = 2024-01-15` (**poda de partições**) |
| **E2** join | sort-merge (broadcast off) | 0,89 s | `SortMergeJoin` · **6** `Exchange` |
| | broadcast hash join | 0,37 s | `BroadcastHashJoin` · **4** `Exchange` (sem shuffle do lado grande) |
| **E3** skew | ingênuo (AQE off) | 2,04 s | stage de reduce: tarefa mais lenta = **9,8×** a mediana (1082 ms vs 110 ms) |
| | AQE *skew join* | 1,25 s | **2,6×** a mediana · "skew join" no plano final |
| | salting manual (16 baldes) | 2,02 s | **1,8×** a mediana; resultado **idêntico** |
| **E4** shuffle | 2000 partições | 2,13 s | 2000 tarefas (overhead de agendamento) |
| | 200 (padrão) | 0,66 s | 200 tarefas |
| | 8 partições | 0,44 s | 8 tarefas |
| | 2000 + AQE coalesce | 0,50 s | AQE reduziu para **4** tarefas |
| **E5** cache | sem `persist` | 5,48 s | join+agg recomputados nas 3 ações |
| | `persist()` | 2,85 s | `Disk Memory Deserialized 1x` |
| **E6** UDF | expressão nativa | 0,12 s | tudo na JVM |
| | UDF Python | 1,94 s | nó `BatchEvalPython` (**~16× mais lento**) |
| **E7** escrita | `partitionBy` direto | 3,89 s | 120 arquivos (~1,5 MB) — **8 tarefas × 30 dias** |
| | `repartition` + `partitionBy` | 5,06 s | 30 arquivos (~4,9 MB) — **paga um shuffle** |
| | `coalesce(2)` | 2,24 s | 2 arquivos (~92 MB) — sem particionar |

Como ler (e o que **não** concluir):

- **E3**: o AQE e o salting reduzem a tarefa mais lenta de ~10× para 2–3× a mediana. O *tempo total* melhora
  menos porque o dado é pequeno; em produção (bilhões de linhas), a tarefa gigante é o que **trava o job**
  e/ou causa *spill*/OOM. O AQE exige limiares ajustados ao demo (`skewedPartitionThresholdInBytes=8m`; os
  padrões, 256 MB, não disparariam com 10M linhas).
- **E4**: sem AQE, o **padrão de 200** é arbitrário — ruim para dados pequenos *e* grandes. Com AQE ligado, o
  Spark junta as partições pequenas sozinho; ainda assim, entenda o parâmetro.
- **E7**: não existe layout "certo": `repartition('event_date')` dá arquivos melhores, mas **custa um shuffle** e,
  se um dia for muito maior que os outros, vira *skew* na escrita. É um trade-off, não uma regra.
- **E1** sem `PushedFilters` em CSV *ajuda pouco*: o CSV precisa ser lido e *parseado* por inteiro.

## Testes

```bash
docker compose run --rm spark "python3 -m pytest /app/tests -c /app/pyproject.toml -q -p no:cacheprovider"
# 14 passed (~20 s). Roda de /work (gravável): o Spark 4 cria ./artifacts no diretório corrente.
```

| Grupo | O que garante |
| --- | --- |
| **datagen** | usuários únicos/países válidos; **determinístico**; `hot_share` ≈ pedido (±3 p.p.) |
| **transforms** | limpeza (nulo, negativo, tipo inválido, duplicata) e data **UTC**; *left join* nunca multiplica linhas e preenche `UNKNOWN`; a **dica de broadcast** muda o plano; receita líquida = compras − reembolsos; `view` não é receita |
| **skew** | `detect_hot_keys` acha `[0]` (e `[]` em dado uniforme); **`salted_join` ≡ join comum** (mesma contagem e mesmos totais) |
| **diagnóstico** | razão de skew alta no dado quente e < 1,5 no uniforme; a REST API devolve tempos por tarefa |
| **experimentos (E1–E7 ponta a ponta)** | os planos contêm o que se afirma (SortMerge/Broadcast, `BatchEvalPython`, `PartitionFilters`); as 3 variantes do E3 dão **o mesmo resultado**; contagem de arquivos do E7 |
| **pipeline** | gold **reconcilia** com a silver |

> 🐞 **Armadilha real encontrada ao construir o benchmark**: com **AQE**, chamar `collect()` de novo **no mesmo
> objeto DataFrame** reaproveita os *stages* de shuffle já materializados — a 2.ª execução levou 0,02 s para
> somar 2M linhas passando por um UDF Python (impossível). O "melhor de 2" estava medindo o **cache**, não a
> consulta. Correção: o DataFrame é **reconstruído** a cada repetição (`best_of(build)`), com teste de
> regressão. Moral: benchmark de Spark exige entender o que é reaproveitado entre ações.

## Decisões arquiteturais e trade-offs

- **Dados gerados no próprio Spark** (determinísticos), com **skew parametrizável**: reprodutível, sem
  arquivos grandes no repositório, e o skew é o ingrediente que torna os experimentos instrutivos.
- **Medir pelo Spark UI/REST** (`/api/v1/.../taskSummary`): razão máx/mediana de tempo das tarefas é a
  assinatura do skew — melhor do que olhar só o tempo total ([skew e joins distribuídos](../../16-distributed-processing/04-distributed-joins-skew/README.md)).
- **Transformações puras (`DataFrame → DataFrame`)** separadas dos *jobs*: testam-se com dados de 5 linhas
  ([PySpark](../../16-distributed-processing/07-pyspark/README.md)).
- **Salting só das chaves quentes** (detectadas por amostragem), não de todas: replicar a dimensão custa
  B× linhas *apenas* onde há skew.
- **Dimensão pequena ⇒ broadcast** ([cache e broadcast](../../16-distributed-processing/10-caching-broadcast/README.md));
  o experimento mostra o corte de `Exchange`. Acima do limite de memória do executor, o broadcast **estoura** — não é grátis.
- **Parquet + partição por data** na silver ([formatos](../../08-data-formats/04-parquet/README.md),
  [particionamento](../../16-distributed-processing/03-partitioning-shuffle/README.md)); cuidado com
  partições demais/pequenas (E7).
- **Cluster standalone no Compose** só para estudo: mostra master/worker/executor, mas **não** é produção
  (em produção: Kubernetes, YARN ou serviços gerenciados — ver [Kubernetes](../../21-kubernetes/README.md) e [Cloud](../../19-cloud/README.md)).
  O código é montado nos workers porque executores importam `sparkjobs` — em produção, empacota-se (`--py-files`/imagem).
- **Imagem fixa `apache/spark:4.0.0`** (não `latest`): reprodutibilidade das medidas.
- **O usuário quente é do país `BR`** (user 0 → `0 % 8`): por isso `BR` domina as primeiras linhas do *gold*
  — consequência intencional do skew, não bug.

## Erros comuns que o projeto expõe

1. **`collect()` em dados grandes** (aqui só em agregados pequenos) → OOM no driver.
2. **UDF Python quando existe função nativa** (E6) — perda de ordem de grandeza; prefira `pyspark.sql.functions` (ou *pandas UDF*/Arrow quando inevitável).
3. **Deixar `spark.sql.shuffle.partitions=200` "porque sim"** (E4).
4. **`partitionBy` sem `repartition`** → explosão de arquivos pequenos (E7).
5. **Ignorar skew** — o job "quase termina" e fica preso em 1 tarefa (E3).
6. **Medir o tempo da 1.ª execução** (JIT/cache de arquivo) ou reexecutar o mesmo DataFrame (AQE) — o benchmark mente.

## Possíveis melhorias (exercícios)

1. Aumente `--events` para 50M e `--hot-share 0.7`; o que muda em E3? Em que ponto o ingênuo **falha** (spill/OOM)?
2. Implemente *salting* para uma **agregação** não algébrica (`countDistinct`) em duas fases e compare.
3. Adicione um E8 com **bucketing** (`bucketBy`) e *sort-merge join sem shuffle*.
4. Troque o UDF por **pandas UDF** (Arrow) e meça o meio-termo (adicione `pandas`/`pyarrow` na imagem).
5. Leia o **Spark UI** (porta 4040 durante o `bench`): ache o stage do skew na aba *Stages* e compare com o REST.
6. Escreva a gold como tabela **Delta/Iceberg** (módulo [15](../../15-lakehouse/README.md)) e faça um *MERGE* incremental por dia.
7. Rode no cluster com `--conf spark.executor.instances` diferentes e relacione paralelismo × nº de tarefas ([tuning](../../16-distributed-processing/11-performance-tuning/README.md)).
8. Orquestre `generate → pipeline` no Airflow do [Projeto 03](../03-orchestration/README.md) via `DockerOperator`/`BashOperator`.

## Referências

- [Spark SQL — Performance Tuning (AQE, skew join, broadcast)](https://spark.apache.org/docs/latest/sql-performance-tuning.html) ·
  [Monitoring REST API](https://spark.apache.org/docs/latest/monitoring.html#rest-api) ·
  [Spark Standalone](https://spark.apache.org/docs/latest/spark-standalone.html).
- Chambers & Zaharia, *Spark: The Definitive Guide*; módulo [16](../../16-distributed-processing/README.md).
