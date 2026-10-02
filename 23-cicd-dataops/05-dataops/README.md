# DataOps

> 🟣 Production · Parte de [23 — CI/CD & DataOps](../README.md)

## O que é

**DataOps** é a aplicação de princípios de **DevOps, Lean/Agile e controle estatístico de processo** ao
**ciclo de vida de dados e analytics**: automatizar, testar e monitorar pipelines continuamente, com
colaboração entre quem produz e quem consome dados, para entregar dados **confiáveis, mais rápido**. Não é
uma ferramenta — é uma **cultura + conjunto de práticas**.

## Por que existe

Equipes de dados sofriam com: pipelines frágeis e manuais, erros descobertos pelo usuário final,
deploys lentos e arriscados, silos entre engenharia/analytics/negócio, ausência de testes e de
observabilidade. DataOps ataca isso trazendo disciplina de engenharia ao trabalho com dados.

```text
Dev/Eng de software → DevOps (CI/CD, infra como código, observabilidade)
                         │ aplicado a dados
                         ▼
                      DataOps = DevOps + qualidade de dados + orquestração + colaboração
```

## Princípios (do DataOps Manifesto, resumidos)

- **Entregar valor continuamente**, em iterações curtas.
- **Tratar dados/pipelines como código** — versionados, revisados, testados.
- **Automatizar** testes, deploy e orquestração; reduzir toil manual.
- **Qualidade desde a origem** — testes e monitoramento **no** pipeline, não depois.
- **Observabilidade** — enxergar o que acontece com dados e pipelines.
- **Reprodutibilidade** — ambientes, builds e resultados repetíveis.
- **Colaboração** entre engenharia, analytics, ciência de dados e negócio; feedback rápido.
- **Medir e melhorar** continuamente (métricas de pipeline e de processo).

## As práticas concretas (e onde estudar)

| Prática DataOps | Como se materializa | Onde |
| --- | --- | --- |
| **Controle de versão de tudo** | código, SQL, DAGs, IaC, contratos, docs em Git | [Git/SWE](../../03-git-software-engineering/README.md) |
| **Ambientes isolados e reprodutíveis** | containers, IaC, ambientes efêmeros | [ambientes](../04-environments-artifacts/README.md), [IaC](../../22-infrastructure-as-code/README.md) |
| **CI/CD automatizado** | testar e implantar pipelines/modelos dbt | [CI](../01-continuous-integration/README.md), [CD](../02-continuous-delivery/README.md) |
| **Testes automatizados** | unitários + **testes de dados** + contratos | [pipeline testing](../../10-data-pipelines/07-pipeline-testing/README.md), [data quality](../../12-data-quality/README.md) |
| **Orquestração e idempotência** | DAGs, retries, backfill seguro | [orquestração](../../11-orchestration/README.md), [idempotência](../../09-etl-elt/07-idempotency-retries/README.md) |
| **Observabilidade de dados** | frescor, volume, schema, distribuição, lineage | [observability](../../24-observability/README.md), [lineage](../../10-data-pipelines/06-data-lineage/README.md) |
| **Governança e segurança embutidas** | catálogo, acesso, mascaramento, auditoria | [governança](../../25-data-governance/README.md), [security](../../26-security/README.md) |
| **Data contracts** | acordos explícitos produtor↔consumidor | [contracts](../../29-data-contracts/README.md) |
| **Gestão de incidentes e pós-mortem** | runbooks, blameless, aprendizado | [incident response](../../24-observability/07-incident-response/README.md) |

## Testes de dados no fluxo (o diferencial vs DevOps puro)

Software testa **código**; DataOps testa **código e dados**:

- **Pré-merge (CI)**: testes de lógica com fixtures; `dbt build` em ambiente efêmero.
- **Pós-deploy / a cada execução**: testes de dados em produção (unicidade, nulos, faixas, FKs, frescor,
  anomalias) como **gate** do DAG ([expectation testing](../../12-data-quality/04-expectation-testing/README.md),
  [dbt tests](../../28-dbt/05-tests/README.md)).
- **Contratos** verificados na fronteira entre times.

## Dois "pipelines" no DataOps

Nuance conceitual útil:

1. **Pipeline de dados** (a "fábrica de dados"): ingestão → transformação → entrega, rodando em produção.
2. **Pipeline de desenvolvimento** (a "fábrica de pipelines"): commit → CI → CD → produção, que **entrega
   mudanças** ao primeiro.

DataOps otimiza **ambos** e a interação entre eles.

## Métricas e feedback

- **De entrega** (DORA): frequência de deploy, *lead time*, taxa de falha de mudança, tempo de
  recuperação.
- **De dados/pipeline**: frescor, completude, taxa de falha de runs, tempo até detectar/corrigir
  incidentes, % de testes passando, custo por pipeline.
- **De consumo**: confiança dos usuários, uso das tabelas, tempo para entregar novo dataset.

## Maturidade (caminho prático)

```text
Nível 0: scripts manuais, sem Git, sem testes
Nível 1: Git + orquestrador + alguns testes manuais
Nível 2: CI com testes, ambientes separados, deploy automatizado
Nível 3: testes de dados em runtime, observabilidade, contratos, lineage
Nível 4: self-service, métricas de processo, melhoria contínua, governança automatizada
```

Evolua incrementalmente: comece por **Git + CI + testes** e adicione observabilidade e contratos.

## Cultura

Ownership claro dos dados/pipelines, **blameless post-mortems**, revisão por pares, documentação viva,
colaboração com consumidores, tratar dados **como produto** (ver [data mesh](../../30-advanced/03-data-mesh/README.md)).

## Erros comuns

- Achar que DataOps é "comprar uma ferramenta".
- Testar só código e ignorar os dados em runtime.
- Automatizar sem observabilidade (falhas silenciosas).
- Silos: engenharia entrega, analytics descobre os problemas.
- Processos pesados que travam a entrega (DataOps é sobre **fluxo** rápido e seguro).

## Boas práticas

- Tudo como código; CI/CD; testes de código **e** de dados; observabilidade e alertas.
- Contratos e ownership; incident response com aprendizado.
- Meça fluxo e qualidade; melhore em pequenos passos.

## Relação com outros conceitos

- [CI/CD](../01-continuous-integration/README.md), [data quality](../../12-data-quality/README.md),
  [observability](../../24-observability/README.md), [governança](../../25-data-governance/README.md),
  [contracts](../../29-data-contracts/README.md), [MLOps](../../31-data-engineering-and-ml/README.md).

## Exercícios

1. Avalie a maturidade DataOps de um time fictício e proponha os 3 próximos passos.
2. Liste testes de **código** vs testes de **dados** num pipeline e onde cada um roda.
3. Defina 5 métricas (entrega + dados) para acompanhar a saúde da plataforma.
4. Descreva os "dois pipelines" do DataOps num exemplo com dbt + Airflow.

## Referências

- DataOps Manifesto (dataopsmanifesto.org); Atwal, H. *Practical DataOps*; Kim, G. et al. *The DevOps Handbook*.
- Reis & Housley, *Fundamentals of Data Engineering* — DataOps.
