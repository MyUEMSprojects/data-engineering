# Exercícios — Módulo 21: Kubernetes

Teoria em [21-kubernetes](../../21-kubernetes/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Pod, Deployment, Service

Qual o papel de cada um? Por que não se cria Pods "soltos" para aplicações?

<details><summary>Gabarito</summary>

**Pod:** menor unidade (1+ contêineres). **Deployment:** declara réplicas e faz *rolling update*/recriação de Pods que morrem. **Service:** endereço estável (e balanceamento) para um conjunto de Pods. Pod solto não é recriado se o nó falhar. Ver [pods e deployments](../../21-kubernetes/02-pods-deployments/README.md).
</details>

## 2. 🟢 Conceitual — Job × CronJob × Deployment

Para um ETL diário que roda e termina, qual recurso usar? E para uma API sempre ligada?

<details><summary>Gabarito</summary>

ETL diário: **CronJob** (cria **Jobs** que executam até completar, com `backoffLimit`/`ttl`). API contínua: **Deployment** + Service. Ver [jobs e cronjobs](../../21-kubernetes/04-jobs-cronjobs/README.md).
</details>

## 3. 🔵 Implementação — CronJob seguro

Escreva um `CronJob` que roda `etl` todo dia às 02:00 UTC, **sem sobreposição**, com 2 tentativas e limpeza de Jobs concluídos.

<details><summary>Gabarito</summary>

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: {name: etl-daily}
spec:
  schedule: "0 2 * * *"
  timeZone: "UTC"
  concurrencyPolicy: Forbid           # não sobrepõe execuções
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2
      ttlSecondsAfterFinished: 86400
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: etl
              image: registry.example.com/etl:1.4.2     # tag imutável
              resources: {requests: {cpu: "500m", memory: 1Gi}, limits: {memory: 2Gi}}
```
</details>

## 4. 🔵 Debugging — Pod em CrashLoopBackOff / OOMKilled

Um Pod reinicia sem parar com `OOMKilled`. Que comandos usar e que ajustes considerar?

<details><summary>Gabarito</summary>

`kubectl describe pod X` (motivo da última terminação, eventos), `kubectl logs X --previous`, `kubectl top pod`. `OOMKilled` = excedeu o **limite de memória**. Ajuste `resources.limits.memory`/`requests` com base no consumo real, processe em **lotes** menores ou corrija vazamento. Para Spark/JVM, alinhe o heap ao limite do contêiner. Ver [escala e recursos](../../21-kubernetes/07-scaling-resources/README.md).
</details>

## 5. 🟣 Arquitetura — Config e segredos

Como fornecer configuração e credenciais a um job sem colocá-las na imagem? Quais limites do `Secret` padrão e o que usar para endurecer?

<details><summary>Gabarito</summary>

`ConfigMap` para configuração; `Secret` montado como variável/volume. Limite: `Secret` é só **base64** (não cifrado por padrão no etcd) — habilite **criptografia em repouso**, RBAC restrito e prefira um **cofre** (Vault/Secrets Manager) com *External Secrets*/CSI. Nunca em imagem ou no Git. Ver [ConfigMaps e Secrets](../../21-kubernetes/05-configmaps-secrets/README.md).
</details>

## 6. 🟣 Arquitetura — Autoscaling de jobs de dados

Um consumidor Kafka no Kubernetes deve escalar conforme o **lag**. Por que o HPA por CPU é insuficiente e o que usar?

<details><summary>Gabarito</summary>

CPU não reflete **backlog**: um consumidor pode estar ocioso em CPU e atrasado por I/O do destino. Use **KEDA** (escala por métrica externa como *consumer lag*) ou HPA com métricas customizadas. Limite o nº de réplicas ao nº de **partições**. Ver [observabilidade](../../21-kubernetes/08-observability/README.md).
</details>
