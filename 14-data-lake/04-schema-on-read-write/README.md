# Schema-on-read vs schema-on-write

> 🔵 Analytics Platforms · Parte de [14 — Data Lake](../README.md)

## O que é

Duas filosofias de **quando aplicar o schema** aos dados:

- **Schema-on-write** — o schema é definido e **validado na gravação**. Dado que não conforma **não
  entra**. É o modelo dos bancos [relacionais](../../06-databases/01-relational-concepts/README.md)
  e [warehouses](../../13-data-warehouse/README.md).
- **Schema-on-read** — os dados são gravados **brutos**, sem validação; o schema é **aplicado/
  interpretado na leitura**. É o modelo clássico do [data lake](../01-concepts/README.md).

## A diferença, em uma frase

```text
Schema-on-write:  "valide agora; só dado conforme entra"      (rigor na entrada)
Schema-on-read:   "guarde tudo; descubra o schema ao ler"     (flexibilidade na entrada)
```

## Schema-on-write

- **Validação na entrada** — tipos, obrigatoriedade, constraints impostos na gravação.
- **Qualidade garantida cedo** — dado ruim é rejeitado antes de contaminar.
- **Leitura previsível** — o consumidor sabe exatamente a estrutura.
- **Custo**: menos flexível — mudanças de schema na origem precisam ser tratadas antes de gravar;
  dados que não conformam são barrados (ou exigem ajuste).

Onde: bancos relacionais, warehouses, [Avro](../../08-data-formats/05-avro/README.md) com registry,
[lakehouse](../../15-lakehouse/README.md) com *schema enforcement*.

## Schema-on-read

- **Grava qualquer coisa** — JSON variável, formatos mistos, dados crus.
- **Flexibilidade máxima** na ingestão — não precisa decidir o schema antes.
- **Custo**: o problema é **jogado para o consumidor** — ele precisa interpretar, lidar com
  variações e descobrir erros **na leitura** (tarde). Risco de [data swamp](../01-concepts/README.md).
- A estrutura pode variar entre arquivos/registros (schema implícito/inconsistente).

Onde: lakes crus de JSON/CSV; exploração de dados desconhecidos.

## Comparação

| Aspecto | Schema-on-write | Schema-on-read |
| --- | --- | --- |
| Quando valida | na escrita | na leitura |
| Flexibilidade de ingestão | baixa | alta |
| Qualidade na entrada | garantida | adiada (risco) |
| Problema de schema aparece | cedo (bloqueia) | tarde (no consumo) |
| Onde | warehouse, OLTP, Avro | lake cru |
| Risco | rigidez | data swamp |

## O trade-off central

É **rigor vs flexibilidade**, e **quando** você paga o custo da estrutura:

- On-write paga **adiantado** (esforço de modelar/validar na entrada) e colhe **confiabilidade**.
- On-read paga **depois** (todo consumidor lida com a bagunça) e colhe **flexibilidade** na
  ingestão.

## Na prática: combine com camadas (medallion)

A arquitetura moderna **usa os dois** em camadas (ver
[medallion](../03-medallion-architecture/README.md)):

```text
Bronze (schema-on-read):  grava bruto, flexível, não barra nada
   │  aplica/valida schema aqui
Silver/Gold (schema-on-write): dados tipados, validados, confiáveis
```

Você ganha a flexibilidade do on-read na entrada **e** a confiabilidade do on-write nas camadas
refinadas — aplicando o schema na transição bronze→silver (ver
[validação](../../09-etl-elt/10-data-validation/README.md),
[schema validation](../../12-data-quality/03-schema-validation/README.md)).

## O lakehouse muda o jogo

O [lakehouse](../../15-lakehouse/README.md) (Delta/Iceberg/Hudi) traz **schema enforcement** (barra
dado que não conforma) **e** **schema evolution** (evolui o schema de forma controlada) **sobre o
lake** — ou seja, schema-on-write com a economia do object storage. Reduz muito o risco de swamp.

## Erros comuns

- On-read em tudo → data swamp; consumidores lidando com caos e descobrindo erros tarde.
- On-write rígido na bronze → perde a flexibilidade de capturar dados variáveis/novos.
- Não aplicar schema em **nenhum** ponto (ninguém valida nunca).
- Confundir "formato autodescrito" ([Parquet](../../08-data-formats/04-parquet/README.md) tem
  schema embutido) com validação de negócio (são coisas diferentes).

## Boas práticas

- **On-read na ingestão** (bronze, flexível) + **on-write nas camadas refinadas** (silver/gold,
  confiável).
- Aplique schema/validação na transição bronze→silver.
- Use lakehouse para schema enforcement + evolution sobre o lake.
- Documente o schema esperado por camada ([data contracts](../../29-data-contracts/README.md)).

## Relação com outros conceitos

- [Schema validation](../../12-data-quality/03-schema-validation/README.md),
  [schema evolution](../../08-data-formats/10-schema-evolution/README.md),
  [medallion](../03-medallion-architecture/README.md).
- [Warehouse (on-write)](../../13-data-warehouse/README.md) vs
  [lake (on-read)](../01-concepts/README.md); [lakehouse](../../15-lakehouse/README.md).

## Exercícios

1. Explique o trade-off rigor vs flexibilidade com um exemplo de cada abordagem.
2. Descreva onde você aplicaria o schema numa arquitetura medallion e por quê.
3. Dê um caso em que schema-on-read é a escolha certa e outro em que on-write é.
4. Explique como o lakehouse oferece o "melhor dos dois".

## Referências

- Kleppmann, M. *DDIA* — cap. 4 (schema flexibility).
- Databricks — schema enforcement & evolution (Delta Lake).
