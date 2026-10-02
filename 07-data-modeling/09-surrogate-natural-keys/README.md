# Surrogate vs natural keys

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

Toda tabela precisa de uma **chave** que identifica unicamente cada linha. Há dois tipos:

- **Natural key (chave natural/de negócio)** — um identificador que já existe no mundo
  real: CPF, e-mail, código do produto (SKU), ISBN.
- **Surrogate key (chave substituta)** — um identificador **artificial**, sem significado
  de negócio, gerado pelo sistema: um inteiro sequencial ou um UUID.

Em modelagem dimensional, a regra é clara: **dimensões usam surrogate keys como PK**,
guardando a natural key como atributo.

## Por que surrogate keys em dimensões (as razões)

1. **Suporte a [SCD](../10-slowly-changing-dimensions/README.md)** — a razão nº 1. Para
   historizar mudanças (ex.: cliente mudou de região), você precisa de **várias versões
   da mesma entidade de negócio**. Com surrogate key, cada versão é uma linha com sk
   diferente, mas a mesma natural key. Com natural key como PK, isso seria impossível (PK
   duplicada).

```text
cliente_sk | cliente_id | regiao | valido_de  | valido_ate
    100     |   C-7      | Sul    | 2020-01-01 | 2023-06-30   -- versão antiga
    250     |   C-7      | Sudeste| 2023-07-01 | 9999-12-31   -- versão atual
```

1. **Estabilidade** — chaves de negócio mudam ou são reutilizadas; a surrogate nunca
   muda.
2. **Performance** — inteiros pequenos como FK no [fato](../07-fact-tables/README.md) são
   mais rápidos e compactos que chaves naturais (strings/compostas).
3. **Integração** — unifica entidades de múltiplas fontes que usam identificadores
   diferentes.
4. **Isolamento** — o fato não depende de mudanças/formatos das chaves de origem.

## Problemas de usar natural keys como PK

- Podem **mudar** (empresa muda de CNPJ; produto é recadastrado).
- Podem ser **reutilizadas** (um código liberado e atribuído a outra coisa).
- Podem ser **compostas/grandes** (lenta como FK no fato).
- Vêm de **fontes diferentes** com formatos incompatíveis.
- **Impedem SCD** (não dá para ter duas versões com a mesma PK).

Natural keys **ainda são guardadas** na dimensão (como atributo) — são essenciais para
fazer o *lookup* durante a carga e para rastreabilidade à origem.

## Como gerar surrogate keys

- **Sequência/identidade** do banco (`GENERATED ALWAYS AS IDENTITY`, `SERIAL`) — comum em
  bancos.
- **Hash** de atributos (ex.: `md5(natural_key || valido_de)`) — determinístico, útil em
  pipelines distribuídos/[dbt](../../28-dbt/README.md) (não precisa de coordenação central
  para gerar o mesmo valor).
- **UUID** — único globalmente, bom em sistemas distribuídos, porém maior.

Em warehouses sem sequência global eficiente, **surrogate keys por hash** (determinísticas)
são muito usadas em dbt.

## Chaves no fato

As FKs do fato apontam para as **surrogate keys** das dimensões (não para as naturais).
Durante a carga do fato, você faz o *lookup* da natural key → surrogate key vigente
(respeitando o SCD, para pegar a versão correta na época do evento).

## Degenerate keys (caso especial)

Identificadores de negócio que ficam **no fato** sem dimensão própria (nº do pedido/nota)
— "degenerate dimensions". Não são surrogate nem viram tabela; servem para rastrear/
agrupar transações. Ver [fact tables](../07-fact-tables/README.md).

## Quando natural key basta

- Em **OLTP** normalizado, chaves naturais estáveis podem ser PK (ou, muitas vezes,
  usa-se surrogate mesmo assim por simplicidade).
- Dimensões de **data** frequentemente usam uma "surrogate inteligente" tipo `20240115`
  (legível e ordenável) — exceção aceita.

## Erros comuns

- Usar natural key como PK de dimensão e ficar **sem como historizar** (SCD impossível).
- FK do fato apontando para natural key (lenta, frágil).
- Surrogate key com significado de negócio embutido (perde a vantagem do isolamento) —
  exceto a dim_data.
- Perder a natural key (sem como fazer lookup/rastrear à origem).

## Boas práticas

- Dimensões: **surrogate key como PK + natural key como atributo**.
- Fatos: FKs apontando para surrogate keys.
- Gere surrogate por sequência (banco) ou hash determinístico (pipelines/dbt).
- Preserve a natural key para lookup e lineage.

## Relação com outros conceitos

- Habilita [SCD](../10-slowly-changing-dimensions/README.md).
- Usada em [dimensões](../08-dimension-tables/README.md) e
  [fatos](../07-fact-tables/README.md) do [star](../05-star-schema/README.md).
- Implementação em [dbt](../../28-dbt/README.md) (hash surrogate keys) /
  [constraints](../../05-sql/09-constraints/README.md).

## Exercícios

1. Explique, com o exemplo de um cliente que muda de região, por que surrogate key é
   necessária para SCD tipo 2.
2. Liste 4 problemas de usar CPF como PK de uma dimensão de clientes.
3. Gere uma surrogate key determinística por hash para `(natural_key, valido_de)` e diga
   por que isso ajuda em pipelines distribuídos.
4. Mostre como o fato faz o lookup da surrogate correta na carga.

## Referências

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed. — surrogate keys.
- Documentação do dbt — `dbt_utils.generate_surrogate_key`.
