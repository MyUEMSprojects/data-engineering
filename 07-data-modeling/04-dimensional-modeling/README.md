# Modelagem dimensional

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

**Modelagem dimensional** (Ralph Kimball) é a técnica de projetar dados analíticos em
torno de **processos de negócio**, separando o que é **medido** (fatos/métricas) do que
**descreve o contexto** (dimensões). O resultado é intuitivo para analistas e rápido de
consultar — o padrão de fato dos [data warehouses](../../13-data-warehouse/README.md).

## Por que existe

Modelos normalizados (3NF) são ótimos para [OLTP](../03-oltp-vs-olap-modeling/README.md),
mas analisar neles exige muitos joins e conhecimento do schema. A modelagem dimensional
troca redundância controlada por **simplicidade e performance**: analistas entendem
"fato de vendas" + "dimensão de produto/cliente/tempo" sem precisar decifrar dezenas de
tabelas.

## Os blocos: fatos e dimensões

- **Fato (fact)** — a **medição** de um processo de negócio. Contém *métricas* numéricas
  (valor, quantidade) e *chaves estrangeiras* para dimensões. Linhas de fato são muitas
  (uma por evento). Ver [fact tables](../07-fact-tables/README.md).
- **Dimensão (dimension)** — o **contexto** ("quem, o quê, onde, quando, como"). Contém
  atributos descritivos usados para filtrar/agrupar. Poucas linhas, muitas colunas,
  desnormalizada. Ver [dimension tables](../08-dimension-tables/README.md).

```text
                 dim_data
                     │
 dim_cliente ── FATO_VENDAS ── dim_produto
                     │
                 dim_loja
```

Fatos respondem "quanto?"; dimensões respondem "por quê/como fatiar?".

## O conceito mais importante: o grão (grain)

O **grão** é o que **uma linha do fato representa**. Definir o grão é a **primeira e mais
importante** decisão — tudo depende dela.

```text
grão = "um item de um pedido"  → fato_vendas_item (produto, pedido, qtd, valor)
grão = "um pedido"             → fato_pedidos (um registro por pedido)
grão = "vendas por loja/dia"   → fato agregado (snapshot diário)
```

Regras de Kimball: **declare o grão explicitamente e mantenha todas as linhas do fato no
mesmo grão** (nunca misture granularidades). Métricas e dimensões anexadas devem ser
coerentes com o grão.

## O processo de design de Kimball (4 passos)

1. **Escolher o processo de negócio** (ex.: vendas, envios, pagamentos).
2. **Declarar o grão** (o que é uma linha do fato).
3. **Identificar as dimensões** (o contexto disponível naquele grão).
4. **Identificar os fatos/métricas** (o que se mede naquele grão).

Exemplo:

```text
1. Processo: vendas no PDV
2. Grão: um item vendido em uma transação
3. Dimensões: data, produto, loja, cliente, promoção
4. Fatos: quantidade, preço_unitário, valor_total, desconto
```

## Métricas e aditividade

Métricas de fato têm **aditividade** diferente (ver
[fact tables](../07-fact-tables/README.md)):

- **Aditivas** — somáveis em todas as dimensões (valor, quantidade).
- **Semi-aditivas** — somáveis em algumas, não em tempo (ex.: saldo — soma por conta mas
  não ao longo dos dias).
- **Não-aditivas** — não se somam (ex.: percentuais, razões — recalcule a partir dos
  componentes aditivos).

## Esquemas resultantes

- **[Star schema](../05-star-schema/README.md)** — fato central + dimensões
  desnormalizadas ao redor (o mais comum).
- **[Snowflake schema](../06-snowflake-schema/README.md)** — dimensões normalizadas em
  sub-tabelas (menos comum; mais joins).

## Dimensões conformadas (conformed) — a cola do warehouse

Dimensões **compartilhadas** entre vários fatos (ex.: a mesma `dim_produto` usada por
vendas e por devoluções). Permitem comparar/combinar processos ("*drill-across*") de
forma consistente. São a base do **data warehouse bus** de Kimball. Ver
[dimension tables](../08-dimension-tables/README.md).

## Vantagens

- Intuitivo para analistas e BI (ferramentas entendem star schema).
- Consultas rápidas (poucos joins; otimizadores têm *star schema optimization*).
- Flexível a novas perguntas sem remodelar.
- Suporta histórico via [SCD](../10-slowly-changing-dimensions/README.md).

## Limitações / trade-offs

- Redundância (desnormalização) — gerida pelo [ETL](../../09-etl-elt/README.md).
- Mudanças de grão/dimensão exigem cuidado (reprocessamento).
- Não é ideal para dados muito variáveis/semiestruturados ou integração complexa (onde
  [Data Vault](../11-data-vault/README.md) pode ajudar como camada intermediária).

## Erros comuns

- **Não declarar o grão** ou misturar granularidades no mesmo fato → somas erradas.
- Colocar medidas em dimensões ou atributos descritivos no fato.
- Fatos com chaves de negócio em vez de [surrogate keys](../09-surrogate-natural-keys/README.md).
- Dimensões não conformadas → números divergentes entre relatórios.

## Boas práticas

- Siga os 4 passos; **declare o grão** primeiro.
- Mantenha métricas aditivas quando possível; derive percentuais na consulta.
- Use surrogate keys e dimensões conformadas.
- Modele no formato que o BI/[dbt](../../28-dbt/README.md) consome bem (star).

## Relação com outros conceitos

- Concretizado em [star](../05-star-schema/README.md)/[snowflake](../06-snowflake-schema/README.md),
  com [fatos](../07-fact-tables/README.md) e [dimensões](../08-dimension-tables/README.md).
- Histórico: [SCD](../10-slowly-changing-dimensions/README.md).
- Implementado no [warehouse](../../13-data-warehouse/README.md) via
  [dbt](../../28-dbt/README.md).

## Exercícios

1. Aplique os 4 passos de Kimball a um processo de "aluguel de bicicletas" (processo,
   grão, dimensões, fatos).
2. Classifique como aditiva/semi-aditiva/não-aditiva: receita, saldo de estoque, margem
   percentual.
3. Explique por que misturar grãos no mesmo fato leva a somas erradas.
4. Dê um exemplo de dimensão conformada e o que ela permite comparar.

## Referências

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed. — caps. 1–3.
- Kimball Group — "Dimensional Modeling Techniques" (artigos oficiais).
