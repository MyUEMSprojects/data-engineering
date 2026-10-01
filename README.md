# Data Engineering — Formação Completa

> Uma trilha de estudos progressiva, prática e profissional em Engenharia de
> Dados — dos fundamentos de sistemas e dados até arquitetura de plataformas de
> dados modernas, cloud, produção e integração com Machine Learning.

Este repositório **não é um roadmap superficial de ferramentas**. É uma
formação estruturada: cada conceito tem seu próprio material, com o *porquê*,
os *trade-offs* e exemplos concretos. A ordem é pedagógica — você entende
sistemas de dados antes de escolher ferramentas, e aprende *por que* cada
tecnologia existe antes de usá-la.

---

## Índice

- [Para quem é](#para-quem-é)
- [Pré-requisitos](#pré-requisitos)
- [Filosofia de estudo](#filosofia-de-estudo)
- [Como usar este repositório](#como-usar-este-repositório)
- [Roadmap e níveis](#roadmap-e-níveis)
- [Árvore de módulos](#árvore-de-módulos)
- [Relação entre os módulos](#relação-entre-os-módulos)
- [Projetos práticos](#projetos-práticos)
- [Exercícios](#exercícios)
- [Ambiente local](#ambiente-local)
- [DE vs DS vs ML vs Backend vs DevOps vs MLOps](#de-vs-ds-vs-ml-vs-backend-vs-devops-vs-mlops)
- [Convenções, contribuição e licença](#convenções-contribuição-e-licença)
- [Referências gerais](#referências-gerais)

---

## Para quem é

- Quem quer **começar** em Engenharia de Dados com uma base sólida.
- Devs/analistas em **transição** que precisam preencher lacunas conceituais.
- Profissionais que querem uma **referência** organizada e uma base de
  **portfólio**.
- Quem estuda **ML** e quer entender onde dados "encontram" modelos
  (feature pipelines, feature stores, MLOps).

## Pré-requisitos

Nenhum conhecimento prévio de Data Engineering é exigido. Ajuda ter:

- Lógica de programação básica.
- Vontade de usar o terminal (o módulo [02 — Linux & Shell](02-linux-shell-environment/README.md) cobre o essencial).
- Uma máquina com Docker (ver [Ambiente local](#ambiente-local)).

## Filosofia de estudo

1. **Fundamentos antes de ferramentas.** Uma ferramenta é uma resposta a um
   problema. Entenda o problema primeiro; a ferramenta fica óbvia e
   substituível.
2. **Trade-offs, não dogmas.** Quase nada em dados é "certo" ou "errado" em
   absoluto — é adequado ou inadequado a um contexto.
3. **Aprender fazendo.** Teoria densa + projetos executáveis + exercícios.
4. **Reprodutibilidade e produção.** Idempotência, testes, observabilidade e
   versionamento são tratados como parte do trabalho, não como extras.
5. **Densidade com clareza.** Cada README busca o equilíbrio entre apostila
   técnica e leitura objetiva.

## Como usar este repositório

- Siga a **ordem numérica** dos módulos para a trilha completa, ou use o
  [roadmap por nível](#roadmap-e-níveis) para pular ao seu ponto.
- Leia o `README.md` de cada tópico; os subtópicos têm READMEs próprios e mais
  específicos.
- Ao final de cada módulo há um **Checkpoint** — só avance quando conseguir
  cumprir os critérios.
- Intercale teoria com os [projetos](#projetos-práticos): eles consolidam
  vários módulos ao mesmo tempo.
- Use os [exercícios](#exercícios) para praticar e autoavaliar.

---

## Roadmap e níveis

A progressão vai de conceitos → habilidades core → produção → especialização.

| Nível | Tema | Módulos |
| --- | --- | --- |
| 🟢 **1. Foundations** | Computação, dados e sistemas | 01, 02, 03 |
| 🔵 **2. Core** | SQL, databases, modeling, Python, formatos | 04, 05, 06, 07, 08 |
| 🔵 **3. Pipelines** | ETL/ELT, pipelines, orquestração, qualidade | 09, 10, 11, 12 |
| 🔵 **4. Analytics Platforms** | Warehouse, lake, lakehouse, dbt | 13, 14, 15, 28 |
| 🟣 **5. Distributed Systems** | Spark, Kafka, streaming, brokers | 16, 17, 18 |
| 🟣 **6. Cloud & Infra** | Cloud, containers, Kubernetes, IaC | 19, 20, 21, 22 |
| 🟣 **7. Production** | CI/CD & DataOps, observabilidade, governança, segurança, catálogo | 23, 24, 25, 26, 27 |
| 🟣 **8. Advanced** | CDC, mesh, event sourcing, query engines, contracts | 29, 30 |
| 🟣 **9. ML Integration** | Data pipelines para ML/MLOps | 31 |

> dbt (módulo 28) aparece conceitualmente no nível 4 (Analytics Platforms),
> mas fica numerado junto dos módulos de ferramentas de transformação para
> manter os números estáveis. Siga a tabela acima para a ordem de estudo.

---

## Árvore de módulos

### 🟢 Nível 1 — Foundations

- **[01 — Fundamentos de Data Engineering](01-foundations/README.md)**
  — o que é DE, papéis, ciclo de vida dos dados, sistemas distribuídos, CAP,
  OLTP vs OLAP, batch vs streaming.
- **[02 — Linux, Shell e Ambiente](02-linux-shell-environment/README.md)**
  — filesystem, processos, permissões, `grep`/`sed`/`awk`, scripting, `cron`,
  SSH, logs, troubleshooting.
- **[03 — Git e Engenharia de Software](03-git-software-engineering/README.md)**
  — Git, branching, rebase, PRs, conventional commits, testes, lint, organização
  de projetos, CI.

### 🔵 Nível 2 — Core

- **[04 — Python para Data Engineering](04-python-for-data-engineering/README.md)**
  — essenciais da linguagem, ambientes/packaging, typing, logging, stdlib para
  DE, concorrência, HTTP, testes, performance, pandas/polars/pyarrow.
- **[05 — SQL](05-sql/README.md)** — do `SELECT` a *window functions*,
  transações, *isolation levels*, `EXPLAIN` e otimização.
- **[06 — Databases](06-databases/README.md)** — relacionais, NoSQL
  (key-value, document, column-family, graph), índices, *partitioning*,
  *sharding*, replicação, backup/DR.
- **[07 — Data Modeling](07-data-modeling/README.md)** — conceitual/lógico/
  físico, normalização, modelagem dimensional, *star/snowflake*, SCD, Data Vault.
- **[08 — Data Formats](08-data-formats/README.md)** — CSV, JSON, Parquet,
  Avro, ORC, Protobuf, *row vs columnar*, compressão, *schema evolution*.

### 🔵 Nível 3 — Pipelines

- **[09 — ETL / ELT](09-etl-elt/README.md)** — ingestão, transformação,
  carga, *full vs incremental*, CDC, idempotência, *backfill*, deduplicação,
  validação, falhas.
- **[10 — Data Pipelines](10-data-pipelines/README.md)** — design, DAGs,
  dependências, *scheduling*, checkpoints, *fault tolerance*, lineage, testes,
  observabilidade.
- **[11 — Orquestração](11-orchestration/README.md)** — conceitos, Airflow,
  Dagster, Prefect, como escolher.
- **[12 — Data Quality](12-data-quality/README.md)** — dimensões de
  qualidade, *data contracts*, validação de schema, *expectation testing*,
  Great Expectations, dbt tests, detecção de anomalias.

### 🔵 Nível 4 — Analytics Platforms

- **[13 — Data Warehouse](13-data-warehouse/README.md)** — conceito,
  arquitetura, *columnar storage*, partitioning/clustering, otimização,
  BigQuery/Snowflake/Redshift.
- **[14 — Data Lake](14-data-lake/README.md)** — *object storage*, arquitetura
  medallion, *schema-on-read/write*, partitioning, *small files*, compaction.
- **[15 — Lakehouse](15-lakehouse/README.md)** — motivação, ACID sobre object
  storage, Delta Lake, Iceberg, Hudi.
- **[28 — dbt](28-dbt/README.md)** — models, sources, seeds, snapshots, tests,
  macros/Jinja, docs/lineage, incremental, deployment.

### 🟣 Nível 5 — Distributed Systems

- **[16 — Distributed Data Processing](16-distributed-processing/README.md)**
  — fundamentos, MapReduce, *shuffle*, *distributed joins*, *skew*, Spark,
  PySpark, Catalyst/Tungsten, tuning.
- **[17 — Streaming](17-streaming/README.md)** — *event-driven*, event/
  processing time, *windows*, *watermarks*, *delivery semantics*, stateful,
  Kafka Streams, Flink, Spark Structured Streaming.
- **[18 — Message Brokers](18-message-brokers/README.md)** — *queue vs log*,
  Kafka, producers/consumers, partitions/offsets/consumer groups, retention/
  replay, *backpressure*, RabbitMQ.

### 🟣 Nível 6 — Cloud & Infra

- **[19 — Cloud](19-cloud/README.md)** — IaaS/PaaS/SaaS, object storage,
  compute, databases gerenciados, networking, IAM/secrets, autoscaling, custo;
  AWS/GCP/Azure.
- **[20 — Containers](20-containers/README.md)** — Docker, images/containers,
  volumes/networks, Compose, registries, multi-stage, segurança.
- **[21 — Kubernetes](21-kubernetes/README.md)** — pods, deployments, services,
  configmaps/secrets, jobs/cronjobs, volumes, scaling, observabilidade (foco DE).
- **[22 — Infrastructure as Code](22-infrastructure-as-code/README.md)** —
  conceito, Terraform, *state*, módulos, providers, *remote state*, ambientes,
  *drift*.

### 🟣 Nível 7 — Production

- **[23 — CI/CD & DataOps](23-cicd-dataops/README.md)** — CI/CD, GitHub
  Actions, test/build/deploy, artefatos, DataOps, estratégias de deploy.
- **[24 — Observability](24-observability/README.md)** — logging, métricas,
  tracing, alertas, SLI/SLO/SLA, *data freshness*, resposta a incidentes.
- **[25 — Data Governance](25-data-governance/README.md)** — metadados,
  catálogo, lineage, ownership, access control, retenção, auditoria, compliance.
- **[26 — Security](26-security/README.md)** — authn/authz, IAM, criptografia,
  secrets, rede, *least privilege*, *data masking*, PII, LGPD.
- **[27 — Data Catalog & Metadata](27-data-catalog-metadata/README.md)** —
  tipos de metadados, lineage de coluna, discovery, *impact analysis*,
  DataHub/OpenMetadata/Atlas.

### 🟣 Nível 8 — Advanced

- **[29 — Data Contracts](29-data-contracts/README.md)** — schema, ownership,
  compatibilidade, versionamento, *contract testing*.
- **[30 — Advanced Data Engineering](30-advanced/README.md)** — CDC/Debezium,
  event sourcing/CQRS, data mesh, data fabric, real-time analytics, query
  engines (Trino/Presto), feature stores, vector databases.

### 🟣 Nível 9 — ML Integration

- **[31 — Data Engineering + Machine Learning](31-data-engineering-and-ml/README.md)**
  — ML data pipelines, feature engineering, feature stores (online/offline),
  training pipelines, serving, *data drift*, DE → MLE → MLOps.

---

## Relação entre os módulos

Dependências conceituais principais (leia de cima para baixo):

```text
Foundations (sistemas, dados, distribuído)
        │
        ▼
SQL ──► Data Modeling ──► Data Warehouse ──► ETL/ELT ──► dbt ──► Orchestration
        │                        │
        ▼                        ▼
   Databases                Data Lake ──► Lakehouse
        │
        ▼
Data Formats (Parquet/Avro) ─────────────┐
                                          ▼
Distributed Systems ──► Spark ──► Streaming ◄── Message Brokers (Kafka)

Cloud ──► Containers ──► Kubernetes ──► IaC
        │
        ▼
CI/CD & DataOps ──► Observability ──► Governance ──► Security ──► Catalog

Data Engineering ──► ML Data Pipeline ──► Feature Engineering ──► Training ──► MLOps
```

Cada README de módulo repete, no topo, suas dependências diretas ("o que você
precisa saber antes") e para onde ele leva ("o que estudar depois").

---

## Projetos práticos

Projetos progressivos que combinam vários módulos. Cada um tem README com
objetivo, arquitetura, requisitos, execução, testes, decisões e trade-offs.

| # | Projeto | Combina |
| --- | --- | --- |
| 01 | [ETL básico](projects/01-basic-etl/README.md) | Python + API/CSV + PostgreSQL |
| 02 | [Analytics Warehouse](projects/02-analytics-warehouse/README.md) | Modelagem dimensional + ELT + dbt |
| 03 | [Orquestração](projects/03-orchestration/README.md) | Airflow + pipeline ponta a ponta |
| 04 | [Data Quality](projects/04-data-quality/README.md) | Validação + testes + observabilidade |
| 05 | [Data Lake](projects/05-data-lake/README.md) | Object storage S3 + Parquet + medalhão |
| 06 | [Spark](projects/06-spark/README.md) | Processamento distribuído |
| 07 | [Kafka](projects/07-kafka/README.md) | Producer → Kafka → consumer → storage |
| 08 | [Streaming](projects/08-streaming/README.md) | Kafka → processamento streaming → analytics |
| 09 | [Cloud](projects/09-cloud/README.md) | Pipeline completo em cloud + IaC |
| 10 | [Capstone](projects/10-capstone/README.md) | Delta lakehouse + ELT + qualidade + observabilidade + CI/CD |

Ver o [índice de projetos](projects/README.md).

## Exercícios

Exercícios por módulo, com dificuldade crescente (conceitual → SQL →
implementação → debugging → arquitetura). Ver o
[índice de exercícios](exercises/README.md).

---

## Ambiente local

A maior parte do repositório roda com **Docker** + **Python 3.12**. Recomendado:

```bash
# 1. Python e venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# 2. Docker (verifique a instalação)
docker --version && docker compose version
```

Cada projeto traz seu próprio `docker-compose.yml` e `requirements.txt`.
Serviços comuns usados (PostgreSQL, Kafka, MinIO, Airflow, Spark) sobem via
Compose — nada precisa ser instalado na máquina além de Docker.

Guia detalhado: [02 — Linux & Shell](02-linux-shell-environment/README.md) e o
README de cada projeto.

---

## DE vs DS vs ML vs Backend vs DevOps vs MLOps

Entender as fronteiras evita estudar a coisa errada. Resumo (detalhado em
[01/02 — Papéis](01-foundations/02-data-engineer-vs-other-roles/README.md)):

| Papel | Foco principal | Entrega típica |
| --- | --- | --- |
| **Data Engineer (DE)** | Mover, armazenar e disponibilizar dados confiáveis em escala | Pipelines, warehouses/lakes, modelos de dados, SLAs de dados |
| **Data Analyst** | Responder perguntas de negócio com dados | Dashboards, relatórios, análises ad-hoc |
| **Data Scientist (DS)** | Extrair conhecimento/modelos a partir de dados | Modelos, experimentos, insights |
| **ML Engineer (MLE)** | Levar modelos a produção de forma robusta | APIs/serviços de modelo, feature/training pipelines |
| **Backend Engineer** | Lógica de aplicação e APIs transacionais (OLTP) | Serviços, APIs, bancos operacionais |
| **DevOps / SRE** | Confiabilidade e automação de infraestrutura | CI/CD, infra, observabilidade de sistemas |
| **MLOps** | Operacionalizar o ciclo de vida de ML | Automação de treino/deploy/monitoramento de modelos |

Fluxo integrado:

```text
Backend/Apps ─► (dados operacionais) ─► Data Engineering ─► Analytics / BI
                                               │
                                               ▼
                                     ML Data Pipeline ─► Data Science / ML
                                               │
                                               ▼
                                         ML Engineering ─► MLOps
```

O Data Engineer é a base: sem dados confiáveis e acessíveis, analytics e ML não
funcionam.

---

## Convenções, contribuição e licença

- **Convenções:** [CONVENTIONS.md](CONVENTIONS.md) (idioma, estrutura, Markdown,
  código, commits).
- **Contribuição:** [CONTRIBUTING.md](CONTRIBUTING.md).
- **Código de conduta:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- **Glossário:** [GLOSSARY.md](GLOSSARY.md).
- **Licença:** [MIT](LICENSE).

### Princípios de engenharia aplicados

Estes princípios aparecem explicados *onde ocorrem*, não como jargão:

- **KISS / DRY** — exemplos e pipelines simples antes de abstrair.
- **Separation of concerns / modularidade** — camadas de ingestão,
  armazenamento, transformação e serving separadas.
- **Idempotência** — reprocessar sem duplicar/corromper (ETL, pipelines).
- **Reproducibility** — ambientes versionados (Docker, IaC, lockfiles).
- **Testability / Observability** — testes de dados, logs, métricas e lineage.
- **Scalability / Maintainability** — escolhas que não travam o crescimento.

---

## Referências gerais

Livros e fontes que atravessam vários módulos (referências específicas estão em
cada README):

- Kleppmann, M. *Designing Data-Intensive Applications*. O'Reilly, 2017.
- Reis, J.; Housley, M. *Fundamentals of Data Engineering*. O'Reilly, 2022.
- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed. Wiley, 2013.
- Akidau, T. et al. *Streaming Systems*. O'Reilly, 2018.
- Documentações oficiais das ferramentas citadas (priorizadas sobre blogs).

---

> **Status:** conteúdo completo — 31 módulos (cada diretório com README próprio), 10 projetos
> executáveis (verificados em Docker) e exercícios por módulo. Validações automáticas no
> [CI](.github/workflows/ci.yml): markdownlint, links relativos, e testes dos
> [projetos](.github/workflows/projects.yml). Contribuições: veja o [CONTRIBUTING](CONTRIBUTING.md).
