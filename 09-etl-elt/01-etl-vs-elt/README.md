# ETL vs ELT

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

Duas ordens de executar as três operações de um pipeline de dados:

- **ETL (Extract, Transform, Load)** — extrai da origem, **transforma** (num motor
  intermediário) e **carrega** o resultado já pronto no destino.
- **ELT (Extract, Load, Transform)** — extrai, **carrega o dado bruto** no destino e
  **transforma dentro dele** (usando o poder do warehouse/lake).

```text
ETL:  Fonte ─► Extract ─► [Transform em motor externo] ─► Load (dado pronto) ─► Warehouse
ELT:  Fonte ─► Extract ─► Load (dado bruto) ─► Warehouse ─► Transform (SQL/dbt, in-place)
```

## Por que ELT ascendeu

ETL foi o padrão por décadas, quando storage e compute eram caros e o warehouse não dava
conta de transformar. Com os **warehouses na nuvem** ([BigQuery/Snowflake/Redshift](../../13-data-warehouse/README.md)) —
baratos, escaláveis e separando storage de compute — ficou vantajoso **carregar bruto e
transformar lá dentro** com SQL. Ferramentas como [dbt](../../28-dbt/README.md) tornaram o
"T" do ELT versionado e testável. Hoje, **ELT é o padrão** na maioria dos stacks analíticos
modernos.

## Comparação

| Aspecto | ETL | ELT |
| --- | --- | --- |
| Onde transforma | motor externo (Spark, Python, ferramenta) | dentro do warehouse/lake (SQL) |
| O que carrega | dado já transformado | dado bruto (+ transformações depois) |
| Flexibilidade | transformação fixa; re-extrair para remodelar | re-transformar o bruto quando quiser |
| Dado bruto preservado | não (por padrão) | **sim** (fica no destino) |
| Escala de transformação | limitada ao motor | aproveita o warehouse elástico |
| Custo | motor dedicado | compute do warehouse |
| Ferramentas | Informatica, Spark, scripts | [dbt](../../28-dbt/README.md) + warehouse |

## A grande vantagem do ELT: preservar o bruto

No ELT, o dado bruto fica carregado. Se amanhã você descobrir um bug na transformação ou
precisar de uma nova métrica, basta **re-transformar o bruto** — sem re-extrair da fonte
(que pode nem ter mais o histórico). No ETL clássico, a transformação é destrutiva: o que
não foi transformado "se perde". Isso conecta ao conceito de camada *raw/bronze* no
[medallion](../../14-data-lake/03-medallion-architecture/README.md).

## Quando ETL ainda faz sentido

ELT não é sempre a resposta:

- **Dados sensíveis/PII** que não podem entrar brutos no warehouse → transformar/mascarar
  **antes** (ETL), por [compliance/LGPD](../../26-security/08-lgpd/README.md).
- **Transformações muito pesadas/complexas** melhor servidas por
  [Spark](../../16-distributed-processing/README.md) (ML, processamento não-SQL).
- **Redução drástica de volume antes de carregar** (filtrar/agregar na fonte para economizar
  storage/custo).
- **Streaming** — transformação em voo (ver [streaming](../../17-streaming/README.md)).

Na prática, arquiteturas reais **misturam**: ELT para o grosso do analítico + ETL/Spark para
cargas pesadas e dados sensíveis.

## EtLT (o híbrido comum)

Um padrão frequente: um **"t" leve** na ingestão (limpeza mínima, mascaramento de PII,
normalização de formato) + o **"T" pesado** no warehouse (modelagem dimensional, agregações)
com dbt. Daí "EtLT".

## O papel de cada etapa (links)

- **Extract** → [ingestão/extração](../02-ingestion-extraction/README.md).
- **Transform** → [transformação](../03-transformation/README.md).
- **Load** → [loading](../04-loading/README.md).

## Erros comuns

- Tratar "ELT é sempre melhor" como dogma (PII bruta no warehouse, cargas pesadas mal
  servidas por SQL).
- No ETL, descartar o bruto e depois não conseguir remodelar/re-auditar.
- Carregar tudo bruto sem governança → [data swamp](../../14-data-lake/README.md).
- Transformar na fonte OLTP e impactar a produção.

## Boas práticas

- Default **ELT** para analytics; preserve a camada bruta.
- Use ETL/EtLT para PII, cargas pesadas (Spark) e redução de volume.
- Transformações versionadas e testadas ([dbt](../../28-dbt/README.md)/código).
- Decida pela natureza do dado e do custo, não pela moda.

## Relação com outros conceitos

- Implementado em [warehouse](../../13-data-warehouse/README.md)/[lake](../../14-data-lake/README.md)
  com [dbt](../../28-dbt/README.md)/[Spark](../../16-distributed-processing/README.md).
- Camadas: [medallion](../../14-data-lake/03-medallion-architecture/README.md).
- Orquestrado em [pipelines](../../10-data-pipelines/README.md).

## Exercícios

1. Para um caso com dados de PII, argumente por ETL em vez de ELT.
2. Descreva como o ELT permite corrigir uma métrica sem re-extrair da fonte.
3. Desenhe um fluxo EtLT para e-commerce (o que é "t" leve na ingestão vs "T" no
   warehouse).
4. Liste 3 situações em que você escolheria Spark (ETL) em vez de SQL no warehouse.

## Referências

- Reis & Housley, *Fundamentals of Data Engineering* — cap. 8.
- Documentação do dbt — "What is ELT?".
