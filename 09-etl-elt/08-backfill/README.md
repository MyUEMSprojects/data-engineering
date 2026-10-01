# Backfill

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

**Backfill** é reprocessar dados **históricos** — preencher o passado. Acontece quando você:

- Cria um pipeline novo e precisa carregar todo o histórico (não só "de agora em diante").
- Corrige um **bug** na transformação e precisa recalcular dados já processados.
- Adiciona uma **nova coluna/métrica** e quer aplicá-la retroativamente.
- Teve uma **falha/lacuna** e precisa reprocessar o período afetado.

## Por que é um tópico à parte

Backfill parece "só rodar o pipeline para datas antigas", mas tem armadilhas próprias:
volume (reprocessar anos de dados), custo, duplicação (se não for idempotente), consistência
(dados que mudaram desde então) e impacto nos consumidores. Fazer backfill errado é uma das
formas mais fáceis de **corromper um warehouse**.

## Pré-requisito absoluto: idempotência

Backfill **só é seguro** se o pipeline for [idempotente](../07-idempotency-retries/README.md).
Reprocessar o dia 2024-01-15 deve **substituir** os dados daquele dia, não **adicionar** por
cima. Sem isso, backfill duplica tudo. Use **overwrite por partição** ou **upsert** (ver
[loading](../04-loading/README.md)).

```sql
-- reprocessar uma data substitui só aquela partição
DELETE FROM fato_vendas WHERE dt = :data;
INSERT INTO fato_vendas SELECT ... WHERE dt = :data;
```

## Pré-requisito: parametrização por data

O pipeline deve receber a **data lógica** como parâmetro (não usar `now()` embutido), para
poder rodar "como se fosse" qualquer dia do passado. Em orquestradores isso é a *execution
date*/*logical date* (ver [scheduling](../../10-data-pipelines/03-scheduling/README.md)).

```python
def run(logical_date: str): ...   # processa a partição daquela data
```

## Estratégias de execução

### Por partição, em paralelo

Divida o período em partições (geralmente por dia) e processe-as — frequentemente em
**paralelo** (respeitando limites de recursos). Orquestradores oferecem *backfill* nativo
(Airflow: `airflow dags backfill`; Dagster: *backfills* de partições).

```text
backfill de 2023-01-01 a 2023-12-31  →  365 execuções (uma por dia), paralelizadas
```

### Em lotes com controle

Para volumes enormes, processe em lotes (ex.: mês a mês), monitorando custo e sem saturar o
warehouse/cluster.

## Preservar o raw ajuda muito

Se você guardou a camada [raw/bronze](../../14-data-lake/03-medallion-architecture/README.md),
o backfill de uma correção de transformação é **reprocessar o raw** — sem re-extrair da
fonte (que pode não ter mais o histórico). Esse é um dos maiores argumentos a favor de
preservar o bruto (ver [ETL vs ELT](../01-etl-vs-elt/README.md)).

## Cuidados importantes

- **Custo e recursos** — reprocessar anos pode custar caro (compute/warehouse) e saturar o
  cluster. Estime antes; limite o paralelismo.
- **Dados que mudaram desde então** — se a fonte foi atualizada, o backfill de hoje pode
  produzir resultados **diferentes** dos originais. Decida: reproduzir o estado da época
  (precisa de snapshots/raw versionado) ou aceitar o estado atual.
- **Impacto nos consumidores** — backfill muda números em dashboards/modelos. Comunique;
  considere fazer em staging e trocar.
- **Ordem de dependências** — backfille as tabelas na ordem correta do
  [DAG](../../10-data-pipelines/02-dags-dependencies/README.md) (dimensões antes de fatos).
- **SCD** — backfill de dimensões [SCD2](../../07-data-modeling/10-slowly-changing-dimensions/README.md)
  é delicado (reconstruir a linha do tempo de versões).

## Backfill em dbt

[dbt incremental](../../28-dbt/08-incremental-models/README.md): para backfill, roda-se com
`--full-refresh` (recria tudo) ou filtra-se o período e reprocessa por partição. Modelos
idempotentes tornam isso seguro.

## Fluxo recomendado

```text
1. Garanta idempotência + parametrização por data.
2. Estime volume/custo; defina janela e paralelismo.
3. (Opcional) rode em staging e valide amostras.
4. Backfille por partição, na ordem de dependências.
5. Valide (contagens, testes) e comunique os consumidores.
```

## Erros comuns

- Backfill sem idempotência → duplicação massiva.
- `now()` embutido → não dá para reprocessar o passado corretamente.
- Reprocessar tudo de uma vez e saturar/estourar custo.
- Ignorar que a fonte mudou (resultado difere do original sem avisar).
- Backfillar fatos antes das dimensões (FKs quebradas).

## Boas práticas

- Idempotência + parametrização por data como pré-requisito.
- Preserve o raw para reprocessar sem re-extrair.
- Backfille por partição, com paralelismo controlado e na ordem do DAG.
- Valide o resultado e comunique mudanças aos consumidores.

## Relação com outros conceitos

- Exige [idempotência](../07-idempotency-retries/README.md) e
  [loading](../04-loading/README.md) por partição.
- [Scheduling/execution date](../../10-data-pipelines/03-scheduling/README.md),
  [dependências/DAG](../../10-data-pipelines/02-dags-dependencies/README.md).
- [dbt incremental](../../28-dbt/08-incremental-models/README.md),
  [raw/bronze](../../14-data-lake/03-medallion-architecture/README.md).

## Exercícios

1. Torne um pipeline parametrizável por data lógica e faça backfill de 3 dias sem duplicar.
2. Explique como preservar o raw facilita o backfill de uma correção de transformação.
3. Descreva os cuidados ao backfillar quando a fonte já mudou desde o período original.
4. Planeje o backfill de um ano de fatos: ordem, paralelismo, custo e validação.

## Referências

- Documentação de backfill do Airflow e do Dagster.
- dbt — `--full-refresh` e incremental.
- Reis & Housley, *Fundamentals of Data Engineering*.
