# Fact tables

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

A **tabela de fato** é o coração do modelo dimensional: armazena as **medições** de um
processo de negócio. Cada linha representa um evento no [grão](../04-dimensional-modeling/README.md)
definido, contendo **métricas** numéricas e **chaves estrangeiras** para as
[dimensões](../08-dimension-tables/README.md).

```text
fato_vendas(data_sk, produto_sk, cliente_sk, loja_sk,   -- FKs (contexto)
            quantidade, valor, desconto, custo)          -- métricas (o que se mede)
```

Características: **estreita** em colunas (chaves + medidas), **profunda** em linhas
(milhões/bilhões). É onde vive o volume do warehouse.

## Anatomia

- **Chaves estrangeiras** — surrogate keys apontando para as dimensões.
- **Métricas/medidas** — valores numéricos (aditivos de preferência).
- **Degenerate dimensions** — identificadores de negócio sem atributos próprios
  (ex.: número do pedido/nota) armazenados no próprio fato.
- **Chave do fato** — geralmente a combinação das FKs no grão (ou uma surrogate própria).

## Aditividade das métricas (conceito crucial)

Determina como você pode somar/agregar cada métrica:

| Tipo | Soma em... | Exemplo |
| --- | --- | --- |
| **Aditiva** | todas as dimensões | valor de venda, quantidade |
| **Semi-aditiva** | algumas, **não** no tempo | saldo de conta, nível de estoque |
| **Não-aditiva** | nenhuma (não some direto) | percentuais, razões, preço unitário |

Para não-aditivas, **guarde os componentes aditivos** (ex.: numerador e denominador) e
calcule a razão na consulta — somar percentuais dá resultado errado.

```sql
-- certo: margem calculada dos aditivos
SELECT SUM(valor - custo) / NULLIF(SUM(valor), 0) AS margem FROM fato_vendas;
-- errado: média de margens pré-calculadas por linha
```

## Tipos de tabela de fato

### 1. Transactional (transacional)

Uma linha por **evento** no momento em que ocorre (uma venda, um clique). Grão mais fino,
máxima flexibilidade analítica. É o tipo mais comum.

### 2. Periodic snapshot (snapshot periódico)

Uma linha por **período** capturando o estado (saldo diário, estoque no fim do dia).
Métricas tipicamente **semi-aditivas**. Bom para medir "níveis" ao longo do tempo.

### 3. Accumulating snapshot (snapshot acumulativo)

Uma linha por **processo com etapas**, atualizada conforme avança (pedido: criado →
pago → enviado → entregue, com múltiplas datas e durações). Bom para medir *lead times*
de pipelines/processos.

```text
Transacional:  1 linha por venda
Snapshot per.: 1 linha por produto por dia (estoque)
Accumulating:  1 linha por pedido, com datas de cada etapa (atualizada)
```

### Factless fact tables (fatos sem métrica)

Registram que um **evento ocorreu** sem métrica numérica (ex.: aluno matriculado em
disciplina; promoção vigente para um produto). Úteis para contar ocorrências ou
analisar cobertura/"o que não aconteceu".

## Grão: a regra de ferro

Todas as linhas de um fato **devem ter o mesmo grão** (ver
[dimensional](../04-dimensional-modeling/README.md)). Misturar grãos (ex.: linhas por
item e linhas por pedido na mesma tabela) corrompe toda agregação. Declare o grão e seja
fiel a ele.

## Modelando no warehouse

- Fatos são **particionados** (geralmente por data) para performance/retenção (ver
  [partitioning](../../13-data-warehouse/03-partitioning-clustering/README.md)).
- Carga tipicamente **append** (eventos novos) + reprocessamento por partição.
- [Colunar](../../08-data-formats/08-row-vs-columnar/README.md): como se agrega poucas
  colunas de muitas linhas, o armazenamento colunar é ideal.
- Construídos por [ETL/ELT](../../09-etl-elt/README.md)/[dbt](../../28-dbt/README.md),
  frequentemente [incrementais](../../28-dbt/08-incremental-models/README.md).

## Erros comuns

- Misturar grãos no mesmo fato.
- Guardar métricas não-aditivas (percentuais) e somá-las.
- Colocar atributos descritivos (texto) no fato em vez da dimensão.
- Esquecer *degenerate dimensions* (nº do pedido) e criar uma dimensão desnecessária.
- Usar chaves de negócio em vez de [surrogate](../09-surrogate-natural-keys/README.md) nas
  FKs.

## Boas práticas

- Declare e respeite o grão; escolha o tipo de fato pelo processo.
- Métricas aditivas; derive razões na consulta.
- FKs surrogate; degenerate dimensions no fato.
- Particione por data; carregue de forma append/incremental.

## Relação com outros conceitos

- Par das [dimensões](../08-dimension-tables/README.md) no
  [star schema](../05-star-schema/README.md).
- Grão vem da [modelagem dimensional](../04-dimensional-modeling/README.md).
- Construído via [ETL](../../09-etl-elt/README.md); usado no
  [Projeto 02](../../projects/02-analytics-warehouse/README.md).

## Exercícios

1. Para "pedidos de e-commerce", projete os três tipos de fato (transacional, snapshot
   periódico, accumulating) e diga o que cada um responde melhor.
2. Classifique a aditividade de: receita, saldo de estoque, taxa de conversão.
3. Dê um exemplo de *factless fact table* e uma pergunta que ela responde.
4. Mostre como calcular corretamente uma margem percentual a partir de métricas aditivas.

## Referências

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed. — tipos de fato,
  aditividade.
- Kimball Group — "Fact Table Techniques".
