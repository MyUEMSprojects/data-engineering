# Sources e seeds

> 🔵 Analytics Platforms · Parte de [28 — dbt](../README.md)

Dois mecanismos de **entrada** de dados num projeto dbt: **sources** (declarar tabelas brutas já no
warehouse) e **seeds** (carregar pequenos CSVs versionados).

## Sources

### O que são

**Sources** declaram as tabelas **brutas** (carregadas por [ingestão](../../09-etl-elt/02-ingestion-extraction/README.md)
externa — Airbyte/Fivetran/scripts) que servem de ponto de partida para o dbt. Você as referencia com
`{{ source('nome', 'tabela') }}` em vez do nome físico.

```yaml
# models/staging/_sources.yml
sources:
  - name: raw                       # grupo lógico
    database: analytics
    schema: raw
    tables:
      - name: pedidos
        loaded_at_field: _ingested_at
        freshness:
          warn_after:  {count: 12, period: hour}
          error_after: {count: 24, period: hour}
      - name: clientes
```

```sql
select * from {{ source('raw', 'pedidos') }}
```

### Por que usar sources (não a tabela direto)

- **Lineage** — o dbt sabe que seus models dependem daquela fonte (aparece no DAG).
- **Desacoplamento** — se a tabela raw muda de schema/nome, você ajusta num lugar só.
- **Freshness** — testar se a fonte está atualizada (ver abaixo).
- **Documentação** — fontes entram nos [docs/lineage](../07-documentation-lineage/README.md).

### Source freshness

```bash
dbt source freshness
```

Verifica, pelo `loaded_at_field`, se os dados brutos chegaram no prazo — pegando upstream atrasado
**antes** de construir os marts (ver [freshness](../../24-observability/06-data-freshness/README.md),
[dbt tests](../05-tests/README.md)). É uma peça-chave de qualidade/observabilidade.

## Seeds

### O que são

**Seeds** são arquivos **CSV pequenos** versionados no projeto (pasta `seeds/`) que o dbt carrega como
tabelas com `dbt seed`. Servem para dados de referência **estáticos e pequenos**.

```text
seeds/
└── mapa_regioes.csv     (uf, regiao)
```

```bash
dbt seed
```

```sql
select * from {{ ref('mapa_regioes') }}   -- seeds são referenciados como models
```

### Quando usar seeds

- **Tabelas de lookup/mapeamento** pequenas e estáveis: UF→região, códigos→descrição, feriados,
  mapeamentos de negócio.
- Dados que fazem sentido **versionar junto do código** (mudam raramente, por PR).

### Quando NÃO usar seeds

- **Dados grandes** — seeds são para CSVs **pequenos** (dezenas/centenas de linhas), não para
  datasets (use [ingestão](../../09-etl-elt/02-ingestion-extraction/README.md) → sources).
- **Dados que mudam com frequência** — não versione dados voláteis como seed.
- **Dados sensíveis/PII** — não comite (ver [security](../../26-security/README.md),
  [.gitignore](../../.gitignore)).

## Sources vs Seeds vs Models

| | Source | Seed | [Model](../02-models/README.md) |
| --- | --- | --- | --- |
| Origem | tabela raw já no warehouse | CSV no repositório | SELECT (transformação) |
| Quem carrega | ingestão externa | `dbt seed` | `dbt run` |
| Tamanho | qualquer | pequeno | derivado |
| Uso | ponto de entrada | lookup estático | transformação |

## Erros comuns

- Referenciar a tabela raw direto (sem `source()`) → perde lineage/desacoplamento.
- Usar seed para dados grandes/voláteis (deveria ser source).
- Comitar PII/dados sensíveis como seed.
- Não configurar `freshness` nas sources (não detecta upstream atrasado).

## Boas práticas

- Declare **todas** as tabelas brutas como sources; sempre `source()`/`ref()`.
- Configure `freshness` nas sources críticas; rode `dbt source freshness`.
- Seeds só para lookups pequenos, estáticos e não-sensíveis.
- Documente sources e seeds (vira docs/lineage).

## Relação com outros conceitos

- [Models](../02-models/README.md), [tests](../05-tests/README.md),
  [lineage](../07-documentation-lineage/README.md).
- [Ingestão](../../09-etl-elt/02-ingestion-extraction/README.md),
  [freshness](../../24-observability/06-data-freshness/README.md).

## Exercícios

1. Declare uma source `raw.pedidos` com `freshness` e referencie-a num model staging.
2. Rode `dbt source freshness` e explique o que ele detecta.
3. Crie um seed `mapa_regioes.csv` e use-o num join num model.
4. Dê um exemplo de dado que deve ser seed e outro que deve ser source.

## Referências

- Documentação do dbt — Sources, Source freshness, Seeds.
