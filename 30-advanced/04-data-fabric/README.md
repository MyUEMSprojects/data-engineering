# Data fabric

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: conceito/abordagem de integração (parte marketing)*

## O que é

**Data fabric** é uma **abordagem arquitetural** (termo popularizado por analistas, sobretudo Gartner e
vendors) que busca **integrar e dar acesso unificado** a dados **distribuídos** (multi-cloud, on-prem,
SaaS) usando **metadados ativos**, **automação** e, frequentemente, **IA/ML** — em vez de **mover tudo**
para um repositório central. A ideia: uma **"malha" de metadados e serviços** sobre os dados onde estão.

> Cuidado: "data fabric" é um **conceito guarda-chuva** com forte presença de **marketing**. Não há uma
> definição técnica única nem uma tecnologia canônica. Avalie **capacidades concretas**, não rótulos.

## O problema que busca resolver

Dados espalhados em muitos sistemas/nuvens/formatos, com **integração manual**, silos e pouca visibilidade.
O fabric propõe **descobrir, conectar, governar e entregar** dados de forma **semi-automática**, baseada em
**metadados**, reduzindo o esforço de integração ponto a ponto.

## Capacidades típicas

| Capacidade | Descrição | Onde estudar |
| --- | --- | --- |
| **Catálogo/metadados ativos** | inventário unificado; metadados que **acionam** automação | [27](../../27-data-catalog-metadata/README.md) |
| **Integração/virtualização** | acesso a dados **sem copiar** (query federada, data virtualization) | [Query engines](../08-query-engines/README.md) |
| **Pipelines/ingestão automatizados** | conectores, CDC, ELT orquestrado | [ETL/ELT](../../09-etl-elt/README.md), [CDC](../01-cdc-debezium/README.md) |
| **Governança e segurança unificadas** | políticas, classificação, mascaramento, acesso centralizados | [25](../../25-data-governance/README.md), [26](../../26-security/README.md) |
| **Qualidade e observabilidade** | testes/monitoramento contínuos | [12](../../12-data-quality/README.md), [24](../../24-observability/README.md) |
| **Recomendações/automação por IA** | sugerir joins, classificar PII, detectar anomalias, otimizar | tendência |
| **Self-service / marketplace** | consumo facilitado de dados e produtos | [mesh](../03-data-mesh/README.md) |

## Como funciona (arquitetura conceitual)

```text
Fontes heterogêneas (DBs, lakes, SaaS, streams, on-prem, multi-cloud)
        │ conectores / virtualização / CDC
        ▼
   Camada de metadados ativos (catálogo + grafo de conhecimento + lineage + políticas)
        │  ▲ aprendizado (padrões de uso, qualidade, anomalias)
        ▼  │
 Serviços: descoberta · integração · governança · qualidade · entrega (SQL/API/streaming)
        ▼
 Consumidores (BI, ML, apps, analistas) — via acesso unificado
```

O núcleo é o **plano de metadados** (grafo de conhecimento) que **orquestra** o resto — daí "metadados
ativos".

## Data fabric vs data mesh

Frequentemente confundidos, mas **ortogonais**:

| | **Data fabric** | **[Data mesh](../03-data-mesh/README.md)** |
| --- | --- | --- |
| Natureza | **tecnologia/arquitetura** (metadados + automação) | **organizacional** (propriedade + produto + governança federada) |
| Pergunta | "como **integrar/automatizar** acesso a dados distribuídos?" | "**quem** é responsável e como **escalar** a entrega?" |
| Abordagem | top-down, automação/IA sobre metadados | bottom-up, domínios donos de produtos |
| Centralização | **lógica** (metadados centralizados) | **descentralizada** (domínios) |
| Combinação | pode ser a **camada técnica** do mesh | pode usar fabric como habilitador |

Resumo: **mesh = quem/como organiza; fabric = com que automação conectar.** Podem coexistir.

## Data virtualization e federação

Um pilar comum: **consultar dados onde estão**, via camada virtual (Denodo, Starburst/Trino, Dremio, Databricks
Lakehouse Federation, BigQuery Omni/federated queries) — evita ETL para todo caso. **Trade-offs**:
performance dependente das fontes/rede, carga em sistemas operacionais, governança de custo, limites em
joins grandes. Para analytics pesado e recorrente, **materializar** (lakehouse/warehouse) ainda vence
([query engines](../08-query-engines/README.md)).

## Ferramentas associadas (exemplos, não endosso)

Plataformas e vendors que usam o rótulo ou capacidades afins: IBM Cloud Pak for Data, Informatica,
Talend/Qlik, NetApp, Microsoft **Fabric/Purview**, Google Dataplex, AWS (Glue/Lake Formation/DataZone),
Databricks Unity Catalog, Starburst/Denodo/Dremio (virtualização), catálogos open source
([DataHub/OpenMetadata](../../27-data-catalog-metadata/04-tools/README.md)). Confira o que cada uma entrega
**de fato**.

## Quando faz sentido

- **Ambientes híbridos/multi-cloud** com muitas fontes e forte necessidade de **governança e descoberta
  unificadas**.
- Quando a **integração manual** é o gargalo e há **metadados** de boa qualidade para automatizar.
- Complemento de um mesh para a **camada de plataforma**.

## Críticas e limites

- **Vago/marketing**: muita promessa de "automação por IA" sem entrega correspondente.
- **Dependência de metadados de qualidade** — "garbage in, garbage out"; metadados ruins = automação ruim.
- **Lock-in** potencial em plataformas proprietárias.
- **Virtualização** não substitui modelagem/ELT quando performance e consistência importam.
- Pode ser **sobreengenharia** para organizações pequenas/stack único.

## Erros comuns

- Comprar "um data fabric" esperando resolver silos sem processo, donos e qualidade de metadados.
- Confundir fabric com mesh (ou achar que um substitui o outro).
- Virtualizar tudo (performance/custo ruins) em vez de materializar o que é recorrente.
- Ignorar governança e segurança na camada unificada.
- Aceitar promessas de IA sem prova de conceito.

## Boas práticas

- Foque em **capacidades concretas** (catálogo ativo, lineage, políticas por tag, conectores, federação) e
  em **POC** com casos reais.
- Invista **primeiro** na qualidade e na automação dos **metadados**.
- Combine virtualização (exploração/casos pontuais) com **materialização** (cargas analíticas críticas).
- Prefira **padrões abertos** (OpenLineage, Iceberg, REST catalogs) para evitar lock-in.

## Relação com outros conceitos

- [Data mesh](../03-data-mesh/README.md), [catálogo/metadados](../../27-data-catalog-metadata/README.md),
  [governança](../../25-data-governance/README.md), [query engines/federação](../08-query-engines/README.md),
  [lakehouse](../../15-lakehouse/README.md).

## Exercícios

1. Explique data fabric vs data mesh em 5 linhas e quando combiná-los.
2. Liste 5 capacidades que você exigiria de uma plataforma "data fabric" numa POC (e como medir).
3. Dê um caso adequado a virtualização e um que exige materialização.
4. Por que a qualidade dos metadados é o fator crítico de sucesso do fabric?

## Referências

- Gartner (conceito de data fabric — materiais públicos); Dehghani, Z. *Data Mesh* (contraste);
  documentação de Purview, Dataplex, Unity Catalog, Denodo, Starburst/Trino.
