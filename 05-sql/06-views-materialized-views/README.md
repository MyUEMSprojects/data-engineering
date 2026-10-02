# Views e materialized views

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

- **View** — uma consulta salva com um nome; comporta-se como uma tabela virtual. É
  recalculada **toda vez** que você a consulta (não armazena dados).
- **Materialized view** — uma view cujo resultado é **armazenado em disco**
  (pré-computado). Consultas são rápidas, mas os dados ficam "parados" até um
  `REFRESH`.

## Por que existem

- **Views** — abstração e reuso: escondem complexidade (joins, regras de negócio),
  dão uma interface estável a consumidores e controlam acesso (expor só certas
  colunas). Não melhoram performance por si.
- **Materialized views** — performance: pré-computam agregações/joins caros para
  consultas analíticas frequentes, trocando frescor por velocidade.

## Views

```sql
CREATE VIEW vw_pedidos_pagos AS
SELECT p.id, c.nome, p.valor, p.criado_em
FROM pedidos p
JOIN clientes c ON c.id = p.cliente_id
WHERE p.status = 'pago';

SELECT * FROM vw_pedidos_pagos WHERE valor > 100;   -- usa como tabela
```

- A query da view roda a cada consulta; o otimizador a combina com seus filtros.
- `CREATE OR REPLACE VIEW` atualiza a definição.
- Views **updatable** (simples) permitem `INSERT/UPDATE`; com joins/agregação,
  geralmente são só leitura (ou use `INSTEAD OF triggers`).

Casos de uso em DE:

- Camada semântica estável sobre tabelas físicas (consumidores não dependem do schema
  interno).
- Mascarar colunas sensíveis (expor view sem PII — ver
  [data masking](../../26-security/07-data-masking-pii/README.md)).
- Padronizar regras de negócio num lugar só (DRY).

## Materialized views

```sql
CREATE MATERIALIZED VIEW mv_receita_diaria AS
SELECT criado_em::date AS dia, uf, SUM(valor) AS receita
FROM pedidos
GROUP BY 1, 2;

-- consultar é rápido (lê o resultado armazenado)
SELECT * FROM mv_receita_diaria WHERE dia = '2024-01-01';

-- atualizar (recomputa)
REFRESH MATERIALIZED VIEW mv_receita_diaria;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_receita_diaria;  -- sem travar leituras (requer índice único)
```

Trade-off central: **frescor vs performance**. O dado da MV tem a idade do último
`REFRESH`. Você agenda o refresh ([cron](../../02-linux-shell-environment/06-cron/README.md)/
[orquestrador](../../11-orchestration/README.md)) conforme a tolerância a defasagem.

## View vs Materialized view vs Tabela (ETL)

| | View | Materialized view | Tabela (via ETL/dbt) |
| --- | --- | --- | --- |
| Armazena dados | Não | Sim | Sim |
| Frescor | Sempre atual | Até o último refresh | Até o último run |
| Custo de leitura | Recalcula | Baixo | Baixo |
| Controle/transform. | Limitado | Médio | Total (incremental, testes) |

Em pipelines analíticos, muitas vezes a resposta não é view nem MV, e sim **uma
tabela construída por [dbt](../../28-dbt/README.md)/ETL** — com controle de
incremental, testes e lineage. MVs são ótimas para pré-agregações simples; tabelas
materializadas por dbt, para transformações complexas e versionadas.

## Diferenças entre bancos

- **Postgres** — MV com `REFRESH` manual/agendado (não auto-atualiza).
- **BigQuery** — materialized views com atualização incremental automática (limitada a
  certos padrões).
- **Snowflake** — materialized views auto-mantidas (com custo) e *dynamic tables*.
- dbt oferece *materializations* (`view`, `table`, `incremental`,
  `materialized_view`) como abstração portável.

## Performance e indexação

- Views herdam a performance da query subjacente — indexe as **tabelas base**.
- Materialized views podem receber **índices próprios** (consultadas como tabelas).

## Erros comuns

- Esperar que uma view comum melhore performance (não melhora).
- Esquecer de agendar `REFRESH` → MV com dados velhos silenciosamente.
- Empilhar views sobre views sobre views → planos monstruosos e lentos.
- Usar MV onde um pipeline incremental seria mais correto (dados tardios, SCD).

## Boas práticas

- Views para abstração/segurança; MVs para pré-computar agregados quentes.
- Documente a latência esperada de cada MV e automatize o refresh.
- Para transformações complexas/versionadas, prefira tabelas via dbt/ETL.
- Evite aninhamento profundo de views.

## Relação com outros conceitos

- Abstração estável conecta a [data contracts](../../29-data-contracts/README.md).
- Alternativa gerenciada: [dbt materializations](../../28-dbt/02-models/README.md).
- Pré-computação ⇄ [otimização](../11-optimization/README.md) e
  [warehouse](../../13-data-warehouse/README.md).

## Exercícios

1. Crie uma view que esconde PII de uma tabela de clientes e exponha só o necessário.
2. Crie uma materialized view de receita diária por UF, indexe-a e agende um refresh.
3. Compare o tempo de consulta entre a view "crua" e a MV.
4. Explique quando você escolheria uma tabela dbt incremental em vez de uma MV.

## Referências

- Documentação do PostgreSQL — "CREATE VIEW", "CREATE MATERIALIZED VIEW".
- Documentação de materialized views de BigQuery/Snowflake.
