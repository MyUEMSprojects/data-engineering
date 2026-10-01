# Cost management (FinOps para dados)

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)

## Por que importa

Na nuvem, **cada decisão técnica vira dinheiro** — e dados são um dos maiores centros de custo
(storage, compute, egress, warehouses). Sem governança, a fatura cresce silenciosamente. **FinOps** é a
prática de alinhar engenharia, finanças e negócio para otimizar custo **sem sacrificar valor**.

## Anatomia do custo em dados

| Fonte | O que cobra | Alavancas |
| --- | --- | --- |
| **Storage** | GB/mês por classe | lifecycle, classes frias, compressão/Parquet, apagar o desnecessário |
| **Compute** | tempo/recursos | clusters efêmeros, spot, rightsizing, autoscaling, desligar ocioso |
| **Warehouse** | bytes lidos (BigQuery) ou tempo de compute (Snowflake/Redshift) | partição/cluster, evitar `SELECT *`, auto-suspend, MVs |
| **Egress/transferência** | dados saindo de região/nuvem/internet | mesma região, endpoints privados, cache |
| **Requests** | operações em object storage/APIs | evitar small files, batching |
| **Serviços gerenciados** | por instância/uso | dimensionamento, reservas |
| **Streaming** | throughput, retenção, partições | retenção, compressão, tiered storage |

## Modelos de preço

- **On-demand** — flexível, mais caro.
- **Reservado / Savings Plans / CUD** — desconto (20–70%) por compromisso 1–3 anos p/ carga estável.
- **Spot/preemptible** — muito barato, interruptível (batch tolerante).
- **Serverless por uso** — paga o que consome (ótimo p/ esporádico; avalie p/ constante).

## Práticas de FinOps

### 1. Visibilidade — **tags** e alocação

Tagueie recursos (`time`, `projeto`, `ambiente`, `dono`) e use **cost allocation** para saber **quem gasta
o quê**. Sem tags, ninguém é responsável. Dashboards (Cost Explorer, Billing Reports) por serviço/tag.

### 2. Orçamento e alertas

Budgets com alertas (50/80/100%) e **detecção de anomalia de custo**. Quotas/limites (ex.:
`maximum_bytes_billed` no BigQuery) protegem contra queries descontroladas.

### 3. Otimização contínua

- **Rightsizing** — reduzir recursos superdimensionados.
- **Desligar ocioso** — clusters de dev, warehouses (auto-suspend), ambientes fora do expediente.
- **Dados frios** — mover para classes baratas; expirar dados sem valor; deduplicar cópias.
- **Eficiência de query/pipeline** — [otimização do warehouse](../../13-data-warehouse/04-query-optimization/README.md),
  [Spark tuning](../../16-distributed-processing/11-performance-tuning/README.md),
  [Parquet + partição](../../08-data-formats/04-parquet/README.md).
- **Incremental em vez de full** ([incremental](../../09-etl-elt/05-full-vs-incremental/README.md)).
- **Compromissos** só para o baseline previsível.

### 4. Cultura

Engenheiros veem o custo do que constroem; custo por pipeline/produto de dados; *showback/chargeback*;
revisões periódicas. Custo é uma **métrica de engenharia**, como latência.

## Armadilhas clássicas de custo em dados

- **Egress inter-região/nuvem** (processar longe do dado).
- **`SELECT *`/sem partição** em warehouse por bytes.
- **Clusters 24/7** e ambientes de dev esquecidos.
- **Small files** (muitas requests).
- **Retenção/versionamento infinitos** (logs, snapshots, time travel).
- **Streaming sobredimensionado** para latência que ninguém precisa.
- **Duplicação** de dados em vários sistemas.
- **Ferramentas SaaS por volume** cobrando linhas ingeridas desnecessárias.

## Unit economics

Meça **custo por unidade de valor**: custo por TB processado, por pipeline, por dashboard, por 1000
eventos. Tendência importa mais que valor absoluto — crescimento de custo > crescimento de valor é alerta.

## Erros comuns

- Sem tags/alocação (ninguém dono do custo).
- Otimizar tarde, só após a conta chegar.
- Reservar capacidade para carga que ainda não é estável.
- Cortar custo sacrificando confiabilidade/qualidade sem medir impacto.
- Ignorar custos de transferência e requests.

## Boas práticas

- Tags obrigatórias (policy/IaC); budgets e alertas; revisão mensal.
- Lifecycle, rightsizing, spot para batch, auto-suspend, incremental.
- Meça unit economics; compartilhe custo com os times donos.
- Combine reservas (baseline) + on-demand/spot (picos).

## Relação com outros conceitos

- [Object storage](../02-object-storage/README.md), [compute](../03-compute/README.md),
  [monitoring](../07-monitoring-autoscaling/README.md), [IaC](../../22-infrastructure-as-code/README.md).
- [Warehouse optimization](../../13-data-warehouse/04-query-optimization/README.md),
  [small files](../../14-data-lake/06-small-files-compaction/README.md).

## Exercícios

1. Liste 8 fontes de custo de uma plataforma de dados e uma ação de redução para cada.
2. Defina um esquema de tags obrigatórias e um budget com alertas.
3. Compare custo de cluster 24/7 vs efêmero + spot para um job diário de 2h.
4. Proponha 3 métricas de unit economics para o time de dados.

## Referências

- FinOps Foundation (finops.org); AWS/GCP/Azure Well-Architected — Cost Optimization.
- Storment, J.R.; Fuller, M. *Cloud FinOps*. O'Reilly.
