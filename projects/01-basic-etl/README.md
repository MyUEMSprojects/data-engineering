# Projeto 01 — ETL básico (CSV/API → Python → PostgreSQL)

> 🟢→🔵 Nível: iniciante · Módulos relacionados: [04 Python](../../04-python-for-data-engineering/README.md),
> [05 SQL](../../05-sql/README.md), [09 ETL/ELT](../../09-etl-elt/README.md),
> [12 Data Quality](../../12-data-quality/README.md) · Próximo:
> [Projeto 02 — Analytics Warehouse](../02-analytics-warehouse/README.md)

## Objetivo

Construir o pipeline ETL "mínimo, mas correto": ler pedidos de um **CSV** (ou de uma **API paginada**),
**validar e limpar**, **deduplicar** e **carregar** no PostgreSQL — de forma **idempotente**, com
**quarentena** de linhas inválidas e um **gate de qualidade**. O foco não é a quantidade de código, e sim as
propriedades que separam um script de um pipeline: **reexecutar é seguro**, **dado ruim não passa em
silêncio** e **a lógica é testável sem banco**.

## Arquitetura

```text
 CSV (stream) ─┐                                  ┌─► orders            (upsert idempotente, nunca regride)
               ├─► extract ─► validate ─► dedupe ─┤
 API paginada ─┘   (generators)  (pura)    (pura) └─► orders_rejected   (quarentena, idempotente, com motivo)
                                    │
                         gate: taxa de rejeição > limite ⇒ ABORTA antes de carregar
```

| Módulo | Responsabilidade | Pura (sem I/O)? |
| --- | --- | :-: |
| [`extract.py`](src/basic_etl/extract.py) | CSV em *streaming*; API com paginação por cursor, retry/backoff só p/ transitórios | — |
| [`transform.py`](src/basic_etl/transform.py) | parse/validação/normalização, quarentena de linhas, dedupe determinístico | ✅ |
| [`load.py`](src/basic_etl/load.py) | `INSERT … ON CONFLICT DO UPDATE` em lotes, numa transação; quarentena por hash | — |
| [`pipeline.py`](src/basic_etl/pipeline.py) | orquestra, métricas da execução, gate de qualidade, CLI | parcial |

## Requisitos

- Python ≥ 3.11 · Docker (para o PostgreSQL local) · `make` é opcional.
- Dependências: `psycopg[binary]`, `requests` ([`requirements.txt`](requirements.txt)); dev: `pytest`, `ruff`,
  `black` ([`requirements-dev.txt`](../../requirements-dev.txt) da raiz).

## Estrutura

```text
01-basic-etl/
├── docker-compose.yml       # PostgreSQL 16 (aplica sql/schema.sql na criação)
├── sql/schema.sql           # tabelas orders e orders_rejected (idempotente)
├── scripts/generate_sample_data.py   # CSV sintético COM sujeira proposital
├── sample_data/orders.csv   # amostra gerada (500 linhas + sujeira)
├── src/basic_etl/           # extract / transform / load / pipeline
├── tests/                   # unitários (sem banco) + integração (com PostgreSQL)
├── pyproject.toml · requirements.txt · .env.example
```

## Execução

```bash
cd projects/01-basic-etl
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest

# 1) sobe o PostgreSQL  (se a porta 5432 estiver ocupada: POSTGRES_PORT=5433 docker compose up -d)
docker compose up -d

# 2) gera dados de exemplo (com duplicatas, status inválido, valor negativo, UF inexistente...)
python scripts/generate_sample_data.py --rows 500 --out sample_data/orders.csv

# 3) valida sem gravar
export PYTHONPATH=src
python -m basic_etl --csv sample_data/orders.csv --dry-run

# 4) carrega de verdade
export DATABASE_URL=postgresql://de:de@localhost:5432/warehouse
python -m basic_etl --csv sample_data/orders.csv

# 5) reexecute: o resultado é o mesmo (idempotência)
python -m basic_etl --csv sample_data/orders.csv
docker compose exec postgres psql -U de -d warehouse \
  -c "select count(*) from orders;" -c "select reason, count(*) from orders_rejected group by 1;"
```

