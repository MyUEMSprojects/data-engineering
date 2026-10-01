# Lineage (visão de governança)

> 🟣 Production · Parte de [25 — Data Governance](../README.md)

> A mecânica de captura em pipelines está em [data lineage](../../10-data-pipelines/06-data-lineage/README.md)
> e as ferramentas em [27 — lineage/column lineage](../../27-data-catalog-metadata/02-lineage-column-lineage/README.md).
> Aqui: **por que governança precisa de lineage** e como usá-lo.

## O que é

**Data lineage** é o mapa de **origem → transformações → destino** dos dados: de quais fontes um dataset/
coluna veio, por quais processos passou e quem o consome. Para governança, é a **prova e o mapa de impacto**
do que acontece com os dados.

## Por que governança precisa de lineage

| Necessidade | Como o lineage ajuda |
| --- | --- |
| **Confiança** | "este número vem de onde?" — rastrear até a fonte e transformações |
| **Auditoria e compliance** | demonstrar a cadeia de custódia (regulatórios financeiros, BCBS 239, SOX) |
| **Privacidade (LGPD)** | achar **todos os lugares** onde um dado pessoal foi copiado/derivado (direito de acesso/exclusão — [compliance](../07-compliance-privacy/README.md)) |
| **Análise de impacto** | antes de mudar/descontinuar uma tabela/coluna, ver **quem depende** |
| **Debug/incidentes** | achar a origem de um número errado e o raio de impacto ([incident response](../../24-observability/07-incident-response/README.md)) |
| **Propagação de classificação** | uma coluna PII "contamina" derivados — herdar tag/mascaramento |
| **Racionalização/custo** | achar datasets sem consumidores para aposentar |

## Níveis

- **Table/dataset-level** — quais tabelas alimentam quais. Mais fácil, já muito útil.
- **Column-level** — qual coluna de origem gera qual coluna de destino. Essencial para **privacidade**
  (rastrear um campo PII) e debug fino.
- **Operacional/run-level** — qual execução/versão de código produziu qual dado (reprodutibilidade).
- **Fim-a-fim** — da fonte operacional até o dashboard/modelo de ML (inclui **exposures**/consumidores).

## Como é capturado

- **Declarativo** (dbt: `ref()`/`source()`) — lineage "de graça" ([dbt lineage](../../28-dbt/07-documentation-lineage/README.md)).
- **Parsing de SQL/código** — ferramentas inferem dependências (table/column).
- **Instrumentação — OpenLineage** — pipelines/orquestradores (Airflow, Spark, dbt, Dagster) emitem eventos
  padronizados a um backend (Marquez, DataHub, OpenMetadata).
- **Metadados de plataformas** — query history do warehouse, Unity Catalog, Dataplex, Purview.

## Usos práticos (governança)

1. **Impact analysis antes de mudar**: "vou alterar `clientes.uf` — quais modelos/dashboards quebram?"
   (integre ao [CI](../../23-cicd-dataops/README.md): PR que altera coluna lista consumidores).
2. **Rastreio de PII**: encontre todas as cópias/derivados de `cpf` para aplicar mascaramento/retenção/
   atender solicitação de titular ([masking](../../26-security/07-data-masking-pii/README.md)).
3. **Auditoria**: relatório "de onde vem a receita reportada ao regulador".
4. **Propagação automática de tags** (sensibilidade/certificação) ao longo do grafo.
5. **Depreciação segura**: confirmar ausência de consumidores antes de remover.

## Limites e cuidados

- **Lineage incompleto** (código dinâmico, scripts, planilhas, BI) gera falsa sensação de completude —
  saiba o que **não** está coberto.
- **Column-level** é difícil em SQL complexo/UDFs/Python.
- **Desatualização** se capturado manualmente — automatize.
- **Granularidade vs custo** de armazenar/consultar.
- Lineage mostra **dependência**, não **semântica/qualidade** — combine com catálogo e testes.

## Erros comuns

- Lineage desenhado à mão (desatualiza).
- Só table-level quando a necessidade (PII) exige column-level.
- Não integrar ao fluxo de mudança (lineage existe mas ninguém consulta antes de alterar).
- Ignorar consumidores fora do warehouse (BI, notebooks, modelos).
- Confiar cegamente em lineage parcial.

## Boas práticas

- Capture automaticamente (dbt + OpenLineage + plataforma); cubra fonte → consumo.
- Integre ao PR/CI (impacto) e ao catálogo (descoberta, tags).
- Priorize column-level para dados sensíveis/regulados.
- Declare consumidores (exposures) e documente lacunas conhecidas.

## Relação com outros conceitos

- [Data lineage (pipelines)](../../10-data-pipelines/06-data-lineage/README.md),
  [catálogo](../02-metadata-catalog/README.md), [compliance](../07-compliance-privacy/README.md),
  [27 — Catalog](../../27-data-catalog-metadata/README.md), [dbt](../../28-dbt/07-documentation-lineage/README.md).

## Exercícios

1. Descreva como usaria lineage para atender uma solicitação de exclusão de dados de um titular (LGPD).
2. Faça uma *impact analysis* para renomear uma coluna usada em 3 modelos e 2 dashboards.
3. Explique por que column-level lineage é importante para propagar classificação de PII.
4. Liste 3 lacunas típicas de lineage e como mitigá-las.

## Referências

- OpenLineage (openlineage.io); DAMA-DMBOK (lineage); documentação de DataHub/OpenMetadata/Purview.
