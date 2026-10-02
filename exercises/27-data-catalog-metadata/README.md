# Exercícios — Módulo 27: Catálogo e metadados

Teoria em [27-data-catalog-metadata](../../27-data-catalog-metadata/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Tipos de metadados

Dê um exemplo de metadado **técnico**, **de negócio** e **operacional**.

<details><summary>Gabarito</summary>

Técnico: schema, tipos, partições, formato. Negócio: definição de "receita líquida", dono, classificação. Operacional: última atualização, volume, taxa de falha, frescor. Ver [tipos de metadados](../../27-data-catalog-metadata/01-metadata-types/README.md).
</details>

## 2. 🟢 Conceitual — Para que serve um catálogo?

Cite três perguntas que um catálogo responde e por que uma planilha de documentação não escala.

<details><summary>Gabarito</summary>

"Onde está o dado X?", "quem é o dono e é confiável?", "de onde ele vem e quem o consome?". Planilha **desatualiza**, não captura metadados automaticamente (schema, linhagem, uso) nem integra com acesso e qualidade. Ver [catálogos](../../27-data-catalog-metadata/03-catalogs-discovery/README.md).
</details>

## 3. 🔵 Implementação — Metadados como código

Escreva um `YAML` que documente uma tabela (`dono`, `classificação`, colunas com PII) e um **teste de CI** que reprova tabelas sem dono.

<details><summary>Gabarito</summary>

```yaml
table: gold.customer_ltv
owner: time-analytics@empresa.com
classification: confidential
columns:
  - {name: customer_id, pii: true, description: "Identificador pseudonimizado"}
  - {name: lifetime_revenue, pii: false, description: "Soma de pedidos não cancelados"}
```

```python
import sys, yaml, pathlib
bad = [p for p in pathlib.Path("catalog").glob("*.yml") if not yaml.safe_load(p.read_text()).get("owner")]
sys.exit(f"sem dono: {bad}" if bad else 0)
```

</details>

## 4. 🔵 Conceitual — Linhagem de coluna

Por que a linhagem **por coluna** é mais útil que por tabela para análise de impacto? Dê um exemplo.

<details><summary>Gabarito</summary>

Mudar `orders.amount` afeta só as colunas derivadas dele (`revenue`, `ltv`), não toda a tabela `orders` nem todos os seus consumidores. Por tabela você over-alerta; por coluna mede o **impacto real** e acha PII propagada. Ver [linhagem de coluna](../../27-data-catalog-metadata/02-lineage-column-lineage/README.md).
</details>

## 5. 🟣 Arquitetura — Coleta automática

Como coletar metadados e linhagem **sem depender de preenchimento manual**? Que fontes alimentam o catálogo?

<details><summary>Gabarito</summary>

Conectores que leem **schemas** do warehouse/lake, **parser de SQL**/artefatos do dbt (`manifest.json`) e eventos do orquestrador (**OpenLineage**), **logs de consulta** (uso) e métricas de qualidade. Humanos completam o que máquina não sabe (definições de negócio, donos). Ver [ferramentas](../../27-data-catalog-metadata/04-tools/README.md).
</details>

## 6. 🟣 Arquitetura — Escolher uma ferramenta

Compare uma ferramenta open source (DataHub/OpenMetadata) com uma comercial/gerenciada para um time de 15 pessoas. Que critérios importam?

<details><summary>Gabarito</summary>

Critérios: **conectores** disponíveis, linhagem por coluna, custo total (licença × operação própria), governança/RBAC, integração com orquestrador e dbt, esforço de manter. Open source: flexível e sem licença, mas exige operar. Gerenciada: rápida de adotar, custo recorrente e dependência. Para 15 pessoas, comece pelo que o time **consegue operar** e prove valor com poucos domínios.
</details>
