# Loading

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

**Loading** é o "L" do ETL/ELT: gravar os dados no **destino** (warehouse, lake, banco).
Parece trivial, mas a **estratégia de escrita** determina a idempotência, a corretude e a
performance de todo o pipeline.

## As estratégias de escrita

### Append (anexar)

Adiciona novas linhas sem tocar nas existentes.

```sql
INSERT INTO fato_vendas SELECT * FROM novas_vendas;
```

- **Bom para**: fatos/eventos imutáveis (cada evento é uma linha nova).
- **Risco**: se reexecutar, **duplica** (não é idempotente por si só) — combine com
  partições determinísticas ou dedupe.

### Overwrite (sobrescrever)

Substitui dados existentes — total ou por partição.

```sql
-- overwrite por partição (idempotente!)
DELETE FROM fato_vendas WHERE dt = '2024-01-15';
INSERT INTO fato_vendas SELECT * FROM vendas WHERE dt = '2024-01-15';
```

- **Overwrite por partição** é o padrão idempotente favorito: reprocessar um dia apaga e
  recria **só aquele dia**. Ver [idempotência](../07-idempotency-retries/README.md).
- Overwrite **total** só para tabelas pequenas (dimensões, lookups).

### Upsert / Merge (atualizar ou inserir)

Insere novos e atualiza existentes pela chave — a base de cargas incrementais e
[SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md).

```sql
MERGE INTO dim_cliente d
USING staging_cliente s ON d.cliente_id = s.cliente_id
WHEN MATCHED THEN UPDATE SET nome = s.nome, uf = s.uf, updated_at = s.updated_at
WHEN NOT MATCHED THEN INSERT (cliente_id, nome, uf) VALUES (s.cliente_id, s.nome, s.uf);
```

- **Bom para**: dimensões, tabelas com estado mutável, cargas incrementais com updates.
- **Idempotente por natureza** (reexecutar com os mesmos dados dá o mesmo estado).
- Dialetos: `MERGE` (padrão/Snowflake/BigQuery), `INSERT ... ON CONFLICT` (Postgres),
  `INSERT ... ON DUPLICATE KEY UPDATE` (MySQL).

## Escolhendo a estratégia

```text
dados imutáveis (eventos)        → append (+ partição determinística p/ idempotência)
reprocessar por janela/dia       → overwrite por partição ✅
estado mutável por chave         → upsert/merge
tabela pequena de referência     → overwrite total
```

## Carga em massa (bulk load)

`INSERT` linha a linha é lentíssimo. Use carregadores em massa:

- Postgres: `COPY`/`\copy`.
- MySQL: `LOAD DATA`.
- Warehouses: `COPY INTO` (Snowflake), `bq load`/`LOAD DATA` (BigQuery), `COPY` (Redshift) —
  lendo arquivos [Parquet](../../08-data-formats/04-parquet/README.md)/CSV de
  [object storage](../../19-cloud/02-object-storage/README.md).
- Spark/dbt: escrevem arquivos/tabelas diretamente.

## Escrita atômica (all-or-nothing)

O destino nunca deve ficar num estado parcial se a carga falhar no meio:

- Em arquivos: escreva em **temporário** e `mv`/*rename* atômico (ver
  [stdlib/atomic](../../04-python-for-data-engineering/05-stdlib-for-de/README.md)).
- Em bancos: envolva em **[transação](../../05-sql/08-transactions-isolation/README.md)**
  (carrega numa staging e faz swap/merge no commit).
- Em lake: [lakehouse](../../15-lakehouse/README.md) (Delta/Iceberg) dá **commits
  atômicos** sobre object storage.
- Padrão **staging + swap**: carrega numa tabela temporária, valida, e troca
  atomicamente pela de produção.

## Particionamento no destino

Grave particionado (por data/chave) para habilitar overwrite por partição, *pruning* e
retenção fácil (ver [partitioning](../../14-data-lake/05-partitioning/README.md)). Evite o
[small files problem](../../14-data-lake/06-small-files-compaction/README.md) (muitos
arquivos minúsculos).

## Loading e idempotência (o elo)

A carga é **o ponto** onde a idempotência é ganha ou perdida. Prefira estratégias
idempotentes (overwrite por partição, upsert) para que retries/backfill não corrompam.
Append puro exige cuidado extra (partição determinística + dedupe). Ver
[idempotência](../07-idempotency-retries/README.md).

## Erros comuns

- Append sem controle → duplicação em reexecução.
- `INSERT` linha a linha para volume grande → lentíssimo (use bulk load).
- Carga não atômica → estado parcial em falha.
- `DELETE`+`INSERT` sem transação → janela de dados faltando/inconsistentes.
- Over-partitioning no destino (small files).

## Boas práticas

- Escolha a estratégia pela natureza do dado (append/overwrite-partição/upsert).
- Bulk load a partir de arquivos colunares; carga atômica (staging+swap/transação).
- Particione o destino; mantenha a carga idempotente.
- Registre contagens carregadas (observabilidade).

## Relação com outros conceitos

- [Idempotência](../07-idempotency-retries/README.md),
  [full vs incremental](../05-full-vs-incremental/README.md),
  [dedupe](../09-deduplication/README.md).
- [Transações](../../05-sql/08-transactions-isolation/README.md),
  [lakehouse ACID](../../15-lakehouse/03-acid-on-object-storage/README.md).
- [SCD via merge](../../07-data-modeling/10-slowly-changing-dimensions/README.md).

## Exercícios

1. Implemente overwrite por partição para reprocessar um único dia sem afetar os demais.
2. Escreva um `MERGE`/upsert idempotente para uma dimensão de clientes.
3. Descreva o padrão staging + swap atômico e por que ele evita estado parcial.
4. Explique por que append puro não é idempotente e como torná-lo seguro.

## Referências

- Documentação de `MERGE`/`COPY` (Postgres, Snowflake, BigQuery, Redshift).
- dbt — materializations (`incremental`, estratégias de merge).
- Reis & Housley, *Fundamentals of Data Engineering*.
