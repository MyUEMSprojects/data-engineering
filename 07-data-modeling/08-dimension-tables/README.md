# Dimension tables

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

As **tabelas de dimensão** fornecem o **contexto descritivo** das medições do
[fato](../07-fact-tables/README.md): o "quem, o quê, onde, quando, como". São os atributos
pelos quais você **filtra, agrupa e rotula** relatórios. Diferente dos fatos
(estreitos e profundos), dimensões são **largas** (muitos atributos) e **rasas** (poucas
linhas).

```text
dim_cliente(cliente_sk, cliente_id, nome, cidade, uf, regiao, segmento, faixa_etaria, ...)
dim_produto(produto_sk, produto_id, nome, categoria, subcategoria, marca, ...)
dim_data(data_sk, data, dia, mes, ano, trimestre, dia_semana, feriado, ...)
```

## Por que importam tanto

A qualidade analítica de um warehouse vem **das dimensões**: são os atributos delas que
viram filtros e eixos nos dashboards. Dimensões ricas e limpas = análises poderosas.
Kimball resume: "as dimensões são a alma do data warehouse".

## Características

- **Surrogate key** como PK (ver [chaves](../09-surrogate-natural-keys/README.md)) +
  chave natural de negócio.
- **Desnormalizadas** — hierarquias achatadas numa tabela só (cidade→uf→região juntos),
  para evitar [snowflake](../06-snowflake-schema/README.md).
- **Atributos textuais e descritivos** — nomes legíveis, não códigos (`'Região Sul'`, não
  `3`).
- **Baixo volume** — mesmo "grandes" dimensões (milhões de clientes) são pequenas perto
  dos fatos.

## A dimensão de data (sempre presente)

Quase todo warehouse tem uma `dim_data` pré-populada com um atributo por "forma de ver o
tempo": dia, mês, ano, trimestre, semana, dia da semana, feriado, dia útil, etc. Isso
evita calcular isso em toda query e permite análises de calendário ricas.

```sql
SELECT ano, trimestre, SUM(f.valor)
FROM fato_vendas f JOIN dim_data d ON d.data_sk = f.data_sk
WHERE d.feriado = false
GROUP BY ano, trimestre;
```

## Hierarquias

Dimensões contêm hierarquias de *drill-down*: produto (marca → categoria →
subcategoria), geografia (país → estado → cidade), tempo (ano → trimestre → mês → dia).
No star, elas ficam **na mesma tabela** (desnormalizadas); no snowflake, separadas.

## Dimensões conformadas (conformed dimensions)

Dimensões **compartilhadas** por vários fatos (a mesma `dim_produto` em vendas, estoque e
devoluções). São a base do **bus architecture** de Kimball: permitem *drill-across*
(combinar processos diferentes) com consistência garantida ("produto" significa a mesma
coisa em todo lugar). Construí-las e mantê-las conformes é um trabalho central do DE.

## Tipos especiais de dimensão

- **[Slowly Changing Dimensions (SCD)](../10-slowly-changing-dimensions/README.md)** —
  como tratar mudanças de atributos ao longo do tempo (o tópico seguinte).
- **Role-playing** — a mesma dimensão usada em papéis diferentes (uma `dim_data` como
  "data do pedido" e "data de entrega"); resolvida com views/aliases.
- **Degenerate** — identificador de negócio que fica no fato, sem tabela própria (nº do
  pedido).
- **Junk dimension** — agrupa *flags* e indicadores de baixa cardinalidade (sim/não,
  tipo de pagamento) numa dimensão só, em vez de poluir o fato.
- **Mini dimension** — separa atributos que mudam rápido (ex.: faixas demográficas) de
  uma dimensão grande e estável.
- **Outrigger** — pequena dimensão referenciada por outra (ver
  [snowflake](../06-snowflake-schema/README.md)).
- **Dimensão "desconhecido"** — linha especial (sk = -1) para FKs ausentes/nulas no fato,
  evitando perder linhas em joins.

## Boas práticas de atributos

- Prefira **valores descritivos legíveis** a códigos (ferramentas de BI mostram direto).
- Nada de nulos em atributos usados para filtrar — use "N/A"/"Desconhecido".
- Documente o significado de cada atributo (vira [metadado/catálogo](../../27-data-catalog-metadata/README.md)).
- Padronize valores (ex.: UF sempre em 2 letras maiúsculas) na transformação.

## Erros comuns

- Dimensões pobres (só código, sem atributos descritivos) → análises limitadas.
- Não conformar dimensões → números divergentes entre relatórios.
- Nulos em atributos de filtro → linhas somem ou grupos "em branco".
- Não tratar mudanças de atributo (ver [SCD](../10-slowly-changing-dimensions/README.md))
  → histórico incorreto.
- Poluir o fato com muitos *flags* em vez de uma junk dimension.

## Boas práticas (resumo)

- Surrogate key + natural key; desnormalize hierarquias.
- Atributos ricos, legíveis, padronizados, sem nulos de filtro.
- Dimensões conformadas e uma linha "desconhecido".
- Escolha o tipo especial certo (junk, role-playing, mini) conforme o caso.

## Relação com outros conceitos

- Par dos [fatos](../07-fact-tables/README.md) no [star schema](../05-star-schema/README.md).
- [Chaves](../09-surrogate-natural-keys/README.md) e [SCD](../10-slowly-changing-dimensions/README.md).
- Alimenta [catálogo/governança](../../25-data-governance/README.md).

## Exercícios

1. Projete uma `dim_cliente` rica (com hierarquia geográfica e atributos de segmentação).
2. Monte uma `dim_data` com ao menos 8 atributos de calendário.
3. Dê um exemplo de dimensão conformada e explique o que ela habilita (*drill-across*).
4. Crie uma *junk dimension* para 3 flags booleanos de um pedido.

## Referências

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed. — dimensões.
- Kimball Group — "Dimension Table Techniques".
