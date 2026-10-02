# Dagster

> 🔵 Pipelines · Parte de [11 — Orquestração](../README.md)

## O que é

**Dagster** é um orquestrador moderno construído em torno de **assets de dados** (tabelas,
arquivos, modelos de ML) em vez de apenas tarefas. Você declara *quais dados devem existir* e
suas dependências; o Dagster deriva a execução, o lineage e a observabilidade disso. Traz
forte ênfase em **developer experience**, **testabilidade** e **data-awareness**.

## A ideia central: Software-Defined Assets (SDA)

Em vez de "rode a tarefa X", você declara **o asset** que a função produz e de quais assets
ele depende:

```python
from dagster import asset

@asset
def stg_pedidos() -> pd.DataFrame:
    return extrair_e_limpar()

@asset
def fct_vendas(stg_pedidos: pd.DataFrame, dim_cliente: pd.DataFrame) -> pd.DataFrame:
    return montar_fato(stg_pedidos, dim_cliente)   # dependências = parâmetros
```

As **dependências entre assets** viram o grafo automaticamente (parâmetro = upstream). Isso dá
[lineage](../../10-data-pipelines/06-data-lineage/README.md) nativo e alinha a orquestração ao
modelo de dados, não só às tarefas (ver
[conceitos](../01-orchestration-concepts/README.md)).

## Conceitos

| Conceito | O que é |
| --- | --- |
| **Asset** | um dado persistente que o pipeline produz (tabela/arquivo) |
| **Op / Job** | unidade de computação / grafo de ops (modelo mais "tarefa", opcional) |
| **Resource** | dependências injetáveis (conexão a DB, cliente S3) — ótimo p/ testes |
| **IO Manager** | abstrai onde/como ler e gravar o output do asset |
| **Schedule / Sensor** | dispara por tempo / por evento/condição |
| **Partition** | assets particionados (por data) → backfill por partição nativo |
| **Auto-materialize** | materializar assets automaticamente quando upstreams mudam (data-aware) |

## Diferenciais em relação ao Airflow

| Aspecto | Airflow | Dagster |
| --- | --- | --- |
| Modelo | task-centric | **asset/data-centric** |
| Lineage de dados | via extras | **nativo** |
| Testabilidade | possível | **forte** (resources, tipos, I/O managers) |
| Dev experience | madura | moderna (tipos, UI, local dev) |
| Data-aware scheduling | datasets (recente) | **central** (auto-materialize) |
| Maturidade/ecossistema | **maior** | crescendo |

Não é "melhor" em absoluto — é uma filosofia diferente que combina especialmente com stacks
de analytics e com [observabilidade de dados](../../10-data-pipelines/08-pipeline-observability/README.md).

## Resources e testabilidade

Dagster injeta **resources** (ex.: conexão de banco, cliente de storage) nos assets, o que
permite trocar por *mocks* em testes — tornando pipelines
[testáveis](../../10-data-pipelines/07-pipeline-testing/README.md) sem acoplar ao ambiente.
Tipos de input/output são verificados, pegando erros cedo.

## Particionamento e backfill

Assets podem ser **particionados** (ex.: por dia). O Dagster entende as partições e oferece
**backfill** por partição na UI/CLI — alinhado a
[idempotência](../../09-etl-elt/07-idempotency-retries/README.md) e
[scheduling](../../10-data-pipelines/03-scheduling/README.md).

## Integração com dbt

Dagster tem integração de primeira classe com [dbt](../../28-dbt/README.md): cada modelo dbt
vira um asset Dagster, unificando lineage de dbt + ingestão + ML num só grafo observável. É
um dos usos mais populares.

## Rodando

- **Local** (`dagster dev`) — UI e desenvolvimento local fáceis.
- **Produção** — Dagster+ (gerenciado) ou self-hosted em
  [Kubernetes](../../21-kubernetes/README.md)/containers.

## Quando usar / quando NÃO usar

- **Use** quando quer orquestração **orientada a dados**, lineage/observabilidade nativos,
  forte testabilidade, e integração estreita com dbt — típico de plataformas de analytics
  modernas.
- **Considere Airflow** se o ecossistema/comunidade/experiência do time já é Airflow, ou
  [Prefect](../04-prefect/README.md) para fluxos muito dinâmicos.

## Erros comuns

- Tratar Dagster como "Airflow com outra sintaxe" e ignorar o modelo de assets (perde o maior
  benefício).
- Não usar resources/tipos (perde testabilidade).
- Processar dados gigantes dentro do processo do asset sem delegar a engines.

## Boas práticas

- Modele em **assets** com dependências explícitas (lineage grátis).
- Use **resources** e tipos para testar.
- Particione assets por data; aproveite auto-materialize/backfill.
- Integre dbt como assets para um grafo unificado.

## Relação com outros conceitos

- Implementa [conceitos de orquestração](../01-orchestration-concepts/README.md) na forma
  asset-centric; forte em [lineage](../../10-data-pipelines/06-data-lineage/README.md).
- Compara com [Airflow](../02-airflow/README.md) e [Prefect](../04-prefect/README.md).
- Integra [dbt](../../28-dbt/README.md).

## Exercícios

1. Modele 3 assets (staging → dim/fato) e mostre como o grafo/lineage surge das dependências.
2. Injete uma conexão de banco como *resource* e escreva um teste usando um mock.
3. Particione um asset por dia e descreva como faria backfill.
4. Compare, para o seu caso, Dagster (asset-centric) vs Airflow (task-centric).

## Referências

- Documentação oficial do Dagster (docs.dagster.io) — assets, resources, partitions.
- Dagster + dbt integration docs.
