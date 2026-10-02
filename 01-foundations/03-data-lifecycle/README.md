# Ciclo de vida dos dados

> 🟢 Foundations · Parte de [01 — Fundamentos](../README.md)

## O que é

O **ciclo de vida da engenharia de dados** descreve as etapas pelas quais um dado
passa, da sua criação ao seu consumo. É o mapa que organiza *onde* cada
tecnologia do repositório se encaixa. A formulação usada aqui segue Reis &
Housley: **geração → ingestão → armazenamento → transformação → serving**, com
**fundações transversais** (segurança, gestão de dados, DataOps, arquitetura,
orquestração) sustentando todas as etapas.

## Por que pensar em ciclo de vida

Sem um modelo de etapas, decisões viram ad-hoc. Com ele, você consegue:

- Localizar um problema ("isso é de ingestão ou de transformação?").
- Escolher ferramentas por etapa, não por moda.
- Projetar *contratos* entre etapas (o que entra, o que sai, qual garantia).

## As etapas

```text
  GERAÇÃO        INGESTÃO       ARMAZENAMENTO    TRANSFORMAÇÃO       SERVING
 (origem) ──►  (extrair/     ──► (lake/        ──► (limpar/       ──► (BI, ML,
               capturar)         warehouse)        modelar)            apps)

 ───────────── fundações: segurança · data management · DataOps ─────────────
 ───────────── arquitetura de dados · orquestração · engenharia de software ──
```

### 1. Geração (source systems)

Onde o dado nasce: bancos [OLTP](../07-oltp-vs-olap/README.md), APIs, eventos de
aplicação, logs, IoT, arquivos, SaaS de terceiros. O DE geralmente **não controla**
a origem, mas precisa entendê-la: esquema, volume, frequência de mudança,
qualidade e se há [CDC](../../09-etl-elt/06-cdc/README.md) disponível.

Perguntas-chave: é batch ou stream? O schema muda? Qual o SLA da fonte? Há PII?

### 2. Ingestão (ingestion)

Trazer o dado da origem para dentro da plataforma. Dois modos:

- **Batch** — em lotes, por agendamento ([scheduling](../../10-data-pipelines/03-scheduling/README.md)).
- **Streaming** — contínuo, evento a evento ([brokers](../../18-message-brokers/README.md)).

Conceitos: *full vs incremental load*, [CDC](../../09-etl-elt/06-cdc/README.md),
[idempotência](../../09-etl-elt/07-idempotency-retries/README.md), *backfill*.
Aprofundado em [ETL/ELT — ingestão](../../09-etl-elt/02-ingestion-extraction/README.md).

### 3. Armazenamento (storage)

Onde o dado repousa. A escolha depende do uso:

- [Object storage](../../19-cloud/02-object-storage/README.md) + [data lake](../../14-data-lake/README.md)
  para dados brutos/semiestruturados baratos e em escala.
- [Data warehouse](../../13-data-warehouse/README.md) para dados modelados e
  consultas analíticas rápidas.
- [Lakehouse](../../15-lakehouse/README.md) para unir os dois.
- [Databases](../../06-databases/README.md) operacionais para serving de baixa
  latência.

O armazenamento não é uma etapa isolada: ele **permeia** as outras (dados brutos,
intermediários e finais vivem em lugares diferentes — ver
[medallion](../../14-data-lake/03-medallion-architecture/README.md)).

### 4. Transformação (transformation)

Transformar dado bruto em dado útil: limpar, deduplicar, validar, juntar,
agregar, modelar ([modelagem dimensional](../../07-data-modeling/04-dimensional-modeling/README.md)).
É onde entram [ETL vs ELT](../../09-etl-elt/01-etl-vs-elt/README.md),
[dbt](../../28-dbt/README.md), [Spark](../../16-distributed-processing/README.md) e
a [qualidade de dados](../../12-data-quality/README.md).

### 5. Serving

Entregar o dado a quem consome, no formato e latência certos:

- **Analytics/BI** — tabelas e views no warehouse.
- **Machine Learning** — datasets de treino e *features* ([feature stores](../../31-data-engineering-and-ml/03-feature-stores-online-offline/README.md)).
- **Aplicações reversas** (*reverse ETL*) — devolver dados tratados a sistemas
  operacionais (CRM, marketing).

## Fundações transversais (undercurrents)

Não são etapas; sustentam todas elas:

| Fundação | Onde estudar |
| --- | --- |
| Segurança | [26 — Security](../../26-security/README.md) |
| Data management / governança | [25 — Governance](../../25-data-governance/README.md), [27 — Catalog](../../27-data-catalog-metadata/README.md) |
| DataOps | [23 — CI/CD & DataOps](../../23-cicd-dataops/README.md) |
| Arquitetura de dados | [04 — Sistemas de dados](../04-data-systems/README.md) |
| Orquestração | [11 — Orchestration](../../11-orchestration/README.md) |
| Engenharia de software | [03 — Git & SWE](../../03-git-software-engineering/README.md) |

## Exemplo concreto (e-commerce)

```text
Geração:      banco de pedidos (Postgres) + eventos de clique (Kafka)
Ingestão:     CDC do Postgres + consumo do tópico Kafka → data lake (raw)
Armazenamento: lake em object storage (Parquet, particionado por data)
Transformação: Spark/dbt → tabelas fato/dimensão (vendas, clientes, produtos)
Serving:      warehouse para dashboards de faturamento + dataset de features
              para o modelo de recomendação
```

## Trade-offs e decisões que atravessam o ciclo

- **Latência vs custo/complexidade** — streaming entrega frescor, mas custa mais
  caro de operar que batch. Ver [batch vs streaming](../06-batch-vs-streaming/README.md).
- **ETL vs ELT** — transformar antes ou depois de carregar. Ver [ETL/ELT](../../09-etl-elt/01-etl-vs-elt/README.md).
- **Schema-on-write vs schema-on-read** — validar na entrada (warehouse) ou na
  leitura (lake). Ver [data lake](../../14-data-lake/04-schema-on-read-write/README.md).

## Erros comuns

- Tratar as etapas como silos sem contratos claros entre elas.
- Pular validação na ingestão e "descobrir" dados ruins só no serving.
- Esquecer as fundações (segurança/governança) até um incidente forçar.

## Relação com outros conceitos

- É a espinha dorsal que organiza quase todos os módulos do repositório.
- Cada etapa vira um ou mais módulos de nível Core/Platform.

## Exercícios

1. **Mapeamento.** Pegue um app que você usa e descreva um dado seu percorrendo
   as 5 etapas.
2. **Contrato.** Defina o "contrato" entre ingestão e transformação de uma tabela
   de pedidos: schema, frequência, garantias de qualidade.
3. **Diagnóstico.** Um número no dashboard está errado. Liste, por etapa, as
   hipóteses de causa e como investigaria cada uma.

## Referências

- Reis, J.; Housley, M. *Fundamentals of Data Engineering*. O'Reilly, 2022 —
  cap. 2 (o ciclo de vida) e cap. 3.
