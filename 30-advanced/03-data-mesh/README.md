# Data mesh

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: paradigma organizacional (não é tecnologia)*

## O que é

**Data mesh** (Zhamak Dehghani, 2019) é uma abordagem **sociotécnica** para dados analíticos em escala que
**descentraliza** a propriedade e a entrega de dados para **domínios de negócio**, tratando **dados como
produto**, sustentados por uma **plataforma self-service** e **governança federada**. É uma resposta às
limitações do modelo **centralizado** (um time de dados/um data lake ou warehouse monolítico que vira
gargalo).

> Data mesh **não** é um produto nem uma ferramenta. Comprar "um mesh" não existe — é mudança de
> **organização, responsabilidades e arquitetura**.

## O problema que motivou

Plataformas centralizadas escalam mal organizacionalmente:

- O **time central de dados** vira **gargalo**: toda demanda passa por ele, sem conhecer o domínio.
- **Distância** entre quem **produz** o dado (apps/domínios) e quem o **trata** → qualidade ruim, semântica
  perdida, "pipelines frágeis" ([contratos](../../29-data-contracts/README.md)).
- Ownership difuso, backlog infinito, monólito de dados.

## Os 4 princípios

### 1. Domain ownership (propriedade orientada a domínio)
Os **times de domínio** (vendas, logística, risco) são **donos** dos dados analíticos do seu contexto —
responsáveis por produzi-los, mantê-los e evoluí-los. Alinha-se a **DDD** (bounded contexts). Move a
responsabilidade para **quem melhor conhece** o dado ([ownership](../../25-data-governance/04-ownership-stewardship/README.md)).

### 2. Data as a product (dados como produto)
Cada conjunto de dados exposto é um **data product**, com mentalidade de produto: **descobrível,
endereçável, confiável, auto-descritivo, interoperável, seguro**, com **dono**, **SLAs**, **contrato** e
**documentação**. Consumidores são **clientes**.

```text
Data Product = dados + código (pipelines) + metadados/contrato + infra + SLAs + ownership
Portas: saída (tabelas/tópicos/APIs) · descoberta (catálogo) · observabilidade (qualidade/SLO)
```

Ver [contratos de dados](../../29-data-contracts/README.md) como **interface** do produto.

### 3. Self-serve data platform
Um **time de plataforma** oferece **infraestrutura, ferramentas e "caminhos pavimentados"** que reduzem o
custo cognitivo dos domínios criarem data products: templates, IaC, pipelines/CI, catálogo, observabilidade,
qualidade, segurança embutidas (*platform as a product* — [plataforma](../../22-infrastructure-as-code/README.md),
[DataOps](../../23-cicd-dataops/05-dataops/README.md)). Sem isso, a descentralização vira caos.

### 4. Federated computational governance
Governança **federada**: padrões **globais** (interoperabilidade, segurança, privacidade, formatos,
identificação de entidades) definidos por um conselho com representantes dos domínios e **aplicados de
forma automatizada ("computacional")** pela plataforma (policy-as-code), mantendo autonomia local
([arquitetura de governança](../../25-data-governance/08-governance-architecture/README.md)).

## Arquitetura (visão)

```text
Domínio A (vendas)        Domínio B (logística)        Domínio C (risco)
 ├ Data products           ├ Data products              ├ Data products
 └ time dono               └ time dono                  └ time dono
        ▲        interoperam via contratos/padrões        ▲
        └────────── Plataforma de dados self-service ─────┘
                    (catálogo · IaC · pipelines · qualidade · segurança · lineage)
                    + Governança federada (políticas automatizadas)
```

Tecnicamente, **não impõe tecnologia**: cada domínio pode usar warehouse/lakehouse/streaming, desde que
exponha produtos **interoperáveis** (formatos abertos como [Iceberg](../../15-lakehouse/05-apache-iceberg/README.md),
contratos, catálogo comum, identidades/chaves globais).

## Benefícios

- **Escala organizacional** — remove o gargalo central; paralelismo entre domínios.
- **Qualidade e semântica** melhores (quem conhece o dado cuida dele).
- **Agilidade** — autonomia e menor *lead time* para novos produtos de dados.
- **Responsabilização** clara.

## Custos, riscos e críticas (honestidade)

- **Pré-requisitos organizacionais pesados**: maturidade de engenharia de dados **nos domínios**; hoje
  muitos domínios **não têm** esses skills/capacidade — e **duplicar** times de dados em cada domínio é
  caro.
