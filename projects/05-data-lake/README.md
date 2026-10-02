# Projeto 05 — Data Lake (object storage + Parquet + particionamento + medallion)

> 🟣 Nível: intermediário/avançado · Módulos: [14 Data Lake](../../14-data-lake/README.md),
> [08 Formatos](../../08-data-formats/README.md), [19 Cloud (object storage)](../../19-cloud/02-object-storage/README.md),
> [09 ETL/ELT](../../09-etl-elt/README.md) · Anterior: [Projeto 04](../04-data-quality/README.md) ·
> Próximo: [Projeto 06](../06-spark/README.md)

## Objetivo

Construir um **data lake** de verdade sobre *object storage* com a API **S3**: dados brutos imutáveis
(**bronze**), dados limpos e particionados em **Parquet** (**silver**) e tabelas analíticas (**gold**) —
a [arquitetura medallion](../../14-data-lake/03-medallion-architecture/README.md). O foco são as
propriedades que fazem um lake funcionar (ou virar um "pântano"):

- **imutabilidade e reprocessamento**: toda a silver/gold é reconstruível a partir da bronze;
- **idempotência** de ponta a ponta (reexecutar não muda nada);
- **particionamento** por data de **negócio** e *partition pruning* (medido);
- **dado tardio** (*late data*) e eventos fora de ordem;
- **arquivos pequenos** e *compaction*;
- **quarentena** com motivo, **linhagem** (`_source_file`) e inventário por **metadados**.

## Arquitetura

```text
  fonte (API/CDC simulada)        OBJECT STORAGE (S3 API ‑ SeaweedFS local, ou disco `file://`)
  eventos de pedidos JSONL  ──►  ┌────────────────────────────────────────────────────────────────────┐
  (novos + atualizações          │ bronze/orders/ingest_date=D/batch-<sha>.jsonl     IMUTÁVEL, bruto   │
   + duplicatas + lixo)          │        │  parse · valida · tipa · deduplica (maior updated_at)      │
                                 │        ▼                                                            │
                                 │ silver/orders/order_date=D/part-<hash>-i-of-N.parquet  LIMPO        │
                                 │ quarantine/orders/ingest_date=D/…parquet  rejeitadas + motivo + raw │
                                 │        │  DuckDB (SQL) sobre Arrow                                  │
                                 │        ▼                                                            │
                                 │ gold/{daily_revenue, customer_value, status_funnel}/part-….parquet  │
                                 └────────────────────────────────────────────────────────────────────┘
                                   consulta: `lake query "<SQL>"` (DuckDB) · `lake inventory` · `lake prune`
```

| Camada | O que guarda | Particiona por | Por quê |
| --- | --- | --- | --- |
| **bronze** | bytes **exatos** que chegaram (JSONL) | **data de ingestão** | auditoria + reprocessamento; a data de ingestão é sempre conhecida |
| **silver** | pedidos tipados, 1 linha por `order_id` | **data de negócio** (`order_date`) | consultas filtram por data do pedido ⇒ *pruning* |
| **quarantine** | linha original + `reason` + arquivo/linha de origem | data de ingestão | diagnóstico e reenvio; nada some em silêncio |
| **gold** | agregações de consumo | — (pequenas) | prontas para BI; *full refresh* barato |

## Requisitos

Python ≥ 3.11 (`pyarrow`, `duckdb`). Docker é **opcional**: sem ele o lake roda em disco local
(`file://`); com ele, num object storage S3 de verdade.

> **Por que SeaweedFS e não MinIO?** O MinIO foi a escolha "óbvia" para S3 local, mas a edição comunitária
> deixou de publicar imagens Docker públicas (Docker Hub/Quay — a tag que tentei resolver retornou *401*).
> Em vez de apontar para uma imagem que não baixa, o projeto usa o **SeaweedFS** (Apache-2.0, ativo) com
> `weed server -s3`. **Nada no código depende dele**: qualquer endpoint S3 serve (MinIO, Ceph, Garage,
> AWS S3 — basta mudar `LAKE_S3_*`). Esse é justamente o valor da API S3 como interface comum.

