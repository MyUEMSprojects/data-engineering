# OLTP vs OLAP

> 🟢 Foundations · Parte de [01 — Fundamentos](../README.md)

## O que é

Duas classes de carga de trabalho sobre dados, que levam a sistemas projetados de
formas opostas:

- **OLTP (Online Transaction Processing)** — processamento transacional. Muitas
  operações pequenas e rápidas que *rodam o negócio*: inserir um pedido, debitar
  um saldo, atualizar um perfil.
- **OLAP (Online Analytical Processing)** — processamento analítico. Poucas
  consultas grandes que *entendem o negócio*: "faturamento por categoria e região
  nos últimos 24 meses".

Entender essa divisão é pré-requisito para quase tudo em DE: é a razão de existir
[warehouses](../../13-data-warehouse/README.md),
[formatos colunares](../../08-data-formats/08-row-vs-columnar/README.md) e
[modelagem dimensional](../../07-data-modeling/04-dimensional-modeling/README.md).

## Por que não usar o mesmo banco para os dois

As cargas têm perfis de acesso **opostos**:

- OLTP lê/escreve **poucas linhas inteiras** por operação, com altíssima
  concorrência e baixa latência. Otimiza para **escritas e buscas pontuais**.
- OLAP lê **poucas colunas de milhões de linhas** por consulta, varrendo grandes
  volumes. Otimiza para **leitura analítica em massa**.

Rodar analytics pesado em um banco OLTP de produção o sobrecarrega (e pode
derrubar o sistema que atende clientes). Rodar transações em um sistema OLAP é
inviável (não é feito para escritas pontuais frequentes). Daí a necessidade de
**mover** dados do OLTP para o OLAP — o trabalho central do Data Engineer.

## Comparação

| Aspecto | OLTP | OLAP |
| --- | --- | --- |
| Objetivo | Operar o negócio | Analisar o negócio |
| Operações | INSERT/UPDATE/DELETE pontuais | SELECT agregados em massa |
| Nº de linhas por operação | Poucas | Milhões |
| Nº de colunas lidas | Muitas (linha inteira) | Poucas |
| Concorrência | Altíssima (muitos usuários) | Baixa (analistas/jobs) |
| Latência alvo | ms | segundos a minutos |
| Modelagem | [Normalizada](../../07-data-modeling/02-normalization-denormalization/README.md) (3NF) | [Dimensional](../../07-data-modeling/04-dimensional-modeling/README.md) / desnormalizada |
| Armazenamento | [Orientado a linha](../../08-data-formats/08-row-vs-columnar/README.md) | Orientado a coluna |
| Dados | Atuais, mutáveis | Históricos, append-only |
| Exemplos | PostgreSQL, MySQL | BigQuery, Snowflake, Redshift |

## Por que row-based vs columnar

Essa é a implicação técnica mais importante:

- **OLTP** guarda cada linha junta (row-based). Buscar/atualizar um pedido inteiro
  é eficiente — tudo está contíguo.
- **OLAP** guarda cada coluna junta (columnar). Para "somar `valor` de 1 bilhão de
  linhas", lê-se só a coluna `valor`, ignorando as demais → muito menos I/O, e a
  compressão é melhor (valores semelhantes juntos). Detalhes em
  [row vs columnar](../../08-data-formats/08-row-vs-columnar/README.md).

```text
Row-based (OLTP):  [id,nome,valor][id,nome,valor][id,nome,valor] ...
                   bom para "me dê o pedido 42 inteiro"

Columnar (OLAP):   [id,id,id,...][nome,nome,...][valor,valor,...]
                   bom para "some valor de todos os pedidos"
```

## Como se conectam: o papel do Data Engineer

```text
   OLTP (produção)                    OLAP (analytics)
 ┌───────────────┐   ingestão      ┌──────────────────┐
 │ Postgres/MySQL│──(batch/CDC)──► │ Lake / Warehouse │──► BI, ML
 │ (apps)        │                 │ (colunar)        │
 └───────────────┘                 └──────────────────┘
          ▲                                  ▲
    Backend Engineer                   Data Engineer
```

O DE extrai dados do OLTP sem impactar a produção (ex.: réplicas de leitura,
[CDC](../../09-etl-elt/06-cdc/README.md)), e os carrega modelados no OLAP.

## HTAP: borrando a fronteira

Alguns sistemas modernos tentam servir as duas cargas (*Hybrid Transactional/
Analytical Processing* — ex.: TiDB, SingleStore) ou oferecem réplicas colunares
sobre o OLTP. Útil em nichos, mas a separação OLTP/OLAP segue sendo o padrão
dominante por simplicidade e custo.

## Erros comuns

- Rodar relatórios pesados direto no banco de produção OLTP.
- Modelar o warehouse igual ao banco OLTP (normalizado demais) — perde
  performance analítica. Ver [modelagem dimensional](../../07-data-modeling/04-dimensional-modeling/README.md).
- Confundir OLAP (carga) com *data warehouse* (sistema): o warehouse é uma
  *implementação* de um sistema OLAP.

## Relação com outros conceitos

- Motiva [warehouse](../../13-data-warehouse/README.md),
  [formatos colunares](../../08-data-formats/04-parquet/README.md) e
  [modelagem](../../07-data-modeling/03-oltp-vs-olap-modeling/README.md).
- A movimentação OLTP→OLAP é o tema de [ETL/ELT](../../09-etl-elt/README.md) e
  [CDC](../../09-etl-elt/06-cdc/README.md).

## Exercícios

1. **Classificação.** Para cada consulta, diga se é OLTP ou OLAP: (a) "atualizar o
   endereço do cliente 123"; (b) "ticket médio por mês e canal no último ano";
   (c) "inserir item no carrinho".
2. **Performance.** Explique, em termos de I/O, por que somar uma coluna de 1
   bilhão de linhas é muito mais barato em armazenamento colunar.
3. **Arquitetura.** Proponha como extrair dados de um Postgres de produção para
   analytics sem degradar a performance do app.

## Referências

- Kleppmann, M. *Designing Data-Intensive Applications*. O'Reilly, 2017 — cap. 3
  ("Transaction Processing or Analytics?").
- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*. Wiley, 2013 — cap. 1.
