# Snapshots

> 🔵 Analytics Platforms · Parte de [28 — dbt](../README.md)

## O que é

**Snapshots** são o mecanismo do dbt para implementar **[Slowly Changing Dimensions tipo 2
(SCD2)](../../07-data-modeling/10-slowly-changing-dimensions/README.md)** automaticamente: capturar e
**historizar** as mudanças de registros ao longo do tempo. A cada execução, o dbt compara o estado
atual da fonte com o último snapshot e registra as mudanças com colunas de validade.

## Por que existe / que problema resolve

Fontes operacionais ([OLTP](../../01-foundations/07-oltp-vs-olap/README.md)) guardam só o **estado
atual** — quando um cliente muda de região, o valor antigo é sobrescrito e **se perde**. Mas análises
históricas frequentemente precisam saber "como era na época" (ver
[SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md)). Snapshots capturam esse
histórico **antes** que ele desapareça.

> Importante: snapshot deve rodar **com frequência** sobre a fonte, pois só captura o estado nos
> momentos em que roda. Se a fonte muda duas vezes entre snapshots, o estado intermediário é perdido.
> Para captura completa, combine com [CDC](../../09-etl-elt/06-cdc/README.md).

## Como funciona

O dbt mantém uma tabela de snapshot com colunas extras de versionamento: `dbt_valid_from`,
`dbt_valid_to` (nulo = versão atual), `dbt_scd_id`, `dbt_updated_at`.

```sql
-- snapshots/snap_clientes.sql
{% snapshot snap_clientes %}
{{
  config(
    target_schema='snapshots',
    unique_key='cliente_id',
    strategy='timestamp',
    updated_at='updated_at'
  )
}}
select * from {{ source('raw', 'clientes') }}
{% endsnapshot %}
```

```bash
dbt snapshot
```

Resultado ao longo do tempo:

```text
cliente_id | regiao  | dbt_valid_from | dbt_valid_to
   C-7      | Sul     | 2020-01-01     | 2023-07-01     ← versão antiga (fechada)
   C-7      | Sudeste | 2023-07-01     | (null)         ← versão atual
```

## Estratégias de detecção de mudança

- **`timestamp`** — usa uma coluna `updated_at` confiável da fonte (muda a cada alteração). Mais
  eficiente; exige que a fonte mantenha esse campo corretamente.
- **`check`** — compara o valor de colunas específicas (`check_cols`) entre execuções; detecta mudança
  quando os valores diferem. Use quando não há `updated_at` confiável (mais custoso).

```sql
config(strategy='check', unique_key='cliente_id', check_cols=['regiao','segmento'])
```

## Usando o snapshot nos models

O snapshot vira uma fonte historizada; você constrói a dimensão SCD2 a partir dele:

```sql
-- dim_cliente com histórico
select
    {{ dbt_utils.generate_surrogate_key(['cliente_id','dbt_valid_from']) }} as cliente_sk,
    cliente_id, regiao, segmento,
    dbt_valid_from as valido_de,
    coalesce(dbt_valid_to, '9999-12-31') as valido_ate,
    dbt_valid_to is null as is_current
from {{ ref('snap_clientes') }}
```

A [surrogate key](../../07-data-modeling/09-surrogate-natural-keys/README.md) por hash de
`(cliente_id, valid_from)` dá uma chave única por versão — exatamente o que o SCD2 precisa.

## Cuidados

- **Frequência** — rode snapshot regularmente (ele só "vê" o estado nos momentos de execução).
  Mudanças entre execuções se perdem (combine com CDC se precisar de completude).
- **Idempotência** — `dbt snapshot` é seguro de reexecutar (não duplica versões).
- **Não mude a estratégia/`unique_key`** de um snapshot existente sem planejar (corrompe o
  histórico).
- **Deletes na fonte** — por padrão o snapshot não "fecha" registros deletados; há configs/estratégias
  para *hard deletes* (`invalidate_hard_deletes`).

## Snapshots vs fazer SCD2 na mão

Você *poderia* implementar SCD2 manualmente com `MERGE` + [window functions](../../05-sql/05-window-functions/README.md),
mas é trabalhoso e fácil de errar. Snapshots automatizam o padrão com as colunas de validade
gerenciadas — menos código, menos bugs. Para SCD2, **prefira snapshots**.

## Erros comuns

- Rodar snapshot raramente → perde histórico entre execuções.
- Usar `strategy='timestamp'` com um `updated_at` que a fonte não atualiza em todo update → perde
  mudanças.
- Mudar `unique_key`/estratégia de um snapshot já em uso.
- Esquecer de tratar deletes quando o histórico de remoções importa.

## Boas práticas

- Agende o `dbt snapshot` frequentemente (combine com CDC para completude).
- `timestamp` quando houver `updated_at` confiável; `check` caso contrário.
- Construa a dimensão SCD2 a partir do snapshot, com surrogate key por versão.
- Trate hard deletes conforme a necessidade de histórico.

## Relação com outros conceitos

- Implementa [SCD2](../../07-data-modeling/10-slowly-changing-dimensions/README.md) com
  [surrogate keys](../../07-data-modeling/09-surrogate-natural-keys/README.md).
- [Sources](../03-sources-seeds/README.md), [models](../02-models/README.md),
  [CDC](../../09-etl-elt/06-cdc/README.md).

## Exercícios

1. Crie um snapshot `timestamp` de uma tabela de clientes e rode-o duas vezes (com uma mudança no
   meio); inspecione `dbt_valid_from/to`.
2. Construa `dim_cliente` SCD2 a partir do snapshot, com surrogate key por versão.
3. Explique quando usar `check` em vez de `timestamp`.
4. Explique por que rodar snapshot com pouca frequência perde histórico.

## Referências

- Documentação do dbt — Snapshots.
- Kimball, R. — SCD (ver [modelagem/SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md)).