## Estrutura

```text
05-data-lake/
├── docker-compose.yml · s3/identities.json   # SeaweedFS (S3) + credencial de EXEMPLO (só local)
├── src/lake/
│   ├── storage.py     # Lake: o MESMO código em disco local e em S3 (pyarrow.fs)
│   ├── synth.py       # fonte sintética determinística (novos, updates, duplicatas, lixo)
│   ├── bronze.py      # ingestão imutável e idempotente (nome = hash do conteúdo)
│   ├── silver.py      # parse/validação/quarentena/deduplicação/particionamento
│   ├── publish.py     # publicação idempotente de um "diretório de tabela" (hash + layout)
│   ├── gold.py        # SQL (DuckDB) → tabelas analíticas
│   ├── reader.py      # dataset Hive + relatório de partition pruning
│   ├── compaction.py  # arquivos pequenos → poucos arquivos grandes
│   ├── inventory.py   # inventário por metadados (rodapé do Parquet)
│   └── cli.py         # init | ingest | silver | gold | run | demo | inventory | prune | compact | query
└── tests/             # 26 testes (rodam em disco local e, com LAKE_URI_TEST, no S3)
```

## Execução

### A) Disco local (zero infraestrutura)

```bash
cd projects/05-data-lake
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
export PYTHONPATH=src            # o lake fica em ./lake-data (ignorado pelo git)

python -m lake demo --days 5     # 5 dias de ingestão + reexecução + gold + inventário
```

### B) Object storage S3 de verdade (Docker)

```bash
docker compose up -d                              # (porta ocupada? export S3_PORT=8399)
export LAKE_URI=s3://lake LAKE_S3_ENDPOINT=localhost:${S3_PORT:-8333}
python -m lake init                               # cria o bucket
python -m lake demo --days 5
docker compose down -v                            # limpa
```

Saída verificada no **S3** (SeaweedFS), dados sintéticos determinísticos (1.º dia ≈ 300 pedidos):

```text
=== REEXECUÇÃO do último dia (idempotência: nada deve mudar) ===
bronze  JÁ EXISTIA (no-op) bronze/orders/ingest_date=2024-01-05/batch-d0b4b1fbec3c.jsonl (71.0 KB)
silver  bronze=5 arquivos · linhas=1714 · válidas=1683 · rejeitadas=31 · duplicatas/atualizações colapsadas=183 · pedidos=1500
        partições: 0 escritas · 5 inalteradas
        rejeições: {'bad_date': 6, 'invalid_json': 7, 'missing_field:amount': 5, 'missing_field:customer_id': 7, ...}

camada     tabela            arquivos    tamanho   linhas  dirs
bronze     orders                   5   335.0 KB        -     5
gold       customer_value           1     4.4 KB      390     1
gold       daily_revenue            1     3.2 KB      125     1
quarantine orders                   5    12.8 KB       31     5
silver     orders                   5    37.1 KB     1500     5
```

### Experimentos guiados

```bash
# 1) PARTITION PRUNING — filtrar por data lê só as partições necessárias
python -m lake prune --from 2024-01-04 --to 2024-01-05
#   arquivos totais=5 · lidos=2 · PULADOS=3 · linhas retornadas=600

# 2) PROBLEMA DOS ARQUIVOS PEQUENOS — produza-o de propósito e corrija
python -m lake silver --rows-per-file 100 && python -m lake inventory | grep silver
#   silver  orders   15 arquivos   68.2 KB   1500 linhas
python -m lake compact
#   compaction: 5 partições · arquivos 15 → 5 · 1500 linhas (inalteradas)

# 3) CONSULTA ANALÍTICA direto no lake (DuckDB)
python -m lake query "select country, sum(revenue) rev from daily_revenue group by 1 order by 2 desc"

# 4) USAR OS DADOS DA SUA FONTE: grave um JSONL e ingira
python -m lake ingest --date 2024-02-01 --file meu_lote.jsonl && python -m lake silver && python -m lake gold

# 5) REPROCESSAR DO ZERO: apague silver/ e gold/ e reconstrua — o resultado é byte a byte o mesmo
python -m lake silver && python -m lake gold
```

