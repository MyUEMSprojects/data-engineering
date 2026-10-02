# Tipos de metadados

> 🟣 Production · Parte de [27 — Catalog & Metadata](../README.md)

## O que é

**Metadados** são "dados sobre dados". Cada tipo responde a perguntas diferentes e vem de fontes
diferentes; um bom catálogo **combina todos**. (Visão de governança em
[metadados e catálogo](../../25-data-governance/02-metadata-catalog/README.md); do lake em
[metadata](../../14-data-lake/07-metadata/README.md).)

## Os tipos

### 1. Metadados técnicos

**Como o dado está estruturado e armazenado.** Coletados **automaticamente** dos sistemas.

- Schema: tabelas, colunas, tipos, nulabilidade, chaves, constraints.
- Armazenamento: localização, formato ([Parquet/Iceberg](../../08-data-formats/04-parquet/README.md)),
  partições, tamanho, contagem de linhas, compressão.
- Estatísticas: min/max, cardinalidade, % nulos, distribuição (perfilamento).
- Origem técnica: sistema/banco/schema, conexão, tipo de ativo (tabela, view, tópico, dashboard).

### 2. Metadados de negócio

**O que o dado significa e como se usa.** Exigem **curadoria humana**.

- Descrição e definição de negócio; **glossário** (termos como "cliente ativo", "receita líquida").
- **Domínio**, produto de dados, finalidade, regras de cálculo de métricas.
- **Dono e steward**, contato/canal de suporte ([ownership](../../25-data-governance/04-ownership-stewardship/README.md)).
- Contexto de uso, exemplos de consulta, limitações conhecidas.

### 3. Metadados operacionais

**Como o dado é produzido e se comporta no tempo.** Coletados de pipelines/orquestradores/engines.

- Execução: último run, status, duração, job/DAG/tarefa que produz, versão do código/imagem.
- **Frescor**, volume por carga, SLAs/[SLOs](../../24-observability/05-sli-slo-sla/README.md) e cumprimento.
- Resultados de **testes de qualidade** ([dbt tests/GX](../../12-data-quality/README.md)).
- Uso: quem consulta, frequência, consultas populares, **custo** ([cost](../../19-cloud/08-cost-management/README.md)).
- Incidentes/mudanças recentes.

### 4. Metadados de governança e segurança

**Regras e controles aplicáveis.**

- **Classificação/sensibilidade** (público→restrito), tags **PII** ([classificação](../../25-data-governance/05-access-control-classification/README.md)).
- Políticas de acesso/mascaramento, **retenção**, base legal/finalidade (LGPD), certificação/selo de
  confiança, ciclo de vida (ativo/depreciado).

### 5. Metadados sociais / colaborativos

**Conhecimento coletivo dos usuários.**

- Tags, comentários, perguntas e respostas, avaliações/curtidas, favoritos, "quem usa isto".
- Ajudam a descobrir o que é **confiável e popular**.

### 6. Metadados de lineage (relacional)

**Relações entre ativos**: de onde vem e para onde vai — tratado em
[lineage e column lineage](../02-lineage-column-lineage/README.md).

## Resumo

| Tipo | Pergunta | Fonte principal | Esforço |
| --- | --- | --- | --- |
| Técnico | "como está estruturado?" | automática (conectores) | baixo |
| Negócio | "o que significa?" | humano (stewards) / dbt YAML | alto |
| Operacional | "está saudável/atualizado? quem usa?" | pipelines, query logs | baixo (automático) |
| Governança | "é sensível? quem pode acessar?" | classificação + políticas | médio |
| Social | "o que os outros acham?" | usuários | contínuo |
| Lineage | "de onde vem/quem depende?" | parsing/OpenLineage/dbt | baixo (automático) |

## Metadados ativos (active metadata)

Metadados deixam de ser só **consulta passiva** e passam a **acionar** processos: tag `pii` → aplica
mascaramento; frescor violado → alerta e marca o dataset como "stale"; tabela sem uso/sem dono → sugere
depreciação; mudança de schema → notifica consumidores ([governança](../../25-data-governance/08-governance-architecture/README.md)).

## De onde vêm (no stack)

- **Warehouse/lake/lakehouse**: schema, estatísticas, partições, query history
  ([Iceberg/Delta metadata](../../14-data-lake/07-metadata/README.md), `INFORMATION_SCHEMA`).
- **dbt**: descrições, testes, `meta`, exposures, lineage ([dbt docs](../../28-dbt/07-documentation-lineage/README.md)).
- **Orquestrador** (Airflow/Dagster): runs, durações, dependências; **OpenLineage**.
- **BI** (Looker/Power BI): dashboards, métricas, uso.
- **Data quality** (GX/Soda/dbt tests): resultados.
- **IaC/contratos**: donos, SLAs, schema esperado ([data contracts](../../29-data-contracts/README.md)).
- **Humanos**: negócio, glossário, certificação.

## Armazenamento e modelagem de metadados

Catálogos modelam metadados como **grafo de entidades e relações** (ativo→coluna, ativo→dono, ativo→
lineage) com **APIs** e busca (Elasticsearch/OpenSearch). Padrões abertos: **OpenLineage** (eventos de
lineage), esquemas de metadados do OpenMetadata/DataHub, **Hive Metastore/Glue Catalog** (técnico),
**Iceberg REST Catalog** ([Iceberg](../../15-lakehouse/05-apache-iceberg/README.md)).

## Qualidade dos metadados

Metadados ruins são pior que nenhum (induzem a erro). Garanta: **atualização automática**, cobertura mínima
obrigatória (dono + descrição para tier-1), **validação** (CI verifica YAML/descrição), expiração de
informação obsoleta, métricas de cobertura/saúde.

## Erros comuns

- Só metadados técnicos (catálogo inútil para o analista).
- Metadados de negócio manuais e desatualizados.
- Sem dono/curador para os metadados.
- Não integrar às ferramentas do dia a dia (dbt, BI, orquestrador).
- Fragmentação: metadados em vários silos sem visão unificada.

## Boas práticas

- Automatize técnico/operacional/lineage; invista curadoria no negócio dos ativos críticos.
- Gere metadados do **código** (dbt, IaC, contratos) — fonte única da verdade.
- Metadados ativos; métricas de cobertura; padrões abertos (OpenLineage).

## Relação com outros conceitos

- [Lineage/column lineage](../02-lineage-column-lineage/README.md), [catálogos/discovery](../03-catalogs-discovery/README.md),
  [ferramentas](../04-tools/README.md), [governança](../../25-data-governance/README.md),
  [dbt docs](../../28-dbt/07-documentation-lineage/README.md).

## Exercícios

1. Para a tabela `fct_vendas`, liste 3 metadados de cada tipo (técnico, negócio, operacional, governança).
2. De onde o catálogo obtém cada um? Quais exigem curadoria humana?
3. Dê um exemplo de metadado ativo e a ação automática que ele dispara.
4. Defina 5 métricas de qualidade/cobertura dos metadados.

## Referências

- DAMA-DMBOK (Metadata); Eryurek et al., *Data Governance: The Definitive Guide*;
  openlineage.io; docs de DataHub/OpenMetadata.
