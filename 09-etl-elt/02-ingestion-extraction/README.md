# Ingestão e extração

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

**Extração/ingestão** é o "E" do ETL/ELT: trazer dados das **fontes** (bancos, APIs,
arquivos, eventos) para dentro da plataforma de dados. É a primeira etapa do
[ciclo de vida](../../01-foundations/03-data-lifecycle/README.md) e, muitas vezes, a mais
frágil — porque você **não controla** as fontes.

## Fontes e seus desafios

| Fonte | Como extrair | Desafios |
| --- | --- | --- |
| Banco [relacional](../../06-databases/01-relational-concepts/README.md) | query/dump/réplica/[CDC](../06-cdc/README.md) | não impactar produção; snapshots consistentes |
| [API HTTP](../../04-python-for-data-engineering/08-http-clients/README.md) | requests paginados | paginação, rate limit, auth, schema variável |
| Arquivos (CSV/JSON/[Parquet](../../08-data-formats/README.md)) | ler de FTP/SFTP/object storage | formatos sujos, encoding, chegada parcial |
| Eventos/[Kafka](../../18-message-brokers/README.md) | consumidor | offsets, ordem, exactly-once |
| SaaS (CRM, ads) | conectores/APIs | limites, schemas instáveis |

## Dois modos de ingestão

- **Batch** — em lotes, por [agendamento](../../10-data-pipelines/03-scheduling/README.md)
  (ex.: toda madrugada). Simples, barato, latência de horas.
- **Streaming** — contínuo, evento a evento (ver
  [batch vs streaming](../../01-foundations/06-batch-vs-streaming/README.md) e
  [streaming](../../17-streaming/README.md)). Baixa latência, mais complexo.

Comece batch; vá para streaming quando a latência for um requisito real.

## Full vs incremental

A decisão central da extração (aprofundada em
[full vs incremental](../05-full-vs-incremental/README.md)):

- **Full** — extrai tudo toda vez. Simples; inviável em volume.
- **Incremental** — extrai só o que mudou desde a última execução, via **watermark**
  (ex.: `updated_at > última_marca`) ou [CDC](../06-cdc/README.md). Eficiente; exige
  controlar o estado (a marca).

```sql
-- extração incremental por watermark
SELECT * FROM pedidos WHERE updated_at > :ultima_marca ORDER BY updated_at;
```

## Extrair de bancos sem derrubar a produção

- **Réplica de leitura** — aponte a extração para a [réplica](../../06-databases/07-replication/README.md),
  não para o primário.
- **[CDC via log](../06-cdc/README.md)** (WAL/binlog) — captura mudanças com impacto
  mínimo e baixa latência.
- **Janela de baixo tráfego** para dumps completos.
- Cuidado com **consistência**: um `SELECT` longo numa tabela que muda pode pegar um estado
  inconsistente — use snapshot/transação ou CDC.

## Consumir APIs robustamente

Resumo (detalhado em [HTTP clients](../../04-python-for-data-engineering/08-http-clients/README.md)):

- **Paginação** como [generator](../../04-python-for-data-engineering/06-iterators-generators-context-managers/README.md).
- **Retries com backoff** só para erros transitórios; respeite `429`/`Retry-After`.
- **Autenticação** com segredos fora do código.
- **Incremental** via parâmetro `since`/cursor persistido.

## A camada raw (landing/bronze)

Boa prática: gravar o dado extraído **cru**, do jeito que chegou, numa camada *raw/bronze*
(ver [medallion](../../14-data-lake/03-medallion-architecture/README.md)), **antes** de
transformar. Benefícios:

- **Reprocessamento** — se a transformação tiver bug, reprocessa do raw sem re-extrair.
- **Auditoria** — você tem a fonte exata do que foi recebido.
- **Desacoplamento** — extração e transformação evoluem separadas.

Formato: preserve o original (JSON/CSV) e/ou converta para
[Parquet](../../08-data-formats/04-parquet/README.md); particione por data de ingestão.

## Idempotência na ingestão

A extração deve ser **re-executável** sem duplicar (ver
[idempotência](../07-idempotency-retries/README.md)): escreva em arquivo/partição
determinística (ex.: por data), com escrita atômica (tmp + move), para que rodar de novo
sobrescreva em vez de acumular.

## Metadados de ingestão

Registre, junto do dado: **data/hora de ingestão**, **fonte**, **versão do schema**,
**contagem de registros**, **marca/cursor**. Isso alimenta
[observabilidade](../../24-observability/README.md), [lineage](../../27-data-catalog-metadata/README.md)
e o controle incremental.

## Ferramentas

- **Código próprio** (Python + requests/SQL) — controle total.
- **Airbyte / Meltano** — conectores prontos (open source).
- **Fivetran / Stitch** — gerenciados (ELT, baixo esforço, custo).
- **Kafka Connect / Debezium** — streaming e [CDC](../06-cdc/README.md).

## Erros comuns

- Extrair do banco primário de produção e degradá-lo.
- Full load onde incremental era necessário (lento/caro) — ou incremental sem watermark
  confiável (perde registros).
- Não gravar a camada raw → impossível reprocessar.
- Ignorar paginação/rate limit de APIs.
- Snapshot inconsistente de tabela que muda durante a extração.

## Boas práticas

- Extraia de réplicas/CDC; prefira incremental com watermark/cursor confiável.
- Grave o raw imutável e particionado; ingestão idempotente.
- Registre metadados de ingestão; monitore volume e frescor.
- Trate APIs com paginação, retries e segredos seguros.

## Relação com outros conceitos

- [Full vs incremental](../05-full-vs-incremental/README.md),
  [CDC](../06-cdc/README.md), [idempotência](../07-idempotency-retries/README.md).
- [HTTP clients](../../04-python-for-data-engineering/08-http-clients/README.md),
  [réplicas](../../06-databases/07-replication/README.md).
- Camada [raw/bronze](../../14-data-lake/03-medallion-architecture/README.md).

## Exercícios

1. Projete uma extração incremental por `updated_at`, incluindo onde guardar a marca.
2. Explique como extrair de um Postgres de produção sem impactá-lo (3 opções).
3. Escreva a ingestão de uma API paginada que grava JSONL no raw particionado por data, de
   forma idempotente.
4. Liste os metadados que você anexaria a cada lote ingerido.

## Referências

- Reis & Housley, *Fundamentals of Data Engineering* — cap. 7 (ingestão).
- Documentação de Airbyte, Debezium, Kafka Connect.
