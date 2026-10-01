# Lineage e column lineage

> 🟣 Production · Parte de [27 — Catalog & Metadata](../README.md)

> Conceito e uso em pipelines: [data lineage](../../10-data-pipelines/06-data-lineage/README.md); visão de
> governança: [lineage](../../25-data-governance/03-lineage/README.md). Aqui: **como é modelado e capturado**
> tecnicamente, com foco em **column-level**.

## Recapitulando

**Lineage** = grafo de **dependências de dados**: quais fontes/transformações/tabelas/colunas produzem
quais outras e quem as consome. Serve a **debug**, **análise de impacto**, **auditoria/LGPD** e
**propagação de classificação**.

## Modelo de dados do lineage

Um grafo **dirigido** (normalmente acíclico no tempo) de **nós** e **arestas**:

- **Nós (ativos)**: dataset/tabela, view, coluna, tópico, arquivo, dashboard, modelo de ML, job/processo.
- **Arestas**: "A → B" (B deriva de A), anotadas com a **transformação** (query/job) e a **execução** (run).
- Duas visões complementares:
  - **Lineage de dataset/coluna** (o *quê* alimenta o *quê*);
  - **Lineage de execução/processo** (qual *run*/versão de código gerou aquele dado) — OpenLineage modela
    `Job`, `Run`, `Dataset`.

```text
raw.pedidos ─► stg_pedidos ─► fct_vendas ─► dashboard "Faturamento"
raw.clientes ─► stg_clientes ─► dim_cliente ─┘
```

## Granularidades

| Nível | O que mostra | Dificuldade | Quando importa |
| --- | --- | --- | --- |
| **Dataset/table** | tabela→tabela | baixa | visão geral, impacto de alto nível |
| **Column** | coluna origem → coluna destino (e a expressão) | **alta** | **PII/LGPD**, debug fino, impacto de renomear coluna |
| **Run/operacional** | execução e versão do código | média | reprodutibilidade, auditoria |
| **Fim-a-fim** | fonte operacional → BI/ML | alta (vários sistemas) | confiança/compliance |

## Column-level lineage

### Por que é valioso
- **Privacidade**: rastrear onde uma coluna **PII** (`cpf`) é copiada/derivada ⇒ aplicar mascaramento,
  atender exclusão ([LGPD](../../26-security/08-lgpd/README.md)).
- **Análise de impacto precisa**: "alterar `clientes.uf` quebra **quais colunas e dashboards**?" (em vez de
  "quais tabelas").
- **Debug**: "esta métrica vem de qual coluna fonte e por qual expressão?"
- **Propagação de tags/descrições** coluna a coluna.

### Como é extraído (parsing de SQL)
A ferramenta analisa a query (AST) e resolve, para cada coluna de saída, **de quais colunas de entrada ela
depende e por qual expressão**:

```sql
create table fct_vendas as
select
  p.id                       as venda_id,        -- venda_id  ← raw.pedidos.id
  c.uf                       as uf,              -- uf        ← dim_cliente.uf
  p.valor * (1 - p.desconto) as valor_liquido    -- valor_liquido ← pedidos.valor, pedidos.desconto
from stg_pedidos p join dim_cliente c on c.id = p.cliente_id;
```

Resultado: `fct_vendas.valor_liquido` depende de `stg_pedidos.valor` e `stg_pedidos.desconto` (via expressão
de multiplicação); `uf` ← `dim_cliente.uf`. Também há **dependência de filtro/join** (colunas que
*influenciam* linhas mesmo sem aparecerem na saída) — algumas ferramentas modelam como "indireta".

Parsers/bibliotecas: **SQLGlot**, `sqllineage`, **OpenLineage SQL parser**, parsers de dbt/DataHub/
OpenMetadata, e **informação nativa de plataformas** (Snowflake `ACCESS_HISTORY`, BigQuery lineage,
Unity Catalog, Dataplex, Purview).

### Limites
SQL dinâmico, `SELECT *`, UDFs, Python/Spark com lógica opaca, `pivot`, joins complexos e planilhas reduzem a
precisão. Para código não-SQL, use **instrumentação** (OpenLineage + facets de coluna) ou declaração
explícita.

## Como o lineage é capturado (mecanismos)