## Testes

```bash
pytest -q                                                    # 26 testes, <1s, disco local
LAKE_URI_TEST=s3://lake LAKE_S3_ENDPOINT=localhost:8333 pytest -q    # os MESMOS testes no S3 (prefixo único por teste)
```

| Grupo | O que garante |
| --- | --- |
| **Fonte / parsing** | geração determinística; contém duplicatas, JSON truncado e *updates* de pedidos antigos; cada tipo de lixo → **motivo explícito** |
| **Bronze** | reingestão = no-op; conteúdo diferente nunca sobrescreve; bytes idênticos ao original |
| **Silver** | `lidas = válidas + rejeitadas`; evento **mais novo vence** e **evento velho tardio é ignorado**; dado tardio reescreve **só** a sua partição; reprocessar do zero reproduz os **mesmos arquivos** |
| **Regressão de layout** | trocar o tamanho dos arquivos nunca duplica linhas (bug real, ver abaixo) |
| **Leitura** | *pruning* pula arquivos (4 → 1) e retorna as mesmas linhas |
| **Compaction** | menos arquivos, **tabela idêntica** (`Table.equals`) |
| **Inventário** | linhas vêm do rodapé do Parquet; JSONL não tem contagem sem ler |
| **Gold** | receita reconcilia com a silver, **exclui cancelados** (o funil não); *full refresh* idempotente |

> 🐞 **Bug real encontrado rodando o experimento 2 no S3**: a publicação nomeava os arquivos
> `part-<hash>-000.parquet`; ao mudar só o *tamanho dos arquivos*, o `-000` do layout antigo tinha o mesmo
> nome do novo, não era reescrito e **as linhas apareciam em dobro** (1500 → 2500). Correção: o nome
> codifica o layout (`-<i>-of-<N>`), com teste de regressão. Moral: idempotência baseada em nome precisa
> que o nome represente **tudo** que muda o conteúdo físico.

## Decisões arquiteturais e trade-offs

- **Bronze imutável com nome = hash do conteúdo** → idempotência e imutabilidade "de graça", mas lotes
  *quase* iguais (diferença de 1 byte) viram arquivos distintos; o dedup ocorre na silver
  ([idempotência](../../09-etl-elt/07-idempotency-retries/README.md), [deduplicação](../../09-etl-elt/09-deduplication/README.md)).
- **Silver recomputada da bronze inteira (full recompute)**: simples, determinística e **reprodutível**.
  Custo: cresce com a bronze. Em volume real → incremental por partição afetada + *watermark*
  ([incremental vs full](../../09-etl-elt/05-full-vs-incremental/README.md)); aqui o mecanismo de
  "só reescrever o que mudou" (hash por partição) já está presente.
- **Particionar por `order_date` (negócio), não por ingestão**: é o filtro das consultas. Custo: dado
  tardio reescreve partições antigas. A cardinalidade é baixa (1 dir/dia) — **nunca** particione por
  `customer_id` ([particionamento](../../14-data-lake/05-partitioning/README.md)).
- **Evento mais novo vence (`updated_at`)** e não "o último que chegou": chegada ≠ ordem dos fatos.
- **Parquet + zstd, `decimal(12,2)` para dinheiro, `timestamp UTC`**: colunar, comprimido, tipado — nunca
  `float` para valores monetários ([Parquet](../../08-data-formats/04-parquet/README.md),
  [colunar vs linha](../../08-data-formats/08-row-vs-columnar/README.md)).
- **`order_date` só no caminho da partição** (não repetida no arquivo): padrão Hive; evita conflito de
  colunas ao ler como *dataset*.
