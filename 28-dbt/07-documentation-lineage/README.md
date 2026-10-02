# Documentação e lineage

> 🔵 Analytics Platforms · Parte de [28 — dbt](../README.md)

## O que é

O dbt gera, **automaticamente**, documentação navegável e um **grafo de lineage** do seu projeto a
partir dos [models](../02-models/README.md), `ref()`/`source()` e descrições em YAML. É um dos maiores
benefícios do dbt: documentação e [lineage](../../10-data-pipelines/06-data-lineage/README.md) que não
dependem de disciplina manual — saem do próprio código.

## Lineage automático

Como você referencia models com `{{ ref('outro') }}` e fontes com `{{ source(...) }}`, o dbt **sabe**
as dependências e monta o DAG/lineage sem você desenhar nada:

```text
source(raw.pedidos) ─► stg_pedidos ─┐
source(raw.clientes) ─► stg_clientes ─► dim_cliente ─► fct_vendas ─► (BI)
```

Isso dá, de graça:

- **Debugging** — número errado? siga o lineage reverso até a fonte (ver
  [lineage](../../10-data-pipelines/06-data-lineage/README.md)).
- **Impact analysis** — vai mudar um model/coluna? o lineage mostra os dependentes.
- **Onboarding** — entender o fluxo visualmente.

```bash
dbt docs generate     # gera o catálogo + lineage
dbt docs serve        # abre a documentação navegável (com o grafo DAG)
```

## Documentação dos models

Descreva models e colunas no YAML (ao lado dos testes):

```yaml
models:
  - name: fct_vendas
    description: "Uma linha por item vendido (grão: item de pedido pago)."
    columns:
      - name: id
        description: "Identificador do item de venda."
        tests: [unique, not_null]
      - name: valor
        description: "Valor líquido do item em reais."
```

Essas descrições aparecem na documentação gerada e viram a **definição de negócio** daquele dado.

### Docs mais ricas (blocos e markdown)

```markdown
{% docs valor_liquido %}
Valor do item após descontos, **sem** impostos. Fonte: `stg_pedidos.valor`.
{% enddocs %}
```

```yaml
- name: valor
  description: "{{ doc('valor_liquido') }}"
```

Blocos `docs` permitem reutilizar descrições longas/markdown.

## Por que isso importa (documentação que não apodrece)

Documentação separada do código **sempre desatualiza**. No dbt, a doc vive **junto** do model (mesmo
PR), e o lineage é derivado do código real — então reflete a verdade. É a forma mais confiável de
documentar uma plataforma de dados.

## Como contribui para a plataforma

- **Catálogo** — a doc gerada é um mini [catálogo de dados](../../27-data-catalog-metadata/README.md)
  (o que existe, o que significa, quem depende).
- **Governança** — descrições, owners (via `meta`) e classificação alimentam
  [governança](../../25-data-governance/README.md).
- **Qualidade** — testes aparecem junto da doc (o consumidor vê as garantias).
- **Lineage para incidentes** — acelera a [resposta a incidentes](../../24-observability/07-incident-response/README.md).

## exposures e metadados

- **Exposures** — declaram os consumidores a jusante (dashboards, apps, modelos de ML) no lineage,
  estendendo o DAG até o uso final ("este dashboard depende de `fct_vendas`").
- **`meta`/tags** — metadados customizados (owner, domínio, PII) que alimentam governança/catálogo.

## Integração com catálogos externos

O lineage do dbt pode ser exportado/integrado a catálogos corporativos (DataHub, OpenMetadata) e a
[Dagster](../../11-orchestration/03-dagster/README.md) (models viram assets), unificando o lineage de
toda a plataforma (ver [27 — Catalog](../../27-data-catalog-metadata/README.md)).

## Erros comuns

- Não documentar models/colunas (perde o catálogo grátis).
- Documentação separada do código (desatualiza — a graça do dbt é evitar isso).
- Não declarar exposures (lineage para no mart, não mostra o uso final).
- Escrever o nome físico em vez de `ref()` (quebra o lineage automático).

## Boas práticas

- Descreva todo model e coluna-chave no YAML (no mesmo PR da mudança).
- Gere/publique `dbt docs` (ex.: no [CI/CD](../../23-cicd-dataops/README.md)).
- Use blocos `docs` para descrições longas e `exposures` para o uso final.
- Integre o lineage ao catálogo corporativo quando houver.

## Relação com outros conceitos

- [Lineage](../../10-data-pipelines/06-data-lineage/README.md),
  [catálogo/metadata](../../27-data-catalog-metadata/README.md),
  [governança](../../25-data-governance/README.md).
- [Models](../02-models/README.md), [tests](../05-tests/README.md),
  [Dagster assets](../../11-orchestration/03-dagster/README.md).

## Exercícios

1. Documente um model e suas colunas no YAML e gere/visualize a doc com `dbt docs serve`.
2. Explore o grafo de lineage e descreva como usá-lo numa impact analysis.
3. Crie um bloco `docs` reutilizável e referencie-o com `doc()`.
4. Declare uma `exposure` para um dashboard e veja o lineage se estender até ele.

## Referências

- Documentação do dbt — Documentation, Exposures, `doc()`.