1. **Estático / declarativo**
   - **dbt**: `ref()`/`source()` ⇒ lineage de modelo (e column-level em versões/ferramentas que o derivam)
     ([dbt lineage](../../28-dbt/07-documentation-lineage/README.md)).
   - **Parsing de SQL** do repositório/query history.
2. **Dinâmico / em runtime — OpenLineage**
   Padrão aberto: orquestradores/engines **emitem eventos** (`START`/`COMPLETE`/`FAIL`) com **inputs/outputs**
   (datasets) e **facets** (schema, estatísticas, SQL, lineage de coluna) para um backend (**Marquez**,
   DataHub, OpenMetadata). Integrações: Airflow, Spark, dbt, Flink, Dagster.
3. **Plataformas nativas**: Unity Catalog, Snowflake Horizon, BigQuery/Dataplex, Purview.
4. **Manual**: último recurso (documentar sistemas legados/planilhas).

```json
{ "eventType": "COMPLETE", "job": {"namespace":"airflow","name":"vendas.build_fct"},
  "run": {"runId":"..."},
  "inputs":  [{"namespace":"snowflake","name":"analytics.stg_pedidos"}],
  "outputs": [{"namespace":"snowflake","name":"analytics.fct_vendas",
     "facets":{"columnLineage":{"fields":{"valor_liquido":{"inputFields":[
        {"name":"analytics.stg_pedidos","field":"valor"},{"name":"analytics.stg_pedidos","field":"desconto"}]}}}}}] }
```

## Usos operacionais

- **Impact analysis no PR/CI** — alteração de coluna lista consumidores afetados; bloqueie/alerte
  ([CI](../../23-cicd-dataops/01-continuous-integration/README.md)).
- **Raiz de causa** — de um número errado, suba o grafo até a origem ([incident response](../../24-observability/07-incident-response/README.md)).
- **Propagação de classificação** (PII herda) e de **certificação**.
- **Depreciação segura** — sem consumidores a jusante.
- **Auditoria/regulatório** — cadeia de custódia e *data provenance*.
- **Custo** — achar pipelines caros sem consumo.

## Armazenamento e consulta

Grafo em banco de grafos ou relacional/ES (DataHub usa Elasticsearch + MySQL/Kafka; OpenMetadata
MySQL/ES; Atlas usa JanusGraph). Consultas: *upstream/downstream*, profundidade N, por coluna/tag. Cuidado
com **escala** (milhões de arestas) e **versionamento temporal** (lineage mudou ao longo do tempo).

## Erros comuns

- Achar o lineage completo quando há buracos (scripts, Python, planilhas, BI).
- Só table-level quando a necessidade (PII) exige column-level.
- Lineage manual (desatualiza); sem integração ao fluxo de mudança.
- Ignorar dependências **indiretas** (filtros/joins) na análise de impacto.
- Não versionar/temporalizar (lineage "de hoje" ≠ lineage de quando o dado foi gerado).

## Boas práticas

- Captura **automática** (dbt + OpenLineage + plataforma); cubra fonte→consumo.
- Column-level para dados sensíveis/críticos; documente lacunas conhecidas.
- Integre ao PR/CI, catálogo e governança; use para propagar tags.
- Padronize com **OpenLineage** para evitar lock-in.

## Relação com outros conceitos

- [Lineage em pipelines](../../10-data-pipelines/06-data-lineage/README.md),
  [governança/lineage](../../25-data-governance/03-lineage/README.md),
  [catálogos/discovery](../03-catalogs-discovery/README.md), [ferramentas](../04-tools/README.md),
  [dbt](../../28-dbt/07-documentation-lineage/README.md).

## Exercícios

1. Escreva o column lineage da query `fct_vendas` acima (colunas de origem + expressão).
2. Explique dependências diretas vs indiretas (filtro/join) com um exemplo e por que importam.
3. Esboce um evento OpenLineage de um job Spark que lê A e escreve B.
4. Descreva como usar column lineage para localizar todas as cópias de `cpf`.

## Referências

- OpenLineage spec (openlineage.io); Marquez; SQLGlot; docs de DataHub/OpenMetadata lineage;
  Snowflake ACCESS_HISTORY, Unity Catalog lineage.
