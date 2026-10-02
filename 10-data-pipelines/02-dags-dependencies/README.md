# DAGs e dependências

> 🔵 Pipelines · Parte de [10 — Data Pipelines](../README.md)

## O que é

Um **DAG (Directed Acyclic Graph / grafo acíclico dirigido)** é a estrutura que representa
as **tarefas** de um pipeline e suas **dependências**: setas indicam "A precisa terminar
antes de B". "Acíclico" = sem ciclos (A→B→A seria impossível de executar). É o modelo mental
central de orquestradores como [Airflow](../../11-orchestration/02-airflow/README.md).

```text
extract_vendas ─┐
                ├─► transform ─► load_fato ─► testar ─► notificar
extract_clientes┘            ↑
load_dim_cliente ────────────┘
```

## Por que DAG

Pipelines têm **dependências**: não dá para carregar o fato antes das dimensões; não dá para
transformar antes de extrair. O DAG:

- **Declara a ordem** explicitamente (sem depender de sorte/sequência de script).
- **Habilita paralelismo** — tarefas sem dependência entre si rodam ao mesmo tempo.
- **Permite retry/retomada** de tarefas específicas sem refazer tudo.
- **Documenta** o fluxo (o grafo é a planta do pipeline).

## Por que acíclico

Um ciclo (A depende de B que depende de A) não tem ordem de execução possível — seria um
*deadlock* lógico. O orquestrador **rejeita** ciclos. (Processos iterativos/feedback exigem
outras construções, não um ciclo no DAG.)

## Tipos de dependência

- **Dentro do DAG** — tarefa B depende da tarefa A (mesmo pipeline).
- **Entre DAGs (cross-DAG)** — o pipeline de marts depende do de ingestão ter terminado.
  Resolvido com *sensors*, *datasets*/*assets*, ou triggers.
- **De dados (data-aware)** — "rode quando a tabela X for atualizada" (orquestração
  orientada a dados — Dagster assets, Airflow datasets).

## Fan-out e fan-in

```text
fan-out:   split ─┬─► parte_1 ─┐
                  ├─► parte_2 ─┼─► merge   (fan-in)
                  └─► parte_3 ─┘
```

Processar partições/arquivos em paralelo (fan-out) e depois consolidar (fan-in) é um padrão
comum para escalar.

## Ordem correta: dimensões antes de fatos

No warehouse dimensional, as dependências refletem o modelo: carregue **dimensões** antes dos
**fatos** (as FKs do fato precisam das surrogate keys das dimensões — ver
[star schema](../../07-data-modeling/05-star-schema/README.md)). O DAG codifica isso.

## Dependências implícitas vs explícitas

Confiar em "roda às 2h, então às 3h o dado já está lá" é uma dependência **implícita**
frágil (e se o de 2h atrasar?). Torne-a **explícita**: a tarefa das 3h depende do *sucesso*
da das 2h (via DAG/sensor), não do relógio. Isso elimina uma classe inteira de bugs de
"corrida".

## Granularidade das tarefas

- **Muito grossa** (uma tarefa gigante) → difícil retomar/paralelizar; um erro refaz tudo.
- **Muito fina** (milhares de tarefas minúsculas) → overhead de orquestração.
- **Equilíbrio**: tarefas que representam uma unidade lógica reexecutável (ex.: "carregar
  partição do dia X").

## Idempotência por tarefa

Cada tarefa deve ser [idempotente](../04-checkpoints-idempotency/README.md) — assim o
orquestrador pode fazer retry de tarefas individuais com segurança.

## Representação em código (exemplo conceitual — Airflow)

```python
extract >> validate >> transform >> [load_fato, load_dim]   # dependências
load_dim >> load_fato                                        # dim antes de fato
```

## Erros comuns

- Dependências implícitas por horário (corrida quando upstream atrasa).
- Criar ciclos (o orquestrador rejeita; sinal de modelagem errada).
- Tarefa gigante que refaz tudo em caso de falha.
- Carregar fato antes da dimensão (FKs quebradas).
- Granularidade extrema (overhead) ou nula (monólito).

## Boas práticas

- Modele dependências **explicitamente** no DAG (não por horário).
- Dimensões antes de fatos; respeite a ordem lógica.
- Tarefas idempotentes, com granularidade de "unidade reexecutável".
- Use dependências *data-aware* quando o orquestrador suportar.

## Relação com outros conceitos

- Executado por [orquestradores](../../11-orchestration/README.md).
- [Scheduling](../03-scheduling/README.md), [idempotência](../04-checkpoints-idempotency/README.md),
  [fault tolerance](../05-fault-tolerance/README.md).
- Reflete o modelo de [dados](../../07-data-modeling/README.md).

## Exercícios

1. Desenhe o DAG de um pipeline que ingere clientes e pedidos e constrói fato + dimensão (na
   ordem correta).
2. Explique por que ciclos são proibidos e dê um exemplo de modelagem que evita um ciclo.
3. Transforme uma dependência implícita por horário em explícita por sucesso.
4. Projete fan-out/fan-in para processar 10 arquivos em paralelo e consolidar.

## Referências

- Documentação do Airflow (DAGs, dependencies, datasets) e Dagster (assets).
- Reis & Housley, *Fundamentals of Data Engineering* — orquestração.
