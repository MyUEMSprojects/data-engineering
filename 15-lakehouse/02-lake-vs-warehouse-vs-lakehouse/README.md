# Lake vs Warehouse vs Lakehouse

> 🔵 Analytics Platforms · Parte de [15 — Lakehouse](../README.md)

## O que é

Uma comparação direta dos três paradigmas de plataforma analítica, para você escolher (ou combinar)
conscientemente — sem declarar um "vencedor universal", porque a resposta depende do contexto.

## Resumo em uma linha

- **[Data Warehouse](../../13-data-warehouse/README.md)** — dados **modelados e estruturados**,
  otimizados para SQL analítico; confiável, mas mais caro e inflexível.
- **[Data Lake](../../14-data-lake/README.md)** — **qualquer dado bruto**, barato e flexível; mas
  sem ACID/governança (risco de swamp).
- **[Lakehouse](../README.md)** — lake + camada transacional: a flexibilidade/custo do lake com a
  confiabilidade/performance do warehouse.

## Tabela comparativa

| Aspecto | Data Warehouse | Data Lake | Lakehouse |
| --- | --- | --- | --- |
| Storage | proprietário/colunar | [object storage](../../14-data-lake/02-object-storage/README.md) | object storage |
| Formato | fechado (geralmente) | aberto (Parquet/JSON) | **aberto** (Parquet + table format) |
| Tipos de dado | estruturado | qualquer | qualquer |
| Schema | on-write | on-read | on-write + evolution |
| ACID / transações | sim | **não** | **sim** |
| Updates/deletes/MERGE | sim | não (reescrever) | **sim** |
| Time travel | varia | não | **sim** |
| Custo de storage | maior | baixo | baixo |
| SQL analítico | ótimo | ok (via engine) | bom/ótimo |
| ML / não-estruturado | limitado | ótimo | ótimo |
| Governança/qualidade | forte | frágil (exige esforço) | forte |
| Lock-in | maior | menor | menor (formatos abertos) |
| Risco | custo/inflexibilidade | data swamp | operação/maturidade |

## Como escolher

```text
"Só analytics SQL estruturado, quero simplicidade gerenciada"   → Warehouse
"Dados brutos/variados, ML, armazenar barato, pouca necessidade de ACID" → Lake
"Quero um sistema só para BI + ML + streaming, com ACID e formatos abertos" → Lakehouse
```

Na prática, muitas organizações **combinam**:

- **Lake + Warehouse** — lake guarda bruto/ML; warehouse serve o analítico (clássico, com
  duplicação).
- **Lakehouse** — tende a unificar, reduzindo cópias (cada vez mais comum).
- **Híbrido** — lakehouse para o grosso + warehouse gerenciado para cargas SQL específicas; ou
  warehouse lendo tabelas Iceberg do lakehouse (convergência: BigQuery/Snowflake já lêem Iceberg).

## A convergência

A fronteira está borrando: warehouses passam a ler **formatos abertos** do lakehouse
([Iceberg](../05-apache-iceberg/README.md)), e lakehouses ficam mais fáceis de operar. O futuro
provável é **storage aberto único** (Iceberg/Delta) consultado por **várias engines** (Spark,
Trino, warehouses) — menos "ou/ou", mais "tudo sobre o mesmo dado aberto".

## Quando o warehouse ainda ganha

- Cargas puramente SQL, bem definidas, que valorizam zero operação de infra e tuning automático.
- Times pequenos que querem simplicidade máxima (BigQuery/Snowflake "só funcionam").

## Quando o lake cru (sem lakehouse) basta

- Zona de *landing* bruta / arquivamento barato.
- Dados não-estruturados para ML onde ACID/updates não importam.
  (Mas, para tabelas analíticas, o lakehouse quase sempre compensa sobre o lake cru.)

## Erros comuns

- Tratar como escolha ideológica ("lake é melhor que warehouse") em vez de contextual.
- Manter lake + warehouse com duplicação quando um lakehouse unificaria.
- Usar lake cru para tabelas que precisam de ACID/updates (deveria ser lakehouse).
- Adotar lakehouse complexo quando um warehouse simples resolveria.

## Boas práticas

- Escolha pelo contexto (tipo de dado, ACID, custo, operação, time).
- Prefira formatos abertos para flexibilidade futura/convergência.
- Combine quando fizer sentido; evite duplicação desnecessária.

## Relação com outros conceitos

- [Warehouse](../../13-data-warehouse/README.md), [Lake](../../14-data-lake/README.md),
  [arquitetura do lakehouse](../01-motivation-architecture/README.md).
- Formatos: [Delta](../04-delta-lake/README.md), [Iceberg](../05-apache-iceberg/README.md),
  [Hudi](../06-apache-hudi/README.md).

## Exercícios

1. Para 3 cenários (BI SQL simples; plataforma ML com dados variados; unificar BI+ML+streaming),
   recomende lake, warehouse ou lakehouse.
2. Preencha a tabela comparativa de memória e confira.
3. Explique a "convergência" (warehouses lendo Iceberg) e o que ela significa para a escolha.
4. Dê um caso em que o warehouse ainda é a melhor escolha.

## Referências

- Armbrust et al. "Lakehouse" (CIDR 2021).
- Documentação comparativa de Databricks, Snowflake, BigQuery.
