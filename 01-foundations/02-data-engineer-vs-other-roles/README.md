# Data Engineer vs outros papéis

> 🟢 Foundations · Parte de [01 — Fundamentos](../README.md)

## Por que isso importa

Os papéis de dados se sobrepõem e variam entre empresas. Entender as fronteiras
evita dois erros: estudar a coisa errada para o objetivo que você tem, e, no
trabalho, fazer (ou esperar que outro faça) algo que não é daquele papel. Este
documento compara o Data Engineer com os papéis vizinhos e mostra como se
encaixam num fluxo único.

## O eixo que organiza tudo: dado operacional vs analítico

A maioria das fronteiras cai sobre uma distinção só:

- **Mundo operacional (OLTP)** — sistemas que *rodam o negócio* em tempo real:
  um pedido é criado, um saldo é debitado. Backend Engineers vivem aqui.
- **Mundo analítico (OLAP)** — sistemas que *entendem o negócio*: faturamento
  por região, previsão de churn. Data/ML gente vive aqui.

O Data Engineer é a **ponte**: pega dado do mundo operacional (e de fora) e o
torna útil no mundo analítico. Ver [OLTP vs OLAP](../07-oltp-vs-olap/README.md).

## Comparação papel a papel

### Data Engineer vs Data Analyst

| | Data Engineer | Data Analyst |
| --- | --- | --- |
| Pergunta central | "Como disponibilizar este dado de forma confiável?" | "O que este dado diz sobre o negócio?" |
| Entrega | Pipelines, tabelas, modelos de dados, SLAs | Dashboards, relatórios, análises |
| Ferramentas | Python, SQL, orquestração, cloud | SQL, BI (Looker/Power BI), planilhas |
| Profundidade de eng. | Alta (sistemas, infra) | Menor (consome o que o DE entrega) |

O Analyst é frequentemente o **cliente** do DE: consome as tabelas que o DE
constrói.

### Data Engineer vs Data Scientist

| | Data Engineer | Data Scientist |
| --- | --- | --- |
| Foco | Disponibilizar dados confiáveis em escala | Extrair conhecimento/modelos dos dados |
| Entrega | Datasets, features, infraestrutura de dados | Modelos, experimentos, insights |
| Preocupações | Confiabilidade, escala, custo, qualidade | Acurácia, significância, generalização |

O DS precisa de dados limpos e *features* — que o DE (ou o próprio DS, em times
pequenos) prepara. Ver [DE + ML](../../31-data-engineering-and-ml/README.md).

### Data Engineer vs Backend Engineer

| | Data Engineer | Backend Engineer |
| --- | --- | --- |
| Carga | OLAP / analítica, *throughput* de dados | OLTP / transacional, baixa latência por request |
| Banco típico | Warehouse colunar, lake | PostgreSQL/MySQL, Redis (operacionais) |
| Otimiza para | Processar volumes, consultas analíticas | Responder requests de usuários rápido e correto |
| Semelhanças | Ambos escrevem código, usam Git, APIs, filas, containers | — |

Há muita sobreposição de *skills* de engenharia de software; a diferença é o
tipo de sistema e de carga.

### Data Engineer vs ML Engineer

| | Data Engineer | ML Engineer |
| --- | --- | --- |
| Foco | Dados confiáveis e acessíveis | Modelos robustos em produção |
| Entrega | Pipelines de dados, warehouse/lake, features | Serviços de modelo, pipelines de treino/serving |
| Fronteira | Prepara dados/*features* | Consome dados/*features*, treina e serve modelos |

Na prática a fronteira é borrada por *feature pipelines* e *feature stores* — ver
[DE + ML](../../31-data-engineering-and-ml/README.md).

### Data Engineer vs DevOps/SRE

| | Data Engineer | DevOps / SRE |
| --- | --- | --- |
| Objeto | Dados e pipelines | Infraestrutura e confiabilidade de sistemas |
| Entrega | Pipelines, modelos de dados | CI/CD, infra, monitoramento de sistemas |
| Sobreposição | IaC, containers, CI/CD, observabilidade | — |

O DE moderno usa muito ferramental de DevOps ([containers](../../20-containers/README.md),
[IaC](../../22-infrastructure-as-code/README.md),
[CI/CD](../../23-cicd-dataops/README.md)) — daí o termo **DataOps**.

### Data Engineer vs MLOps

MLOps é "DevOps para ML": automatiza treino, deploy, monitoramento e
*retraining* de modelos. O DE fornece a camada de dados/*features* sobre a qual o
MLOps opera. Ver [DE → MLE → MLOps](../../31-data-engineering-and-ml/README.md).

## Como todos se encaixam

```text
                         ┌─────────────────────────────┐
  Backend Engineer ─────►│  Sistemas operacionais OLTP │
                         └──────────────┬──────────────┘
                                        │ (dados brutos)
                                        ▼
  APIs/eventos/arquivos ───►  ┌───────────────────┐
                              │   DATA ENGINEER   │  ◄── usa DevOps/IaC/CI-CD
                              │ ingestão→storage→ │
                              │ transform→serving │
                              └─────────┬─────────┘
                        ┌───────────────┼────────────────┐
                        ▼               ▼                ▼
                 Data Analyst     Data Scientist     ML Engineer ─► MLOps
                 (BI/relatórios)  (modelos/insights) (modelos em prod)
```

## "Full-cycle" e a realidade das empresas

- Em **startups/times pequenos**, uma pessoa acumula DE + Analyst + às vezes DS.
- Em **empresas grandes**, os papéis se especializam (e surgem variantes:
  Analytics Engineer — foco em [dbt](../../28-dbt/README.md) e modelagem;
  Platform Engineer — foco na plataforma de dados).
- **Analytics Engineer** é um papel intermediário popular: usa SQL/dbt para
  transformar dados já ingeridos em modelos prontos para análise — fica entre DE
  e Analyst.

## Erros comuns

- Achar que DE "é só mexer com Spark/Airflow". Ferramentas são meio; o fim é
  dado confiável.
- Confundir Data Analyst com Data Scientist (análise descritiva vs modelagem
  preditiva/estatística).
- Esperar que o DS limpe e sirva os próprios dados em escala de produção — isso
  é trabalho de engenharia.

## Relação com outros conceitos

- Aprofunda a [introdução](../01-introduction-to-data-engineering/README.md).
- A ponte OLTP→OLAP é detalhada em [OLTP vs OLAP](../07-oltp-vs-olap/README.md).
- A fronteira com ML vive no módulo [31](../../31-data-engineering-and-ml/README.md).

## Exercícios

1. **Conceitual.** Para cada papel (Analyst, DS, MLE, Backend), escreva uma
   pergunta/entrega que seja claramente *dele* e não do DE.
2. **Cenário.** Numa startup de 6 pessoas sem Data Engineer, que riscos surgem na
   base de dados analíticos? Quem acaba fazendo esse trabalho e com que custo?
3. **Arquitetura.** Desenhe o fluxo de um evento "compra concluída" desde o
   backend até um dashboard de faturamento e um modelo de recomendação, marcando
   onde cada papel atua.

## Referências

- Reis, J.; Housley, M. *Fundamentals of Data Engineering*. O'Reilly, 2022 —
  cap. 1 (papéis e stakeholders).
- dbt Labs — artigos sobre o papel de *Analytics Engineer* (documentação
  oficial).
