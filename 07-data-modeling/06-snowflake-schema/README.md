# Snowflake schema

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

O **snowflake schema** é uma variação do [star schema](../05-star-schema/README.md) em
que as **dimensões são normalizadas** em sub-tabelas, em vez de desnormalizadas numa
tabela larga. As hierarquias (ex.: produto → subcategoria → categoria) viram tabelas
separadas, ligadas por chaves — formando um padrão que lembra um floco de neve.

> Não confundir com o **Snowflake** (o data warehouse na nuvem) — são coisas totalmente
> diferentes que infelizmente compartilham o nome.

```text
Star:                           Snowflake:
fato ── dim_produto             fato ── dim_produto ── dim_subcategoria ── dim_categoria
        (nome, subcat,                  (nome, subcat_sk)   (nome, cat_sk)   (nome)
         categoria tudo junto)
```

## Por que existe

Normalizar as dimensões:

- **Reduz redundância** (o nome da categoria não se repete em milhares de produtos).
- **Facilita manutenção** de hierarquias (mudar o nome de uma categoria em um lugar).
- Economiza algum **espaço**.

## Por que geralmente NÃO se usa (o trade-off)

Os ganhos raramente compensam os custos em analytics:

- **Mais joins** por consulta → mais lento e mais complexo de escrever.
- **Menos intuitivo** para analistas e ferramentas de BI.
- A economia de espaço é **irrelevante** em dimensões (que são pequenas comparadas aos
  fatos) e em [armazenamento colunar comprimido](../../08-data-formats/08-row-vs-columnar/README.md).

Kimball recomenda **evitar** snowflaking na maioria dos casos: a redundância de dimensão
é barata e o star é mais rápido e legível.

## Quando o snowflake faz sentido

- **Dimensões gigantescas** com muita repetição e atributos de alta cardinalidade onde a
  economia é real.
- **Hierarquias compartilhadas/reutilizadas** entre várias dimensões ou que mudam com
  frequência e precisam de manutenção centralizada.
- **Outriggers** — uma forma controlada de snowflake: uma pequena dimensão referenciada
  por outra dimensão (ex.: `dim_data` referenciada dentro de `dim_cliente` para "data de
  cadastro"). Uso pontual, aceito até por Kimball.
- Alguns engines/modelos (e certas práticas com [Data Vault](../11-data-vault/README.md)
  na camada intermediária) acabam com dimensões mais normalizadas.

## Comparação

| Aspecto | Star | Snowflake |
| --- | --- | --- |
| Dimensões | desnormalizadas | normalizadas (sub-tabelas) |
| Nº de joins | menor | maior |
| Performance de consulta | melhor | pior |
| Redundância | maior | menor |
| Manutenção de hierarquia | em vários lugares | centralizada |
| Legibilidade | melhor | pior |
| Recomendação geral | **default** | exceção |

## Exemplo

```sql
-- Star: tudo em dim_produto
dim_produto(produto_sk, nome, subcategoria, categoria, marca)

-- Snowflake: hierarquia quebrada
dim_produto(produto_sk, nome, subcategoria_sk, marca)
dim_subcategoria(subcategoria_sk, nome, categoria_sk)
dim_categoria(categoria_sk, nome)
```

A consulta no snowflake precisa juntar 3 tabelas para chegar à categoria; no star, uma.

## Erros comuns

- Snowflakear "por pureza" (seguir 3NF cegamente no warehouse) e piorar performance/
  legibilidade.
- Confundir o esquema snowflake com o produto Snowflake.
- Normalizar dimensões pequenas onde não há ganho real.

## Boas práticas

- Prefira **star** por padrão.
- Use snowflake só com justificativa concreta (dimensão enorme, hierarquia reutilizada).
- Considere *outriggers* em vez de snowflake completo quando precisar referenciar uma
  sub-dimensão.

## Relação com outros conceitos

- Variação do [star schema](../05-star-schema/README.md).
- [Normalização](../02-normalization-denormalization/README.md) aplicada a dimensões.
- Hierarquias de [dimensões](../08-dimension-tables/README.md).

## Exercícios

1. Converta uma `dim_produto` star em snowflake e conte quantos joins a mais a consulta de
   "receita por categoria" passa a exigir.
2. Dê um caso em que o snowflake se justifica e outro em que não.
3. Explique o conceito de *outrigger* com um exemplo.
4. Argumente por que a economia de espaço do snowflake é pouco relevante em dimensões
   colunarizadas.

## Referências

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed. — snowflaking e outriggers.
- Kimball Group — "Snowflaking" (quando evitar).
