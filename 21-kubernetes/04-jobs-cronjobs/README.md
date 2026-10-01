# Jobs e CronJobs

> 🟣 Cloud & Infra · Parte de [21 — Kubernetes](../README.md)

## O que são

- **Job** — executa Pods **até a conclusão** (run-to-completion): ao terminar com sucesso, acabou.
  Ideal para **batch**: um ETL, uma migração, um backfill, um job Spark.
- **CronJob** — cria Jobs **em um agendamento** (sintaxe [cron](../../02-linux-shell-environment/06-cron/README.md)).
  É o "cron do cluster".

Diferem do [Deployment](../02-pods-deployments/README.md) (serviço que roda para sempre) — em dados, boa
parte do trabalho é **batch**.

## Job

```yaml
apiVersion: batch/v1
kind: Job
metadata: {name: backfill-2024-01-15}
spec:
  backoffLimit: 3                 # retries em falha
  activeDeadlineSeconds: 7200     # timeout total (2h)
  ttlSecondsAfterFinished: 86400  # limpa o Job 1 dia após terminar
  template:
    spec:
      restartPolicy: Never        # ou OnFailure (obrigatório em Job)
      containers:
        - name: etl
          image: ghcr.io/org/pipeline:1.4.2
          args: ["--date", "2024-01-15"]
          resources:
            requests: {cpu: "1", memory: "2Gi"}
            limits: {memory: "4Gi"}
```

### Parâmetros-chave

| Campo | Função |
| --- | --- |
| `backoffLimit` | nº de retries antes de marcar como falho |
| `activeDeadlineSeconds` | timeout do Job inteiro |
| `restartPolicy` | `Never` (novo Pod a cada tentativa) ou `OnFailure` (reinicia o container) |
| `completions` / `parallelism` | execução paralela de N tarefas (processar partições em paralelo) |
| `ttlSecondsAfterFinished` | garbage collection automática |

**Retries** só são seguros se o job for [idempotente](../../09-etl-elt/07-idempotency-retries/README.md).

### Paralelismo (fan-out)

```yaml
spec: {completions: 10, parallelism: 3}   # 10 tarefas, 3 por vez
```

Cada Pod pode processar uma partição/arquivo (índice via `JOB_COMPLETION_INDEX` com *indexed jobs*) —
equivalente ao fan-out de [DAGs](../../10-data-pipelines/02-dags-dependencies/README.md).

## CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: {name: vendas-diario}
spec:
  schedule: "0 2 * * *"
  timeZone: "America/Sao_Paulo"
  concurrencyPolicy: Forbid       # não sobrepor execuções
  startingDeadlineSeconds: 600
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: etl
              image: ghcr.io/org/pipeline:1.4.2
              args: ["--date", "yesterday"]
```

- **`concurrencyPolicy`**: `Allow` | `Forbid` (pula se a anterior roda) | `Replace`. Para pipelines,
  `Forbid` evita sobreposição ([scheduling](../../10-data-pipelines/03-scheduling/README.md)).
- **`timeZone`** explícito evita surpresas de fuso/DST.
- **Limitações**: sem dependências, sem backfill, sem observabilidade de dados, sem *logical date*
  → para pipelines multi-etapa use um [orquestrador](../../11-orchestration/README.md) (Airflow/Dagster).

## Jobs e orquestradores

Orquestradores usam K8s como **executor**: o Airflow `KubernetesPodOperator`/`KubernetesExecutor` cria um
Pod (Job) por tarefa; Spark on K8s cria Pods driver/executor. O K8s fornece **isolamento e elasticidade**;
o orquestrador, **dependências, retries de negócio, backfill e visibilidade**.

## Exemplo de dados: backfill paralelo

```bash
for d in $(seq -w 1 31); do
  kubectl create job backfill-2024-01-$d --image=ghcr.io/org/pipeline:1.4.2 -- --date 2024-01-$d
done
```

(Idempotência por partição torna isso seguro — [backfill](../../09-etl-elt/08-backfill/README.md).)

## Erros comuns

- CronJob como "orquestrador" de pipelines com dependências.
- Job não-idempotente com `backoffLimit` > 0 (duplica).
- Sem `activeDeadlineSeconds`/limits (job travado consome recursos).
- Sem TTL → centenas de Jobs/Pods concluídos acumulados.
- `concurrencyPolicy: Allow` com runs que demoram mais que o intervalo.
- Fuso horário implícito.

## Boas práticas

- Jobs idempotentes e parametrizados (data lógica como argumento); requests/limits; timeout.
- CronJob com `Forbid`, `timeZone`, histórico limitado e TTL.
- Use orquestrador acima do K8s para pipelines reais; K8s Jobs como unidade de execução.

## Relação com outros conceitos

- [Cron](../../02-linux-shell-environment/06-cron/README.md), [scheduling](../../10-data-pipelines/03-scheduling/README.md),
  [orquestração](../../11-orchestration/README.md), [idempotência](../../09-etl-elt/07-idempotency-retries/README.md).
- [Scaling/recursos](../07-scaling-resources/README.md).

## Exercícios

1. Escreva um Job que roda um ETL com retries, timeout e TTL.
2. Escreva um CronJob diário com `Forbid` e fuso explícito.
3. Rode um backfill de 7 dias com `parallelism` e explique a exigência de idempotência.
4. Quando um CronJob deixa de bastar e você precisa de Airflow?

## Referências

- Kubernetes Docs — Jobs, CronJobs; Airflow KubernetesPodOperator; Spark on Kubernetes.
