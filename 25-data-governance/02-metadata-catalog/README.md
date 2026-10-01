# Metadados e catálogo (visão de governança)

> 🟣 Production · Parte de [25 — Data Governance](../README.md)
>
> Detalhes de tipos de metadados, discovery e ferramentas estão em
> [27 — Data Catalog & Metadata](../../27-data-catalog-metadata/README.md). Aqui: o **papel na
> governança**.

## O que é

**Metadados** são "dados sobre dados": descrevem **o que**, **onde**, **como**, **quem**, **quando** e
**com que qualidade**. O **catálogo de dados** é o inventário pesquisável desses metadados — o "Google
interno" dos dados da empresa.

## Por que é a fundação da governança

Você não governa o que **não conhece**. O catálogo responde, para qualquer dataset:

- **O que é?** (descrição, definição de negócio, glossário)
- **Onde está / como acesso?** (localização, schema, formato, como solicitar acesso)
- **Quem é o dono?** ([ownership](../04-ownership-stewardship/README.md))
- **É confiável?** (qualidade, frescor, SLAs, certificação)
- **É sensível?** (classificação PII — [classificação](../05-access-control-classification/README.md))
- **De onde vem / quem usa?** ([lineage](../03-lineage/README.md))

## Tipos de metadados

| Tipo | Conteúdo | Exemplos |
| --- | --- | --- |
| **Técnico** | estrutura e armazenamento | schema, tipos, partições, formato, tamanho, localização |
| **De negócio** | significado e contexto | descrição, glossário, definição de métrica, domínio, dono |
| **Operacional** | execução e uso | última carga, frescor, runs, volume, consultas/uso, custo |
| **De governança** | regras e controles | classificação/sensibilidade, retenção, políticas, certificação |
| **Social** | conhecimento coletivo | tags, comentários, avaliações, perguntas |

## Glossário de negócio

Vocabulário **único e acordado** ("cliente ativo", "receita líquida") ligado aos datasets/colunas que o
implementam. Evita o clássico "cada área calcula diferente". Termo ↔ ativos técnicos ↔ dono.

## Do metadado manual ao ativo

- **Manual** (planilhas/wiki) — desatualiza rápido.
- **Automatizado** — coleta metadados técnicos/operacionais dos sistemas (warehouse, lake, dbt, orquestrador,
  BI) e **lineage**; humanos **enriquecem** (descrições, donos, glossário).
- **Active metadata** — metadados **acionam** processos (bloquear acesso a dataset sem dono, alertar
  frescor, aplicar mascaramento por tag, sugerir descontinuação de tabela sem uso).

Fontes de verdade geradas do código: [dbt docs/YAML](../../28-dbt/07-documentation-lineage/README.md)
(descrições, testes, donos via `meta`, exposures), [IaC](../../22-infrastructure-as-code/README.md),
contratos ([data contracts](../../29-data-contracts/README.md)).

## Catálogos e ferramentas

Open source: **DataHub**, **OpenMetadata**, **Apache Atlas**, Amundsen. Nativos de cloud/plataforma:
**AWS Glue Data Catalog + Lake Formation**, **Google Dataplex/Data Catalog**, **Microsoft Purview**,
**Unity Catalog** (Databricks), Snowflake Horizon. Comerciais: Collibra, Alation, Atlan. Ver
[ferramentas](../../27-data-catalog-metadata/04-tools/README.md).

## Boas práticas de catálogo

- **Automatize a ingestão** de metadados; humanos só curam o que máquina não sabe.
- **Dono + descrição mínima obrigatórios** para datasets "tier 1"/certificados.
- **Certificação/selos** (certificado, em revisão, depreciado) e sinais de confiança (qualidade, frescor, uso).
- **Integre ao fluxo**: link do dashboard/BI para o catálogo; descoberta por busca; pedido de acesso no
  catálogo.
- **Meça**: % de datasets com dono/descrição/classificação; buscas sem resultado; uso.
- **Remova o obsoleto** (tabelas sem uso/sem dono).

## Erros comuns

- Catálogo como projeto manual one-off (desatualizado em semanas).
- Metadados técnicos sem contexto de negócio (inútil para o analista).
- Sem donos/curadores → ninguém mantém.
- Ferramenta cara sem adoção (ninguém a abre).
- Glossário divergente entre áreas; sem ligação com os ativos reais.

## Relação com outros conceitos

- [Lineage](../03-lineage/README.md), [ownership](../04-ownership-stewardship/README.md),
  [classificação](../05-access-control-classification/README.md),
  [27 — Catalog & Metadata](../../27-data-catalog-metadata/README.md),
  [metadata do lake](../../14-data-lake/07-metadata/README.md), [dbt docs](../../28-dbt/07-documentation-lineage/README.md).

## Exercícios

1. Liste os metadados (técnico/negócio/operacional/governança) que você exigiria para uma tabela tier-1.
2. Defina 3 termos de glossário de negócio e a quais colunas/tabelas se ligam.
3. Descreva como "active metadata" poderia bloquear acesso a um dataset sem dono.
4. Proponha 4 métricas de saúde do catálogo.

## Referências

- DAMA-DMBOK (Metadata Management); documentação de DataHub, OpenMetadata, Purview, Dataplex.
- Eryurek et al., *Data Governance: The Definitive Guide* — metadados e catálogo.