- **⚠️ Atomicidade parcial (limite honesto)**: `publish_dir` grava os arquivos novos e **depois** apaga
  os antigos — um leitor concorrente nessa janela vê versões misturadas. Não há *transação* em object
  storage puro. **É exatamente a lacuna que Delta/Iceberg/Hudi resolvem** com um log de transações
  ([ACID no object storage](../../15-lakehouse/03-acid-on-object-storage/README.md)) — e o motivo de o
  [Projeto 10](../10-capstone/README.md) usar um *table format*.
- **Gold em *full refresh***: tabelas pequenas; trocar por incremental só quando o custo justificar.
- **Credenciais de exemplo** no repositório (`s3/identities.json`) servem **só ao ambiente local**; em
  nuvem use IAM/roles, nunca chaves fixas ([IAM e segredos](../../19-cloud/06-iam-secrets/README.md)).
- **Dados em memória (Arrow)**: suficiente para ~10⁶ linhas. Acima disso → [Spark (Projeto 06)](../06-spark/README.md).

## Erros comuns que este projeto evita (e que você verá por aí)

1. **Sobrescrever a bronze** ou transformá-la "só um pouquinho" → perde-se a capacidade de reprocessar.
2. **Particionar por coluna de alta cardinalidade** → milhões de diretórios/arquivos minúsculos.
3. **Confiar na ordem de chegada** para resolver conflitos.
4. **Descartar linhas inválidas em silêncio** (sem quarentena/contagem).
5. **Gravar `float` para dinheiro** e `timestamp` sem fuso.
6. **Listar o bucket inteiro** para saber "o que há aí" em vez de usar metadados/catálogo
   ([metadados](../../14-data-lake/07-metadata/README.md)).

## Possíveis melhorias (exercícios)

1. **Esquema evolutivo**: a fonte passa a enviar `coupon_code` — adicione a coluna à silver sem quebrar
   partições antigas ([schema evolution](../../08-data-formats/10-schema-evolution/README.md)).
2. **Silver incremental**: processe apenas arquivos bronze novos (guarde um *manifest* de processados) e
   reescreva somente as partições afetadas; compare custo com o *full recompute*.
3. **Z-order/ordenação**: ordene a silver por `customer_id` dentro da partição e meça o ganho de
   *row-group pruning* com estatísticas do Parquet (`parquet_metadata`).
4. **Catálogo**: grave um `catalog.json` (tabelas, schema, partições, dono) e valide no CI
   ([catálogo](../../27-data-catalog-metadata/README.md)).
5. **Ciclo de vida**: política de retenção da bronze (ex.: mover > 90 dias para "frio") e da quarentena
   ([custos](../../19-cloud/08-cost-management/README.md)).
6. **Delta/Iceberg**: troque `publish_dir` por uma tabela Delta (`deltalake`) ou Iceberg (`pyiceberg`) e
   elimine a janela de inconsistência ([módulo 15](../../15-lakehouse/README.md)).
7. **Orquestração**: encapsule `ingest → silver → gold` num DAG do [Projeto 03](../03-orchestration/README.md)
   e valide a silver com o gate do [Projeto 04](../04-data-quality/README.md).
8. **Terraform/AWS real**: provisione um bucket S3 versionado com *lifecycle* e rode o mesmo código com
   `LAKE_URI=s3://…` (ver [Projeto 09](../09-cloud/README.md)).

## Referências

- [Apache Arrow — `pyarrow.fs` e Datasets](https://arrow.apache.org/docs/python/filesystems.html) · [Parquet](https://parquet.apache.org/docs/) ·
  [DuckDB](https://duckdb.org/docs/) · [SeaweedFS S3 API](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-S3-API).
- Módulos [14](../../14-data-lake/README.md), [08](../../08-data-formats/README.md) e [15](../../15-lakehouse/README.md);
  Reis & Housley, *Fundamentals of Data Engineering* (cap. armazenamento).