- **Complexidade da plataforma self-service** (o maior investimento) — se fraca, domínios reinventam
  pipelines inconsistentes.
- **Risco de silos novos**: sem governança/interoperabilidade eficazes, troca-se **um monólito** por
  **muitos silos**.
- **Duplicação** de esforço/dados; dificuldade em **joins entre domínios** (identidade, chaves, semântica
  comum — "dados de referência/entidades compartilhadas").
- **Mudança cultural difícil**; exige patrocínio executivo.
- **Hype**: muitos "data mesh" são só renomeação de lake/warehouse com mais ferramentas.

## Quando faz sentido (e quando NÃO)

**Considere** quando: organização **grande**, **muitos domínios** com dados ricos, **gargalo central
comprovado**, **maturidade de engenharia** distribuída, cultura de ownership, e capacidade de **investir em
plataforma**.

**Evite/adie** quando: empresa pequena/média; poucos domínios; time de dados central ainda **não é
gargalo**; baixa maturidade técnica nos domínios; sem patrocínio. Nesses casos, um **warehouse/lakehouse
bem modelado, com ownership e contratos**, resolve mais barato. Dá para **adotar princípios gradualmente**
(ownership + contratos + data products dos domínios mais maduros) sem "mesh completo".

## Mesh e tecnologias/práticas

- **Contratos de dados** e **catálogo/lineage** são a "cola" de interoperabilidade
  ([29](../../29-data-contracts/README.md), [27](../../27-data-catalog-metadata/README.md)).
- **dbt**, **lakehouse/Iceberg**, **Kafka**, orquestradores como blocos dos produtos
  ([dbt](../../28-dbt/README.md)).
- **Policy-as-code** para governança computacional ([IaC](../../22-infrastructure-as-code/README.md)).
- **Marketplace de data products** (catálogo com SLAs/contratos/acesso self-service).

## Mesh vs fabric vs warehouse central

| | Warehouse/lake central | **Data mesh** | [Data fabric](../04-data-fabric/README.md) |
| --- | --- | --- | --- |
| Foco | tecnologia/centralização | **organização/propriedade/produto** | **integração via metadados ativos/automação** |
| Quem constrói | time central | **domínios** (com plataforma) | plataforma/ferramentas |
| Governança | central | **federada** | automatizada por metadados |

(Mesh e fabric **não são excludentes**: fabric pode ser a camada técnica de metadados/automação de um mesh.)

## Erros comuns

- Tratar mesh como produto/tecnologia a ser comprada.
- Descentralizar **sem** plataforma self-service nem governança (caos/silos).
- Adotar em organização pequena (custo > benefício).
- "Data product" = tabela sem dono, contrato nem SLA.
- Ignorar identidade/entidades compartilhadas entre domínios.
- Não investir na mudança cultural/incentivos.

## Boas práticas

- Comece pelo **problema** (gargalo central) e por poucos domínios-piloto maduros.
- Invista cedo em **plataforma self-service** e **contratos**; defina padrões globais mínimos.
- Defina **data product** com dono, contrato, SLAs, catálogo e observabilidade.
- Meça: tempo para criar um produto, qualidade/SLAs, reuso, satisfação.
- Adote **gradualmente**; mantenha pragmatismo.

## Relação com outros conceitos

- [Contratos](../../29-data-contracts/README.md), [governança](../../25-data-governance/README.md),
  [ownership](../../25-data-governance/04-ownership-stewardship/README.md), [catálogo](../../27-data-catalog-metadata/README.md),
  [data fabric](../04-data-fabric/README.md), [DataOps](../../23-cicd-dataops/05-dataops/README.md).

## Exercícios

1. Explique os 4 princípios do data mesh com um exemplo de e-commerce (domínios e data products).
2. Liste 5 sinais de que sua organização **não** está pronta para data mesh.
3. Defina um "data product" completo para `pedidos` (dono, contrato, SLAs, portas, catálogo).
4. Proponha uma adoção gradual dos princípios sem "mesh completo".

## Referências

- Dehghani, Z. *Data Mesh: Delivering Data-Driven Value at Scale*. O'Reilly, 2022; "How to Move Beyond a
  Monolithic Data Lake to a Distributed Data Mesh" (martinfowler.com, 2019).
- Crítica/ressalvas: discussões da comunidade (ex.: artigos de prática sobre custo e pré-requisitos).
