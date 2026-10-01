# 10 — Data Pipelines

> 🔵 Nível 3 — Pipelines · Pré: [09 — ETL/ELT](../09-etl-elt/README.md) ·
> Próximo: [11 — Orquestração](../11-orchestration/README.md)

Se [ETL/ELT](../09-etl-elt/README.md) é *o que* se faz com os dados, **data pipelines** é
*como* se estrutura e opera esse trabalho de forma confiável e repetível: o design, as
dependências (DAG), o agendamento, checkpoints, tolerância a falhas, lineage, testes e
observabilidade. É a disciplina de engenharia que transforma scripts em sistemas.

## Por que importa

Um pipeline de produção roda sozinho, todo dia, por anos — lidando com falhas, dados
tardios e mudanças. Projetá-lo bem (modular, idempotente, observável, testável) é o que
evita ser acordado às 3h por um dashboard quebrado.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Pipeline design](01-pipeline-design/README.md) | Princípios de arquitetura de pipelines |
| 02 | [DAGs e dependências](02-dags-dependencies/README.md) | Grafos de tarefas e ordem |
| 03 | [Scheduling](03-scheduling/README.md) | Agendamento, triggers, execution date |
| 04 | [Checkpoints e idempotência](04-checkpoints-idempotency/README.md) | Retomar e reexecutar com segurança |
| 05 | [Fault tolerance](05-fault-tolerance/README.md) | Resiliência a falhas |
| 06 | [Data lineage](06-data-lineage/README.md) | Rastrear a origem dos dados |
| 07 | [Pipeline testing](07-pipeline-testing/README.md) | Testar pipelines (código + dados) |
| 08 | [Pipeline observability](08-pipeline-observability/README.md) | Enxergar o que o pipeline faz |

## Dependências internas

```text
Pipeline design ─► DAGs/dependências ─► Scheduling
       │                                    │
       ▼                                    ▼
Checkpoints/idempotência ─► Fault tolerance
       │
       ▼
Data lineage · Pipeline testing · Pipeline observability
```

## Checkpoint

- [ ] Projetar um pipeline modular (etapas desacopladas, idempotentes).
- [ ] Modelar dependências como DAG e explicar por que não pode ter ciclos.
- [ ] Diferenciar agendamento por tempo, por evento e por sensor; entender *execution date*.
- [ ] Usar checkpoints para retomar jobs longos e garantir idempotência.
- [ ] Projetar tolerância a falhas (retries, atomicidade, dead letter).
- [ ] Explicar lineage e por que é essencial para debugging/impacto.
- [ ] Testar pipeline (unidade, integração, dados) e observá-lo em produção.

## Referências do módulo

- Reis & Housley, *Fundamentals of Data Engineering* — orquestração e pipelines.
- Documentação de Airflow, Dagster, Prefect.
- Google SRE Book (confiabilidade).
