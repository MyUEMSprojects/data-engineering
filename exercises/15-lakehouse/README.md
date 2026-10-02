# Exercícios — Módulo 15: Lakehouse

Teoria em [15-lakehouse](../../15-lakehouse/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — O que o lakehouse acrescenta

Que **três** capacidades um formato de tabela (Delta/Iceberg/Hudi) acrescenta a "arquivos Parquet numa pasta"?

<details><summary>Gabarito</summary>

(1) **ACID** (transações sobre objetos imutáveis, via log/manifestos); (2) **Schema enforcement/evolution**; (3) **Time travel** e operações como `MERGE`, `UPDATE`, `DELETE`. Também: *compaction*/`OPTIMIZE`, estatísticas para *data skipping*. Ver [ACID no object storage](../../15-lakehouse/03-acid-on-object-storage/README.md).
</details>

## 2. 🟢 Conceitual — Como o ACID funciona sem banco?

Em linhas gerais, como o Delta Lake garante que um leitor não veja uma escrita pela metade?

<details><summary>Gabarito</summary>

Os dados vão para arquivos Parquet **imutáveis**; a "verdade" é um **log de transações** (`_delta_log/`) de commits atômicos que listam arquivos adicionados/removidos. Leitores montam a visão a partir do log; um commit só existe quando o arquivo JSON do log é criado (operação atômica). Concorrência: *optimistic concurrency control* com detecção de conflito. Ver [Delta](../../15-lakehouse/04-delta-lake/README.md).
</details>

## 3. 🔵 Implementação — MERGE que não regride

Escreva (SQL Delta/Spark) o `MERGE` que atualiza pedidos **somente se** o evento é mais novo e insere os inexistentes.

<details><summary>Gabarito</summary>

```sql
MERGE INTO silver.orders t
USING staging.orders s
ON t.order_id = s.order_id
WHEN MATCHED AND s.updated_at > t.updated_at THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

Reexecutar o mesmo lote não altera os dados (predicado estrito `>`). Mesma lógica do [Projeto 10](../../projects/10-capstone/README.md) em Python (`deltalake`).
</details>

## 4. 🔵 Debugging — "Voltei no tempo e sumiu"

Após `VACUUM` com retenção de 0 horas, `SELECT ... VERSION AS OF 3` falha com arquivo não encontrado. Por quê e qual a política segura?

<details><summary>Gabarito</summary>

`VACUUM` **apaga fisicamente** os arquivos que o log marcou como removidos e que já passaram da retenção; versões antigas dependiam deles. Mantenha retenção ≥ **7 dias** (padrão), maior que o job mais longo e a janela de *time travel* necessária; nunca zere sem entender leitores concorrentes. Ver [lakehouse](../../15-lakehouse/README.md).
</details>

## 5. 🟣 Arquitetura — Delta × Iceberg × Hudi

Escolha o formato para: (a) ecossistema Databricks/Spark; (b) multi-engine (Trino, Flink, Spark, Snowflake) com *partition evolution*; (c) *upserts* de alta frequência vindos de CDC. Justifique.

<details><summary>Gabarito (um caminho)</summary>

(a) **Delta** — integração nativa. (b) **Iceberg** — especificação aberta, amplo suporte de engines e evolução de partição escondida. (c) **Hudi** — projetado para *upserts/incremental pulls* (Merge-on-Read). Na prática, a escolha segue o **ecossistema** que você já opera; conversores (UniForm/XTable) reduzem o lock-in. Ver [Iceberg](../../15-lakehouse/05-apache-iceberg/README.md) e [Hudi](../../15-lakehouse/06-apache-hudi/README.md).
</details>

## 6. 🟣 Implementação — Reproduzir um rollback

Usando o [Projeto 10](../../projects/10-capstone/README.md): rode o `demo`, depois `python -m capstone ops history`, restaure a silver para a versão anterior e **prove** que voltou (contagem de linhas). Em seguida reaplique o dia e prove que convergiu.

<details><summary>Gabarito</summary>

```bash
python -m capstone demo
python -m capstone ops history                         # lista versões/operações
python -m capstone ops version --version 2             # linhas na v2 (time travel, só leitura)
python -m capstone ops restore --version 2             # rollback (cria uma NOVA versão com o conteúdo da v2)
python -m capstone run --ds 2024-03-05                 # reaplica o dia: MERGE idempotente
python -m capstone ops history                         # a versão mais recente = o estado final; confira as linhas com `ops version`
```

Nota: `restore` **não apaga o histórico** — ele cria uma versão nova cujo conteúdo é o da versão-alvo.
</details>
