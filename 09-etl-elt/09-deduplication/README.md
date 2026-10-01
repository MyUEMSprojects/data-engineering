# Deduplicação

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

**Deduplicação** é remover registros **duplicados** — manter uma única versão por entidade.
Duplicatas são onipresentes em dados reais e, se não tratadas, inflam contagens e somas,
corrompendo métricas.

## De onde vêm as duplicatas

- **Retries/reprocessamento** sem [idempotência](../07-idempotency-retries/README.md).
- **[CDC](../06-cdc/README.md)/streaming** com entrega *at-least-once* (ver
  [delivery semantics](../../17-streaming/04-delivery-semantics/README.md)).
- **Fontes que reenviam** o mesmo registro (APIs, exports sobrepostos).
- **Joins com fan-out** (ver [joins](../../05-sql/03-joins/README.md)).
- **Backfill** sobrepondo janelas.
- **Dados de má qualidade** na origem (o mesmo cliente cadastrado 2x).

## Dois tipos de duplicata (distinção importante)

- **Duplicata exata** — linhas idênticas em tudo. Fácil: `DISTINCT`/`drop_duplicates`.
- **Duplicata lógica** — mesma entidade, versões diferentes (mesmo `id`, `updated_at`
  diferentes; ou mesma pessoa com grafias distintas). Exige definir **qual manter** e, às
  vezes, **casamento fuzzy** (entity resolution).

## Deduplicação exata

```sql
SELECT DISTINCT * FROM eventos;              -- SQL
```
```python
df.drop_duplicates()                          # pandas
df.unique()                                   # polars
```

## Deduplicação lógica: manter a versão certa (o padrão)

Use [window functions](../../05-sql/05-window-functions/README.md): particione pela **chave
da entidade**, ordene por um critério de recência, e mantenha a primeira.

```sql
WITH ranked AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) AS rn
  FROM staging_clientes
)
SELECT * FROM ranked WHERE rn = 1;            -- versão mais recente por id
```

```python
# polars
df.sort("updated_at").unique(subset=["id"], keep="last")
```

Decisões-chave: **qual é a chave** de unicidade? **qual critério** define "a versão a
manter" (mais recente? mais completa? prioridade de fonte)? Documente isso — é regra de
negócio.

## Deduplicação em streaming

Em streams (at-least-once), deduplica-se mantendo **estado** das chaves já vistas (numa
janela de tempo) ou via chaves idempotentes no destino. Ver
[stateful processing](../../17-streaming/05-stateful-processing/README.md) e
[idempotência](../07-idempotency-retries/README.md). "Exactly-once" prático = at-least-once +
dedupe idempotente.

## Prevenção > correção

Melhor que deduplicar depois é **não duplicar**:

- **[Idempotência](../07-idempotency-retries/README.md)** na carga (upsert por chave,
  overwrite por partição).
- **Chaves determinísticas** (hash dos atributos) que fazem a mesma linha colidir e ser
  substituída.
- **Constraints** `UNIQUE`/PK na origem OLTP (ver
  [constraints](../../05-sql/09-constraints/README.md)).

## Entity resolution (dedupe fuzzy)

Quando não há chave exata (ex.: "João Silva" vs "Joao da Silva", mesmo CPF com formatos
diferentes), é preciso **casar** registros por similaridade: normalizar (lowercase, remover
acentos/pontuação), comparar por distância (Levenshtein, trigram), e às vezes ML. É um
problema difícil — padronize na [transformação](../03-transformation/README.md) o máximo
possível antes de recorrer a fuzzy.

## Deduplicação e qualidade

Unicidade é uma dimensão de [data quality](../../12-data-quality/01-dimensions-of-quality/README.md).
Teste-a: um teste `unique` na chave (ver [dbt tests](../../28-dbt/05-tests/README.md)/
[validação](../10-data-validation/README.md)) pega duplicatas antes de propagarem.

## Erros comuns

- Somar/contar sem deduplicar → métricas infladas.
- `DISTINCT` para "consertar" um fan-out de join (conserte o join, não mascare).
- Deduplicar sem definir a chave correta (remove linhas legítimas ou mantém a versão
  errada).
- Esquecer dedupe em pipelines de streaming at-least-once.
- Fuzzy matching agressivo que funde entidades distintas.

## Boas práticas

- Previna com idempotência/chaves determinísticas; deduplique como rede de segurança.
- Use `ROW_NUMBER` por chave + critério de recência; documente a regra.
- Teste a unicidade da chave.
- Padronize antes de recorrer a casamento fuzzy.

## Relação com outros conceitos

- [Window functions](../../05-sql/05-window-functions/README.md),
  [idempotência](../07-idempotency-retries/README.md), [CDC](../06-cdc/README.md).
- [Data quality](../../12-data-quality/README.md),
  [transformação](../03-transformation/README.md).

## Exercícios

1. Deduplique uma staging de clientes mantendo o registro mais recente por `id`.
2. Explique a diferença entre duplicata exata e lógica, com exemplos.
3. Mostre como chaves determinísticas (hash) + upsert evitam duplicatas na origem.
4. Esboce uma estratégia de entity resolution para nomes com grafias diferentes.

## Referências

- Documentação de window functions (PostgreSQL) e dbt tests (`unique`).
- Kleppmann, M. *DDIA* — processamento exactly-once.