Saída típica (500 linhas geradas → 508 lidas com duplicatas):

```text
lidas=508 válidas=477 rejeitadas=31 após_dedupe=471 carregadas=471
```

Fonte por **API** (contrato: `GET url?limit=N&since=…` → `{"data":[…], "next": url|null}`):

```bash
python -m basic_etl --api-url https://api.exemplo.com/v1/orders --since 2024-01-01T00:00:00Z
```

## Testes

```bash
pytest -q                       # unitários: validação, dedupe, CSV, paginação, retries, CLI (sem banco)

# integração: exige PostgreSQL
docker compose up -d
TEST_DATABASE_URL=postgresql://de:de@localhost:5432/warehouse pytest -q -m integration
```

O que os testes garantem:

- **Validação** parametrizada (9 tipos de linha inválida) e que **nenhuma linha some** (`válidas + rejeitadas = lidas`).
- **Dedupe idempotente** e independente da ordem de chegada.
- **CSV** com aspas/vírgulas/quebras de linha e BOM; **paginação**; **retry só em 429/5xx** (respeitando
  `Retry-After`) e **sem retry em 4xx**.
- **Idempotência da carga** (rodar 2× = mesmo estado), **upsert que nunca regride** versão e **quarentena
  idempotente** — contra um PostgreSQL real.

## Decisões arquiteturais

| Decisão | Motivo |
| --- | --- |
| **Transformação pura**, I/O nas bordas | testável sem banco/rede; ver [organização de projetos](../../03-git-software-engineering/07-project-organization/README.md) |
| **Upsert por chave** (`ON CONFLICT`) com `WHERE updated_at >=` | [idempotência](../../09-etl-elt/07-idempotency-retries/README.md): retry/backfill seguros; dado velho não sobrescreve novo |
| **Uma transação por carga** | tudo-ou-nada: falha no meio não deixa estado parcial |
| **Quarentena em vez de descartar** | auditável e reprocessável; `row_hash` torna a quarentena idempotente |
| **Gate de taxa de rejeição** | uma mudança de schema na origem vira erro claro, não lixo no destino |
| **`Decimal` para dinheiro; datas *timezone-aware* (UTC)** | evita erros de `float` e de fuso |
| **Retry só para erros transitórios**, com backoff e `Retry-After` | [HTTP clients](../../04-python-for-data-engineering/08-http-clients/README.md) |
| **`encoding utf-8-sig`** no CSV | tolera BOM comum em exports do Excel |

## Trade-offs e limitações

- Carga **em memória** (`list`) para validar+deduplicar: ok para centenas de milhares de linhas; para volumes
  maiores, processe em *chunks* particionados e deduplique no banco (ver [Projeto 05](../05-data-lake/README.md)/[06](../06-spark/README.md)).
- `executemany` é suficiente aqui; para milhões de linhas, use `COPY` para uma tabela de *staging* + `MERGE`.
- Sem **orquestração** nem agendamento (próximo passo: [Projeto 03](../03-orchestration/README.md)).
- `md5` na quarentena é só identidade da linha (não é uso de segurança).

## Possíveis melhorias (exercícios)

1. **`COPY` + staging + `MERGE`** para cargas grandes; compare o tempo com `executemany`.
2. **Extração incremental** da API: guardar a marca d'água (`max(updated_at)`) numa tabela de controle.
3. **Observabilidade**: logs JSON com `run_id` e métricas Prometheus (linhas/duração).
4. **Contrato de dados** do pedido em YAML ([módulo 29](../../29-data-contracts/README.md)) validado no CI.
5. **Empacotar em Docker** (multi-stage) e agendar com um CronJob/Airflow.
6. **Testes de propriedade** (`hypothesis`) para a validação/dedupe.

## Referências

- [ETL/ELT](../../09-etl-elt/README.md): [idempotência](../../09-etl-elt/07-idempotency-retries/README.md),
  [dedupe](../../09-etl-elt/09-deduplication/README.md), [validação](../../09-etl-elt/10-data-validation/README.md).
- Documentação do [psycopg 3](https://www.psycopg.org/psycopg3/docs/) (transações, `executemany`) e do PostgreSQL (`INSERT … ON CONFLICT`).
