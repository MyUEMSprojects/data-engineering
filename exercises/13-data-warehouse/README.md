# Exercícios — Módulo 13: Data Warehouse

Teoria em [13-data-warehouse](../../13-data-warehouse/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Por que colunar?

Em um warehouse colunar, por que `SELECT *` é um anti-padrão e `SELECT col1, col2` é barato?

<details><summary>Gabarito</summary>

Cada coluna fica em armazenamento separado: ler 2 de 200 colunas lê ~1% dos dados. `SELECT *` lê **todas**, multiplicando I/O e (em engines cobrados por bytes lidos, como BigQuery) o **custo**. Ver [armazenamento colunar](../../13-data-warehouse/02-columnar-storage/README.md).
</details>

## 2. 🟢 Conceitual — Partição × cluster

Qual a diferença entre **particionar** e **clusterizar** uma tabela de eventos e que filtro se beneficia de cada um?

<details><summary>Gabarito</summary>

**Partição** divide fisicamente por uma coluna de baixa cardinalidade (tipicamente data) — filtro por data **pula partições**. **Cluster** ordena/agrupa dentro das partições por colunas de uso frequente (ex.: `customer_id`) — melhora filtros/joins por essas colunas. Combine: partição por data + cluster por chave. Ver [particionamento](../../13-data-warehouse/03-partitioning-clustering/README.md).
</details>

## 3. 🔵 SQL — Reescrever para custar menos

Esta consulta varre 5 TB: `SELECT * FROM events WHERE DATE(event_ts) = '2024-03-01'` (tabela particionada por `event_ts`). Reescreva e explique.

<details><summary>Gabarito</summary>

```sql
SELECT user_id, event_type             -- só as colunas necessárias
FROM events
WHERE event_ts >= TIMESTAMP '2024-03-01' AND event_ts < TIMESTAMP '2024-03-02';   -- filtro DIRETO na coluna de partição
```

`DATE(event_ts) = ...` aplica **função** na coluna e frequentemente impede a **poda de partições**. Use intervalo semiaberto sobre a coluna crua e selecione só o necessário.
</details>

## 4. 🔵 Debugging — A dimensão com dados demais

Um join `fct_sales JOIN dim_product` fica lento: `dim_product` tem 80 milhões de linhas porque guarda uma linha **por SKU por dia**. O que está errado na modelagem?

<details><summary>Gabarito</summary>

Atributos que mudam raramente estão sendo **snapshotados todo dia** (equivalente a SCD2 diário). Dimensões devem ter uma linha por **versão real**; guarde só quando o atributo mudar (SCD2 com `valid_from/valid_to`), e mova métricas voláteis (estoque, preço do dia) para uma **tabela fato** (*periodic snapshot*). Ver [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md).
</details>

## 5. 🟣 Arquitetura — Custo no BigQuery × Snowflake × Redshift

Compare o **modelo de custo** dos três e escolha para: (a) analistas ad hoc com carga imprevisível; (b) carga constante e previsível 24/7; (c) time já 100% AWS.

<details><summary>Gabarito (um caminho)</summary>

**BigQuery:** *on-demand* por **bytes lidos** (ou *slots* reservados) — ótimo para carga esporádica, perigoso sem controle de partição/cluster. **Snowflake:** computação por **warehouse/segundo** separada do armazenamento — bom para isolar cargas e escalar. **Redshift:** *provisioned* (nós) ou *serverless* — vantajoso com carga constante e integração AWS.
(a) BigQuery on-demand ou Snowflake; (b) capacidade reservada (slots/Redshift provisioned); (c) Redshift (ou Snowflake na AWS). Ver [BigQuery](../../13-data-warehouse/05-bigquery/README.md), [Snowflake](../../13-data-warehouse/06-snowflake/README.md), [Redshift](../../13-data-warehouse/07-redshift/README.md).
</details>

## 6. 🟣 Implementação — Tabela agregada incremental

Projete (SQL + regra de atualização) uma tabela `daily_revenue` que se atualiza **incrementalmente** com pedidos atrasados de até 3 dias, sem recalcular o histórico inteiro.

<details><summary>Gabarito</summary>

```sql
-- janela de reprocessamento = últimos 3 dias da data lógica :ds
DELETE FROM daily_revenue WHERE order_date >= :ds - INTERVAL '3 days' AND order_date <= :ds;
INSERT INTO daily_revenue
SELECT order_date, country, SUM(amount) AS revenue, COUNT(*) AS orders
FROM orders
WHERE order_date >= :ds - INTERVAL '3 days' AND order_date <= :ds AND status <> 'canceled'
GROUP BY 1, 2;
```

É o padrão *delete+insert com **lookback***: pedidos atrasados corrigem os dias recentes; o histórico antigo fica intocado. Em dbt: `incremental` com `delete+insert` e `lookback`. Ver [incremental](../../28-dbt/08-incremental-models/README.md).
</details>
