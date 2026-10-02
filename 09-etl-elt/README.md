# 09 — ETL / ELT

> 🔵 Nível 3 — Pipelines · Pré: [05 — SQL](../05-sql/README.md),
> [07 — Modeling](../07-data-modeling/README.md),
> [08 — Formats](../08-data-formats/README.md) · Próximo:
> [10 — Data Pipelines](../10-data-pipelines/README.md)

ETL/ELT é o **trabalho central** da Engenharia de Dados: mover dados da origem ao destino,
transformando-os em algo confiável e útil. Este módulo cobre as etapas (extração,
transformação, carga) e os conceitos que separam um pipeline de brinquedo de um de
produção: cargas incrementais, [CDC](06-cdc/README.md), **idempotência**, *backfill*,
deduplicação, validação e tratamento de falhas.

## Por que importa

Quase todo valor de dados passa por um pipeline de ETL/ELT. Dominar idempotência,
incremental e falhas é o que torna seus pipelines **confiáveis** — reexecutáveis sem
corromper dados, resilientes a erros e corretos mesmo com dados tardios.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [ETL vs ELT](01-etl-vs-elt/README.md) | Transformar antes ou depois de carregar |
| 02 | [Ingestão e extração](02-ingestion-extraction/README.md) | Trazer dados das fontes |
| 03 | [Transformação](03-transformation/README.md) | Limpar, juntar, modelar |
| 04 | [Loading](04-loading/README.md) | Carregar no destino (append/upsert/overwrite) |
| 05 | [Full vs incremental](05-full-vs-incremental/README.md) | Recarregar tudo vs só o novo |
| 06 | [CDC](06-cdc/README.md) | Change Data Capture |
| 07 | [Idempotência e retries](07-idempotency-retries/README.md) | Reexecutar sem duplicar |
| 08 | [Backfill](08-backfill/README.md) | Reprocessar o histórico |
| 09 | [Deduplicação](09-deduplication/README.md) | Remover duplicatas |
| 10 | [Data validation](10-data-validation/README.md) | Validar antes de propagar |
| 11 | [Tratamento de falhas](11-handling-failures/README.md) | Falhar bem e recuperar |

## Dependências internas

```text
ETL vs ELT ─► Ingestão/extração ─► Transformação ─► Loading
                     │                                  │
            Full vs incremental ─► CDC                  │
                     │                                  ▼
            Idempotência/retries ◄───────────── Deduplicação
                     │
            Backfill · Data validation · Tratamento de falhas
```

## Checkpoint

- [ ] Escolher entre ETL e ELT e justificar.
- [ ] Projetar extração incremental (por watermark) e explicar quando usar full load.
- [ ] Explicar CDC e quando usá-lo em vez de batch.
- [ ] Tornar um pipeline **idempotente** (upsert/overwrite por partição + dedupe).
- [ ] Executar um *backfill* sem duplicar nem corromper dados.
- [ ] Adicionar validação de dados que impede dados ruins de propagarem.
- [ ] Projetar retries para erros transitórios e tratamento para permanentes.

## Referências do módulo

- Reis, J.; Housley, M. *Fundamentals of Data Engineering* — caps. 7–8.
- Kleppmann, M. *DDIA* — batch e stream (caps. 10–11).
- Documentação de dbt, Airbyte, Debezium.
