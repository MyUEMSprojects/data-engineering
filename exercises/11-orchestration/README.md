# Exercícios — Módulo 11: Orquestração

Teoria em [11-orchestration](../../11-orchestration/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — O que um orquestrador faz (e não faz)

Liste quatro responsabilidades de um orquestrador e uma coisa que ele **não deve** fazer.

<details><summary>Gabarito</summary>

Faz: agendar, resolver dependências, **retry**, alertar, **backfill**, expor histórico/logs. **Não** deve **transformar dados pesados** nem trafegar dados pelo XCom — ele coordena, quem processa é Spark/dbt/SQL. Ver [conceitos](../../11-orchestration/01-orchestration-concepts/README.md).
</details>

## 2. 🟢 Debugging — O DAG que processa o dia errado

```python
@task
def extract():
    day = date.today()   # <- ?
```

Qual é o defeito e a correção em Airflow?

<details><summary>Gabarito</summary>

`date.today()` ignora a **data lógica**: um backfill/retry processa "hoje". Use a data do intervalo: `ds` do contexto (`def extract(ds=None)`) ou `data_interval_start`. Ver [Airflow](../../11-orchestration/02-airflow/README.md).
</details>

## 3. 🔵 Implementação — Retries inteligentes

Em Airflow, como configurar: 3 retries com atraso de 5 min para erros transitórios, mas **falha imediata** (sem retry) quando o gate de qualidade reprova?

<details><summary>Gabarito</summary>

```python
default_args = {"retries": 3, "retry_delay": timedelta(minutes=5), "retry_exponential_backoff": True}

@task
def gate(ds=None):
    if bad_data(ds):
        raise AirflowFailException("gate reprovou")   # falha PERMANENTE: não tenta de novo
```

`AirflowFailException` pula os retries; exceções comuns respeitam `retries`. Mesmo padrão do [Projeto 03](../../projects/03-orchestration/README.md).
</details>

## 4. 🔵 Conceitual — Catchup e backfill

Um DAG novo tem `start_date` de 6 meses atrás. O que acontece com `catchup=True`? Por que muitos times usam `catchup=False` + backfill explícito?

<details><summary>Gabarito</summary>

Com `catchup=True`, ao ativar, o scheduler cria **um run por intervalo perdido** (~180 runs) — pode sobrecarregar fontes/cluster por acidente. `catchup=False` + `airflow backfill create` torna o reprocessamento uma **decisão explícita**, com limite de concorrência. Ver [backfill](../../09-etl-elt/08-backfill/README.md).
</details>

## 5. 🟣 Arquitetura — Escolher o orquestrador

Compare Airflow, Dagster e Prefect para: (a) 400 DAGs legados e time grande; (b) time pequeno que quer **assets** de dados e testes locais; (c) fluxos dinâmicos em Python com pouca infraestrutura. Recomende e justifique.

<details><summary>Gabarito (um caminho)</summary>

(a) **Airflow** — ecossistema, operadores, adoção. (b) **Dagster** — modelo de *software-defined assets*, testabilidade e linhagem nativa. (c) **Prefect** — fluxos como código Python com baixa fricção operacional. Critérios: curva de aprendizado, ecossistema de integrações, operação (self-hosted × gerenciado), modelo mental (tarefa × ativo). Ver [escolha](../../11-orchestration/05-choosing-an-orchestrator/README.md).
</details>

## 6. 🟣 Arquitetura — Alta disponibilidade e escala

O scheduler é um ponto único de falha? Descreva como tornar o Airflow resiliente e **escalável** em produção.

<details><summary>Gabarito</summary>

Múltiplos *schedulers* (suportado), banco de metadados gerenciado e replicado, executor distribuído (**Celery/Kubernetes**), workers com *autoscaling*, logs remotos (S3), segredos em *secrets backend*, `max_active_runs`/pools para limitar concorrência e DAGs sem lógica pesada (parse rápido). Monitore *scheduler heartbeat* e *task queue latency*. Ver [Kubernetes](../../21-kubernetes/README.md).
</details>
