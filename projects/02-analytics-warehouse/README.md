# Projeto 02 — Analytics Warehouse (raw → dimensional → warehouse, com dbt)

> 🔵 Nível: intermediário · Módulos: [05 SQL](../../05-sql/README.md),
> [07 Data Modeling](../../07-data-modeling/README.md), [13 Data Warehouse](../../13-data-warehouse/README.md),
> [28 dbt](../../28-dbt/README.md), [12 Data Quality](../../12-data-quality/README.md) ·
> Anterior: [Projeto 01](../01-basic-etl/README.md) · Próximo: [Projeto 03](../03-orchestration/README.md)

## Objetivo

Construir um **data warehouse dimensional** (star schema) a partir de dados brutos de um e-commerce simulado,
seguindo **ELT**: carregar o bruto no warehouse (`raw`) e **transformar dentro dele com dbt** — staging limpo,
dimensões (incluindo **SCD tipo 2** via snapshot) e um **fato** no grão correto, tudo **testado e
documentado**. O ponto central: **o mesmo fato aponta para a versão do cliente vigente na data do pedido**
(análise histórica correta).

## Arquitetura

```text
 gerador sintético           RAW (espelho OLTP)             STAGING (views)            MARTS (tabelas)
 scripts/raw_data.py ─EL─►  raw.customers           ─►  stg_customers ──► snap_customers (SCD2)
 scripts/load_raw.py        raw.products            ─►  stg_products   ──────────┐        │
 (dia 1 / dia 2)            raw.orders              ─►  stg_orders ──┐           ▼        ▼
                            raw.order_items         ─►  stg_order_items ─► fct_sales ◄─ dim_customer (SCD2)
                                                                           ▲  ▲  ▲      dim_product (SCD1)
                                                                           │  │  └────── dim_date
                                                                    testes: unique · not_null · relationships ·
                                                                    accepted_values · reconciliação · SCD2 saudável
```

### Modelo dimensional

```text
                  dim_date
                     │ date_sk
dim_customer ── customer_sk ── FCT_SALES ── product_sk ── dim_product
 (SCD2: valid_from/to,           grão: 1 linha por item de pedido (order_id + line_no)
  is_current)                    métricas aditivas: quantity, gross_amount, discount_amount, net_amount
```

| Decisão de modelagem | Por quê |
| --- | --- |
| **Grão = item do pedido** | máximo detalhe; métricas **aditivas** (`net = qtd × preço × (1 − desconto)`) — ver [fact tables](../../07-data-modeling/07-fact-tables/README.md) |
| **Surrogate keys** (`md5`) nas dimensões | desacopla de chaves de negócio e **viabiliza SCD2** — [chaves](../../07-data-modeling/09-surrogate-natural-keys/README.md) |
| **dim_customer SCD2** | análises por UF/segmento devem refletir **como era na época** — [SCD](../../07-data-modeling/10-slowly-changing-dimensions/README.md) |
| **1ª versão com `valid_from = 1900-01-01`** | fatos anteriores ao 1º snapshot nunca ficam sem dimensão |
| **dim_product SCD1** | só o estado atual do produto importa aqui (decisão **por atributo**) |
| **Membro "desconhecido"** | FK ausente cai nele em vez de **sumir** do fato num join |
| **Join *as-of*** (`order_ts ∈ [valid_from, valid_to)`) | liga o fato à versão correta; janelas sem sobreposição (testado) |
| **`order_status` no fato** | atributo degenerado; receita exclui `canceled` na consulta, não na carga |

## Requisitos

Docker + Compose, Python 3.11+, `dbt-postgres ≥ 1.10` e `psycopg` ([`requirements.txt`](requirements.txt)).
Testado com dbt-core 1.12 / dbt-postgres 1.11 e PostgreSQL 16.

## Estrutura

```text
02-analytics-warehouse/
├── docker-compose.yml · profiles.yml · dbt_project.yml · requirements.txt · .env.example
├── scripts/                   # gerador determinístico (raw_data.py) + carga raw (load_raw.py, COPY)
├── sql/raw_schema.sql         # DDL do schema raw
├── models/
│   ├── staging/               # _sources.yml (freshness) · stg_* (views: tipos, limpeza, métricas por linha)
│   └── marts/                 # dim_date · dim_product · dim_customer (SCD2) · fct_sales · _marts.yml
├── snapshots/snap_customers.sql      # SCD2 automatizado (estratégia timestamp)
├── tests/                     # testes SINGULARES dbt: reconciliação e saúde do SCD2
├── macros/test_unique_combination.sql # teste genérico próprio (sem pacotes externos)
├── analyses/receita_por_mes_uf_categoria.sql
└── pytests/                   # testes Python do gerador (determinismo, integridade, dia 2)
```

## Execução

```bash
cd projects/02-analytics-warehouse
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt pytest

# 1) PostgreSQL (se a 5432 estiver ocupada: POSTGRES_PORT=5433 docker compose up -d  e  export DBT_PORT=5433)
docker compose up -d

# 2) DIA 1: carrega o RAW e constrói tudo (snapshot + modelos + testes, na ordem do DAG)
python scripts/load_raw.py --day 1
dbt build --profiles-dir .

# 3) DIA 2: 10% dos clientes mudam de UF/segmento e entram novos pedidos
python scripts/load_raw.py --day 2
dbt build --profiles-dir .          # o snapshot cria as NOVAS VERSÕES (SCD2)

# 4) explore
docker compose exec postgres psql -U de -d warehouse
```

