# Delta Lake

> 🔵 Analytics Platforms · Parte de [15 — Lakehouse](../README.md)

## O que é

**Delta Lake** é um *table format* open source (criado pela Databricks) que adiciona
[ACID](../03-acid-on-object-storage/README.md), time travel, schema enforcement/evolution e upserts
sobre arquivos [Parquet](../../08-data-formats/04-parquet/README.md) em
[object storage](../../14-data-lake/02-object-storage/README.md). É um dos três grandes formatos de
lakehouse, junto de [Iceberg](../05-apache-iceberg/README.md) e [Hudi](../06-apache-hudi/README.md).

## Como funciona: o transaction log (`_delta_log`)

Uma tabela Delta é: arquivos Parquet + um diretório **`_delta_log/`** com um log de commits em
JSON (e checkpoints em Parquet periódicos).

```text
tabela/
├── _delta_log/
│   ├── 00000000000000000000.json   (commit 0: adiciona arquivos A, B)
│   ├── 00000000000000000001.json   (commit 1: remove A, adiciona C — ex.: um update)
│   └── _last_checkpoint
└── part-*.parquet
```

Cada commit registra *add/remove* de arquivos + metadados (schema, estatísticas). A tabela na versão
N = soma dos commits até N. O commit é **atômico** (ver
[ACID sobre object storage](../03-acid-on-object-storage/README.md)).

## Capacidades

| Recurso | Como |
| --- | --- |
| **ACID** | commits atômicos no log, snapshot isolation |
| **MERGE/UPDATE/DELETE** | reescreve arquivos afetados + commit (SCD, CDC, LGPD) |
| **Time travel** | `VERSION AS OF` / `TIMESTAMP AS OF` |
| **Schema enforcement** | barra escrita com schema incompatível |
| **Schema evolution** | `mergeSchema` para adicionar colunas |
| **OPTIMIZE + Z-ORDER** | compaction + data skipping por colunas |
| **VACUUM** | remove arquivos órfãos/antigos (limpa time travel) |
| **Change Data Feed** | expõe as mudanças da tabela (CDC de saída) |

## Exemplos (Spark/SQL)

```python
df.write.format("delta").mode("overwrite").save("s3://bucket/lake/vendas")

# upsert (MERGE) — SCD/CDC
from delta.tables import DeltaTable
dt = DeltaTable.forPath(spark, "s3://bucket/lake/vendas")
(dt.alias("t").merge(updates.alias("s"), "t.id = s.id")
   .whenMatchedUpdateAll()
   .whenNotMatchedInsertAll()
   .execute())
```

```sql
-- time travel
SELECT * FROM delta.`s3://bucket/lake/vendas` VERSION AS OF 5;
-- manutenção
OPTIMIZE vendas ZORDER BY (uf);
VACUUM vendas RETAIN 168 HOURS;
```

## Pontos fortes

- **Integração profunda com Spark/Databricks** (maduro, performático nesse ecossistema).
- **Change Data Feed** — fácil de consumir mudanças a jusante.
- Simplicidade de uso no stack Spark; **Delta Lake é open source** (protocolo aberto) e lido por
  várias engines (via delta-rs, Trino, etc.), além do conector Uniform/Iceberg-compat.

## Trade-offs / limitações

- Historicamente **muito acoplado ao Spark/Databricks** (fora dele, o suporte amadurece via
  `delta-rs`, conectores) — menos "engine-neutro" que o [Iceberg](../05-apache-iceberg/README.md).
- O commit atômico em S3 puro (sem catálogo/serviço) exige cuidado com concorrência de múltiplos
  writers (gerenciado no Databricks).
- Gerenciar `VACUUM`/retenção (time travel acumula storage).

## Quando usar

- Você já usa **Spark/Databricks** (encaixe natural, melhor experiência).
- Quer ACID/time travel/MERGE sobre o lake com pouco atrito no ecossistema Spark.
- Precisa de Change Data Feed para propagar mudanças.

## Delta vs Iceberg vs Hudi (resumo)

| | Delta | Iceberg | Hudi |
| --- | --- | --- | --- |
| Origem | Databricks | Netflix/Apple (Apache) | Uber (Apache) |
| Engine-neutro | bom (melhorando) | **excelente** | bom |
| Forte em | ecossistema Spark/Databricks | neutralidade, grandes tabelas | upserts/CDC incremental |

Detalhes em [Iceberg](../05-apache-iceberg/README.md) e [Hudi](../06-apache-hudi/README.md). Não há
vencedor universal — escolha pelo ecossistema e necessidade.

## Erros comuns

- Mexer nos arquivos Parquet "por fora" do Delta (corrompe o log).
- Esquecer `OPTIMIZE` (small files) e `VACUUM` (storage/time travel inflado).
- `VACUUM` com retenção curta demais quebrando time travel/leituras em andamento.
- Assumir que só funciona no Databricks (é open source).

## Boas práticas

- Escreva/leia sempre via Delta; nunca manipule os Parquet diretamente.
- Agende `OPTIMIZE`/Z-ORDER e `VACUUM` com retenção adequada.
- Use `MERGE` para SCD/CDC; Change Data Feed para propagar mudanças.
- Gerencie schema evolution explicitamente (`mergeSchema` consciente).

## Relação com outros conceitos

- [ACID sobre object storage](../03-acid-on-object-storage/README.md),
  [Parquet](../../08-data-formats/04-parquet/README.md),
  [small files/compaction](../../14-data-lake/06-small-files-compaction/README.md).
- [Spark](../../16-distributed-processing/README.md), [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md),
  [CDC](../../09-etl-elt/06-cdc/README.md).

## Exercícios

1. Crie uma tabela Delta, faça um `MERGE` (upsert) e inspecione o `_delta_log`.
2. Use time travel para ler uma versão anterior após um update.
3. Rode `OPTIMIZE ZORDER BY` e explique o efeito no data skipping.
4. Explique o que o `VACUUM` faz e o risco de uma retenção curta demais.

## Referências

- Documentação oficial do Delta Lake (delta.io) e protocolo do transaction log.
