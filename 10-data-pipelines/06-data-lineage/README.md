# Data lineage

> 🔵 Pipelines · Parte de [10 — Data Pipelines](../README.md)

## O que é

**Data lineage** (linhagem de dados) é o mapa de **de onde cada dado veio e por onde passou**:
quais fontes, transformações e tabelas intermediárias levaram a um determinado campo/tabela.
É o "GPS" do seu pipeline. (A perspectiva de catálogo/ferramentas está em
[27 — Catalog & Metadata](../../27-data-catalog-metadata/02-lineage-column-lineage/README.md);
aqui focamos no papel no pipeline.)

## Por que importa (muito)

- **Debugging** — "o número do dashboard está errado": o lineage mostra o caminho a
  investigar, da coluna errada até a fonte.
- **Impact analysis** — "vou mudar esta tabela/coluna": o lineage mostra **quem depende** dela
  (o que vai quebrar). Essencial antes de qualquer mudança.
- **Confiança/auditoria** — provar a origem de um número (compliance, [LGPD](../../26-security/08-lgpd/README.md)).
- **Onboarding** — entender como os dados fluem na empresa.

```text
fonte_pedidos ─► stg_pedidos ─► fct_vendas ─► dashboard_faturamento
fonte_clientes ─► stg_clientes ─► dim_cliente ─┘
       (table lineage: fluxo entre tabelas)
```

## Níveis de granularidade

- **Table-level lineage** — quais tabelas alimentam quais. Mais comum e já muito útil.
- **Column-level lineage** — qual **coluna** de origem alimenta qual coluna de destino. Mais
  poderoso para debugging ("este campo específico veio de onde?"), mais difícil de capturar.

## Como o lineage é capturado

- **Declarativo (dbt)** — o [dbt](../../28-dbt/README.md) gera o grafo de lineage
  automaticamente a partir das referências `ref()`/`source()` entre modelos. Essa é uma das
  maiores vantagens do dbt: lineage "de graça".
- **Parsing de SQL/código** — ferramentas analisam as queries para inferir as dependências
  (table e column level).
- **Instrumentação / OpenLineage** — pipelines emitem eventos de lineage padronizados
  ([OpenLineage](https://openlineage.io/)), coletados por um backend (Marquez, DataHub).
- **Metadados do orquestrador** — o próprio [DAG](../02-dags-dependencies/README.md) é uma
  forma de lineage de tarefas (ordem de execução, não necessariamente de colunas).

## Lineage vs DAG

O DAG descreve a **ordem de execução das tarefas**; o lineage descreve o **fluxo dos dados**
entre datasets/colunas. Costumam se alinhar, mas não são a mesma coisa: uma tarefa pode ler/
escrever várias tabelas, e o lineage captura essas relações de dados especificamente.

## Usos práticos no dia a dia

1. **Incidente** — métrica errada → siga o lineage reverso até a fonte/transformação com bug.
2. **Mudança** — antes de alterar uma coluna, veja no lineage todos os consumidores a jusante
   e avise-os / ajuste (*impact analysis*).
3. **Deprecação** — identificar tabelas sem consumidores (candidatas a remover).
4. **Qualidade** — correlacionar um problema de qualidade com a etapa onde surgiu.

## Lineage e observabilidade

Lineage + [observabilidade de dados](../08-pipeline-observability/README.md) são
complementares: a observabilidade detecta *que* algo está errado (volume caiu, frescor
atrasou); o lineage ajuda a achar *onde* e *o que mais* é afetado.

## Erros comuns

- Não ter lineage → debugging vira arqueologia (ninguém sabe de onde o número vem).
- Confiar só no conhecimento tribal ("pergunta pro fulano").
- Mudar uma tabela sem checar quem depende (quebra relatórios a jusante).
- Lineage desatualizado (capturado manualmente, divergente do real).

## Boas práticas

- Capture lineage **automaticamente** (dbt, OpenLineage) — manual desatualiza.
- Use *impact analysis* antes de toda mudança de schema/semântica.
- Integre lineage ao [catálogo](../../27-data-catalog-metadata/README.md) para descoberta.
- Busque column-level onde o debugging fino compensa.

## Relação com outros conceitos

- Ferramentas/catálogo: [27 — Catalog & Metadata](../../27-data-catalog-metadata/02-lineage-column-lineage/README.md),
  [governança](../../25-data-governance/03-lineage/README.md).
- Gerado por [dbt](../../28-dbt/07-documentation-lineage/README.md).
- Complementa [observability](../08-pipeline-observability/README.md).

## Exercícios

1. Desenhe o lineage (table-level) de um pipeline que vai de 2 fontes a 1 dashboard.
2. Descreva como você usaria o lineage para investigar um número errado num relatório.
3. Faça uma *impact analysis*: antes de renomear uma coluna, como listar os consumidores?
4. Explique a diferença entre o DAG do orquestrador e o lineage de dados.

## Referências

- OpenLineage (openlineage.io) e Marquez.
- Documentação do dbt — lineage/DAG.
- Reis & Housley, *Fundamentals of Data Engineering* — lineage e metadados.