> ⚠️ Use **`dbt build`** (e não `dbt snapshot` isolado) na primeira execução: o snapshot depende da view
> `stg_customers`, que só existe depois do staging ser construído. `dbt build` respeita a ordem do DAG.

Resultado esperado (dados sintéticos, seed fixa):

| Etapa | Fato (`fct_sales`) | `dim_customer` (versões / atuais) | Testes |
| --- | --- | --- | --- |
| Dia 1 | 3.718 linhas | 200 / 200 | 37 ✅ |
| Dia 2 | 4.441 linhas | **220** / 200 (20 clientes mudaram) | 37 ✅ |

Consulta-vitrine — a UF do cliente **na época** do pedido (cliente `C00098` mudou de BA para RJ em fev/2024):

```sql
select d.year_month, c.uf, count(distinct f.order_id) pedidos, round(sum(f.net_amount),2) receita
from analytics_marts.fct_sales f
join analytics_marts.dim_date d using (date_sk)
join analytics_marts.dim_customer c using (customer_sk)
where c.customer_id = 'C00098' and f.order_status <> 'canceled'
group by 1, 2 order by 1;
--  2024-01 | BA | 3 | 2567.42      (como era em janeiro)
--  2024-02 | RJ | 2 | 1317.00      (como ficou depois)
```

Docs/lineage: `dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .`

## Testes

```bash
dbt build --profiles-dir .        # roda modelos E testes juntos (um modelo que falha bloqueia os dependentes)
dbt test  --profiles-dir .        # só os testes
pytest -q pytests                 # testes do gerador (sem banco)
```

| Camada de teste | O que garante |
| --- | --- |
| **Genéricos** | `unique`/`not_null` nas chaves; `accepted_values` em `status`; `relationships` fato→dimensões |
| **Teste próprio** | combinação `(order_id, line_no)` única (o grão do fato) |
| **Reconciliação** (`assert_fct_sales_reconcilia_com_staging`) | o fato **não perde nem multiplica** linhas/valores vs. origem (pega *fan-out*) |
| **SCD2 saudável** | exatamente **1 versão atual** por cliente; **sem sobreposição** de vigências |
| **Freshness** (sources) | `dbt source freshness` alerta se a carga raw atrasar |

## Decisões arquiteturais e trade-offs

- **ELT**: raw no warehouse + transformação em SQL/dbt ([ETL vs ELT](../../09-etl-elt/01-etl-vs-elt/README.md)) —
  simples e versionado; custo: o compute do warehouse faz a transformação.
- **Staging como *view***: barato e sem duplicar dados; marts como **tabelas** (consulta rápida). Para volumes
  maiores, `fct_sales` deve ser **incremental** ([dbt incremental](../../28-dbt/08-incremental-models/README.md)).
- **Raw por *full refresh***: simula uma réplica da origem; o **histórico não se perde** porque o *snapshot*
  captura as mudanças a cada execução. Limitação: mudanças **entre** duas execuções do snapshot se perdem —
  para capturar tudo, use [CDC](../../09-etl-elt/06-cdc/README.md).
- **Hash como surrogate key**: determinística, sem sequência central; custo: chaves maiores que inteiros.
- **Testes de constraint no warehouse** são *informativos* em muitos engines — por isso a integridade é
  garantida por **testes dbt**, não por `FOREIGN KEY` ([constraints](../../05-sql/09-constraints/README.md)).
- **Sem pacotes externos** (`dbt_utils`): o teste de unicidade composta é um macro de 4 linhas, o que mantém o
  projeto reprodutível offline. Em projetos reais, prefira `dbt_utils.unique_combination_of_columns`.

## Possíveis melhorias (exercícios)

1. Tornar `fct_sales` **incremental** (`delete+insert` por `order_date`) com *lookback* de 3 dias para pedidos
   tardios.
2. Adicionar **`dim_geography`** (outrigger/snowflake) e comparar o plano de execução.
3. Criar um **mart agregado** (`mart_receita_mensal`) e uma *materialized view*; medir o ganho com `EXPLAIN`.
4. **Contrato de dados** do `fct_sales` (`contract: enforced`) e *source freshness* no CI ([módulo 29](../../29-data-contracts/README.md)).
5. Rodar em **CI** (GitHub Actions) com Postgres como serviço e `dbt build --select state:modified+`.
6. Trocar o loader por **CDC** (Debezium) e reconstruir a dimensão SCD2 com `MERGE`.

## Referências

- Kimball & Ross, *The Data Warehouse Toolkit* (3ª ed.) — grão, SCD, dimensões conformadas.
- Documentação do dbt: [snapshots](https://docs.getdbt.com/docs/build/snapshots), [tests](https://docs.getdbt.com/docs/build/data-tests),
  [sources/freshness](https://docs.getdbt.com/docs/build/sources). Módulos [07](../../07-data-modeling/README.md) e [28](../../28-dbt/README.md).
