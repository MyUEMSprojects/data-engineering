# Compute

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)

## O que é

As opções para **executar código/processamento** na nuvem, do mais controle ao mais abstrato:
**máquinas virtuais**, **containers/orquestradores**, **clusters de dados gerenciados** e
**serverless**. A escolha depende da carga (batch, streaming, serviço), escala, controle e custo.

## Opções

### Máquinas virtuais (VMs)

EC2 / Compute Engine / Azure VMs. Controle total (SO, rede, disco); você opera patching, scaling, HA.
Famílias: uso geral, otimizada p/ memória, p/ CPU, p/ armazenamento (NVMe), com GPU. Úteis para
self-hosting (Kafka, bancos, Airflow) e cargas com requisitos específicos.

**Spot/preemptible** instances: até ~60–90% mais baratas, mas podem ser **interrompidas** — ótimas
para batch tolerante a falhas (Spark com checkpoint/retry, [idempotente](../../09-etl-elt/07-idempotency-retries/README.md)).

### Containers e orquestradores

Empacote a aplicação em [container](../../20-containers/README.md) e rode em
**[Kubernetes](../../21-kubernetes/README.md)** (EKS/GKE/AKS) ou serviços simplificados (ECS/Fargate,
Cloud Run, Azure Container Apps). Portabilidade, densidade de uso e escala; padrão para pipelines
modernos (Airflow em K8s, Spark em K8s).

### Clusters de dados gerenciados

Spark/Hadoop/Flink como serviço: **EMR / Dataproc / Azure Synapse-HDInsight / Databricks**. Provisionam
clusters efêmeros para jobs, com autoscaling e integração ao lake. Menos operação que self-managed;
cuide de **clusters efêmeros por job** (pague só durante a execução).

### Serverless

Sem servidores para gerir; escala automática e pagamento por uso:

- **Funções**: Lambda / Cloud Functions / Azure Functions — eventos pequenos (ex.: ao chegar arquivo no
  bucket, dispare validação). Limites de tempo/memória.
- **Containers serverless**: Cloud Run / Fargate / Container Apps — jobs/serviços sem cluster.
- **Dados serverless**: Athena, BigQuery, Glue, Redshift Serverless, Dataflow — executam consultas/ETL sem
  gerir cluster.

## Como escolher

```text
Job batch grande de Spark, esporádico        → cluster efêmero gerenciado (EMR/Dataproc) com spot, ou Databricks
Pipeline containerizado, vários serviços     → Kubernetes / Cloud Run / Fargate
Reação a evento pequeno (arquivo chegou)     → função serverless
Consulta ad-hoc sobre o lake                 → Athena / BigQuery (serverless)
Self-host de Kafka/DB com requisitos custom  → VMs (ou K8s com operator)
```

## Separação compute × storage

Em dados modernos, o dado vive em [object storage](../02-object-storage/README.md) e o **compute é
efêmero e elástico** — escale/desligue compute sem mover dados (princípio central de warehouses e
lakehouses). Cuidado com a **localidade**: compute e dado na mesma região.

## Custo e dimensionamento (resumo)

- **On-demand** (flexível), **reservado/commitment** (desconto por compromisso, p/ carga estável),
  **spot** (barato, interruptível) — combine conforme a previsibilidade.
- Dimensione pela métrica real (CPU, memória, I/O); evite superprovisionar. Ver
  [cost management](../08-cost-management/README.md), [autoscaling](../07-monitoring-autoscaling/README.md).

## Erros comuns

- Clusters ligados 24/7 para jobs que rodam 1h/dia.
- Spot sem tolerância a interrupção (jobs perdidos).
- Serverless para carga constante e pesada sem comparar custo.
- Compute em região/nuvem diferente do dado (egress/latência).
- Superdimensionar "por segurança".

## Boas práticas

- Compute efêmero e elástico; desligue o ocioso; spot para batch tolerante.
- Imagens/containers reprodutíveis; IaC para provisionar ([IaC](../../22-infrastructure-as-code/README.md)).
- Meça utilização e ajuste tamanhos; reserve só o previsível.

## Relação com outros conceitos

- [Containers](../../20-containers/README.md), [Kubernetes](../../21-kubernetes/README.md),
  [Spark](../../16-distributed-processing/README.md), [cost](../08-cost-management/README.md).
- Equivalentes: [AWS](../09-aws/README.md) · [GCP](../10-gcp/README.md) · [Azure](../11-azure/README.md).

## Exercícios

1. Escolha compute para: job Spark noturno de 2h; API de features; trigger por arquivo; Kafka próprio.
2. Explique spot instances e como tornar um job Spark resiliente a elas.
3. Compare cluster 24/7 vs efêmero por job em custo para um job de 1h/dia.

## Referências

- Documentação de EC2/EMR/Lambda, Compute Engine/Dataproc/Cloud Run, Azure VMs/Container Apps.
