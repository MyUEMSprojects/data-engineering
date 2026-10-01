# Star schema

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

O **star schema** (esquema estrela) é a materialização mais comum da
[modelagem dimensional](../04-dimensional-modeling/README.md): uma **tabela de fato**
central conectada a várias **tabelas de dimensão** desnormalizadas. Visualmente, o fato
no meio com as dimensões ao redor formam uma "estrela".

```text
          dim_data
             │
 dim_cliente ─ fato_vendas ─ dim_produto
             │
          dim_loja
```

## Por que "estrela"

Cada dimensão é uma tabela única e **larga** (desnormalizada) ligada diretamente ao fato
por uma [surrogate key](../09-surrogate-natural-keys/README.md). Não há sub-tabelas de
dimensão (isso seria [snowflake](../06-snowflake-schema/README.md)). Isso minimiza joins:
toda consulta é "fato + as dimensões que preciso".

## Exemplo completo

```sql
-- Dimensões (desnormalizadas, largas, surrogate key)
CREATE TABLE dim_data (
  data_sk    int PRIMARY KEY,          -- surrogate (ex.: 20240115)
  data       date,
  dia, mes, ano, trimestre int,
  dia_semana text, feriado boolean
);
CREATE TABLE dim_produto (
  produto_sk bigint PRIMARY KEY,
  produto_id text,                     -- chave natural de negócio
  nome, categoria, subcategoria, marca text
);
CREATE TABLE dim_cliente (
  cliente_sk bigint PRIMARY KEY,
  cliente_id text,
  nome, cidade, uf, regiao, segmento text
);

-- Fato (grão: um item vendido)
CREATE TABLE fato_vendas (
  data_sk    int    REFERENCES dim_data(data_sk),
  produto_sk bigint REFERENCES dim_produto(produto_sk),
  cliente_sk bigint REFERENCES dim_cliente(cliente_sk),
  quantidade int,
  valor      numeric(12,2),            -- métricas aditivas
  desconto   numeric(12,2)
);
```

Consulta típica (simples e rápida):

```sql
SELECT d.ano, d.mes, p.categoria, SUM(f.valor) AS receita
FROM fato_vendas f
JOIN dim_data d    ON d.data_sk = f.data_sk
JOIN dim_produto p ON p.produto_sk = f.produto_sk
WHERE c.regiao = 'Sul'       -- após join com dim_cliente
GROUP BY d.ano, d.mes, p.categoria;
```

## Por que o star schema é rápido e popular

- **Poucos joins** — fato + dimensões diretas (nunca dimensão→dimensão).
- **Otimização nativa** — bancos/warehouses têm *star schema optimization* (reconhecem o
  padrão e otimizam).
- **Intuitivo** — ferramentas de [BI](../../13-data-warehouse/README.md) mapeiam
  diretamente para star; analistas entendem "métricas por dimensões".
- **Flexível** — novas perguntas = novas combinações de dimensões, sem remodelar.

## Anatomia

- **Fato**: estreito em colunas (chaves + métricas), **profundo** em linhas (milhões).
- **Dimensão**: **larga** em colunas (muitos atributos descritivos), rasa em linhas.
- Ligação: FK do fato → PK (surrogate) da dimensão.

## Decisões de design

1. **Grão do fato** (ver [dimensional](../04-dimensional-modeling/README.md)) — primeiro
   e mais importante.
2. **Surrogate keys** nas dimensões (desacopla de chaves de negócio, suporta
   [SCD](../10-slowly-changing-dimensions/README.md)).
3. **Desnormalizar** hierarquias dentro da dimensão (cidade→uf→região numa tabela só).
4. **Dimensões conformadas** reutilizadas entre fatos.
5. Tratar nulos de FK com uma linha "desconhecido" na dimensão (evita perder linhas de
   fato em joins).

## Star vs Snowflake

| | Star | [Snowflake](../06-snowflake-schema/README.md) |
| --- | --- | --- |
| Dimensões | desnormalizadas (1 tabela) | normalizadas (sub-tabelas) |
| Joins | menos | mais |
| Performance de leitura | melhor | pior (mais joins) |
| Redundância | maior | menor |
| Legibilidade p/ analista | melhor | pior |

Na prática, **star é o default**; snowflake só em casos específicos.

## Erros comuns

- Ligar dimensão a dimensão (vira snowflake acidental ou pior).
- Misturar grãos no fato.
- Usar chave de negócio no fato em vez de surrogate (quebra SCD).
- Perder linhas de fato por FK nula (sem linha "desconhecido" na dimensão).
- Métricas não-aditivas armazenadas como se fossem somáveis.

## Boas práticas

- Declare o grão; mantenha o fato no mesmo grão.
- Surrogate keys + dimensões conformadas.
- Desnormalize hierarquias na dimensão.
- Linha "N/A"/"desconhecido" em cada dimensão para FKs ausentes.
- Métricas aditivas no fato; derive razões na consulta.

## Relação com outros conceitos

- É a forma de [modelagem dimensional](../04-dimensional-modeling/README.md).
- Usa [fatos](../07-fact-tables/README.md), [dimensões](../08-dimension-tables/README.md),
  [surrogate keys](../09-surrogate-natural-keys/README.md), [SCD](../10-slowly-changing-dimensions/README.md).
- Implementado no [warehouse](../../13-data-warehouse/README.md)/[dbt](../../28-dbt/README.md)
  e usado no [Projeto 02](../../projects/02-analytics-warehouse/README.md).

## Exercícios

1. Projete um star schema para "vendas de uma rede de lojas" (fato + 4 dimensões),
   declarando o grão.
2. Escreva uma query de "receita por categoria e trimestre" sobre ele.
3. Explique por que não se liga `dim_produto` a uma `dim_categoria` separada em um star.
4. Adicione a linha "desconhecido" numa dimensão e mostre como ela evita perder linhas de
   fato.

## Referências

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed.
- Kimball Group — "Star Schema" techniques.
