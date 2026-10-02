# Exercícios — Módulo 09: ETL / ELT

Teoria em [09-etl-elt](../../09-etl-elt/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — ETL ou ELT?

Escolha ETL ou ELT para: (a) carregar dados com PII que **não podem** chegar ao warehouse sem mascaramento; (b) warehouse elástico (BigQuery/Snowflake) e analistas que escrevem SQL; (c) fonte legada que só entrega arquivos pequenos e o destino é um banco de poucos recursos.

<details><summary>Gabarito</summary>

(a) **ETL** — transformar (mascarar) **antes** de carregar. (b) **ELT** — carregue o bruto e transforme com SQL/dbt dentro do warehouse. (c) **ETL** — o destino fraco não deve pagar o custo da transformação. Ver [ETL vs ELT](../../09-etl-elt/01-etl-vs-elt/README.md).
</details>

## 2. 🟢 Conceitual — Carga completa × incremental

Quando usar *full load* em vez de incremental? Que dois mecanismos permitem detectar o que mudou?

<details><summary>Gabarito</summary>

*Full* quando a tabela é **pequena**, não há coluna confiável de mudança ou é preciso detectar **deleções**. Incremental via **watermark** (`updated_at > último`) ou **CDC** (log do banco, captura inclusive deletes). Cuidado com `updated_at` não confiável e com atraso de commit. Ver [full vs incremental](../../09-etl-elt/05-full-vs-incremental/README.md).
</details>

## 3. 🔵 Implementação — Upsert idempotente

Escreva o `INSERT ... ON CONFLICT` do PostgreSQL que carrega pedidos de modo **idempotente** e **não regride** um registro para uma versão mais antiga (`updated_at`).

<details><summary>Gabarito</summary>

```sql
INSERT INTO orders (order_id, status, amount, updated_at)
VALUES (%(order_id)s, %(status)s, %(amount)s, %(updated_at)s)
ON CONFLICT (order_id) DO UPDATE
   SET status = EXCLUDED.status, amount = EXCLUDED.amount, updated_at = EXCLUDED.updated_at
 WHERE EXCLUDED.updated_at >= orders.updated_at;
```

Reexecutar o mesmo lote não duplica e um evento atrasado não sobrescreve um mais novo. Implementado no [Projeto 01](../../projects/01-basic-etl/README.md). Ver [idempotência](../../09-etl-elt/07-idempotency-retries/README.md).
</details>

## 4. 🔵 Debugging — O backfill que duplicou

Um job diário faz `INSERT INTO fact SELECT ... WHERE dt = :ds`. Ao reprocessar 5 dias, a receita desses dias **dobrou**. Corrija mantendo o job reexecutável.

<details><summary>Gabarito</summary>

O job é **append-only**: reexecutar soma de novo. Torne-o idempotente por partição: numa transação, `DELETE FROM fact WHERE dt = :ds; INSERT ... WHERE dt = :ds;` — ou use `MERGE`/`INSERT ... ON CONFLICT` com chave natural, ou **sobrescrita de partição** (`INSERT OVERWRITE`/`replaceWhere`). Backfill = rodar o **mesmo** job para várias datas lógicas. Ver [backfill](../../09-etl-elt/08-backfill/README.md).
</details>

## 5. 🟣 Implementação — Deduplicação determinística

Uma tabela `events(event_id, user_id, payload, ingested_at)` recebe entregas *at-least-once*. Escreva a consulta que mantém **uma linha por `event_id`** (a primeira ingerida) e explique por que `SELECT DISTINCT *` não resolve.

<details><summary>Gabarito</summary>

```sql
SELECT * EXCLUDE (rn) FROM (
  SELECT e.*, ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ingested_at) AS rn   -- acrescente um desempate estável se houver empate
  FROM events e
) t WHERE rn = 1;
```

(`EXCLUDE (rn)` é DuckDB; BigQuery usa `EXCEPT (rn)`; em PostgreSQL liste as colunas. Verificado no DuckDB.) `DISTINCT *` só remove linhas **idênticas em todas as colunas** — duplicatas reentregues têm `ingested_at` diferente e passam. A chave de negócio (`event_id`) + critério de desempate é que define "duplicado". Ver [deduplicação](../../09-etl-elt/09-deduplication/README.md).
</details>

## 6. 🟣 Arquitetura — Quando a fonte cai no meio

Um pipeline extrai de uma API paginada (10.000 páginas) e a fonte cai na página 6.200. Projete a extração para **retomar** de onde parou sem duplicar nem perder, e diga o que registrar para auditoria.

<details><summary>Gabarito</summary>

Persistir um **checkpoint** (cursor/última página confirmada) **junto** com os dados gravados (mesma transação ou escrita atômica por página, nome determinístico). Ao reiniciar, retomar do checkpoint; páginas reprocessadas sobrescrevem o mesmo arquivo/chave (idempotência). Retry com backoff para erros transitórios; falha permanente → alerta. Auditar: `run_id`, cursor inicial/final, contagem por página, hashes, horário e erros. Ver [checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md) e [falhas](../../09-etl-elt/11-handling-failures/README.md).
</details>
