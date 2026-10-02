# Modelagem OLTP vs OLAP

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

O mesmo domínio de negócio é modelado de forma **oposta** dependendo da carga:

- **OLTP** (transacional) → modelo **normalizado** (3NF), otimizado para escrita e
  integridade.
- **OLAP** (analítico) → modelo **dimensional/desnormalizado**, otimizado para leitura
  analítica e clareza.

Este tópico conecta a distinção de carga ([OLTP vs OLAP](../../01-foundations/07-oltp-vs-olap/README.md))
com as decisões de modelagem ([normalização](../02-normalization-denormalization/README.md),
[dimensional](../04-dimensional-modeling/README.md)).

## Por que modelar diferente

As cargas têm perfis opostos, então as escolhas que otimizam uma penalizam a outra:

| Objetivo | OLTP | OLAP |
| --- | --- | --- |
| Operação dominante | escritas/updates pontuais | leituras analíticas em massa |
| Prioridade | integridade, escrita rápida, sem redundância | leitura rápida, simplicidade de consulta |
| Modelo | normalizado (3NF) | dimensional (star), desnormalizado |
| Nº de tabelas por consulta | muitas (joins) — ok, operação toca poucas linhas | poucas (fato + dimensões) |
| Histórico | estado atual | histórico preservado ([SCD](../10-slowly-changing-dimensions/README.md)) |
| Chaves | [naturais/negócio](../09-surrogate-natural-keys/README.md) | [surrogate](../09-surrogate-natural-keys/README.md) |

## Por que OLTP é normalizado

Um sistema transacional faz muitas escritas pequenas. Normalizar garante que cada fato
viva em um lugar só → atualizar é barato e consistente (sem
[anomalias](../02-normalization-denormalization/README.md)). Como cada transação toca
poucas linhas, os joins na leitura operacional não são problema.

## Por que OLAP é dimensional/desnormalizado

Uma consulta analítica varre milhões de linhas e junta muitas dimensões. Se o warehouse
fosse 3NF, cada pergunta exigiria dezenas de joins — lento e ilegível. Modelar em
[star schema](../05-star-schema/README.md) (fato central + dimensões largas
desnormalizadas) reduz joins, acelera e deixa o modelo **compreensível para analistas**.
A redundância é controlada pelo [ETL](../../09-etl-elt/README.md) que recria os dados.

```text
OLTP normalizado                       OLAP dimensional
clientes ── pedidos ── itens ── produtos    fato_vendas
    │                                            ├── dim_cliente (nome, uf, regiao...)
ufs ── regioes ── ...                           ├── dim_produto (nome, categoria...)
(muitas tabelas, integridade)                   └── dim_data (dia, mes, ano, feriado...)
                                           (poucas tabelas, leitura rápida)
```

## A ponte entre os dois: o Data Engineer

Mover do modelo OLTP para o OLAP é o trabalho central de DE: extrair da origem
normalizada, **transformar** e **remodelar** para o destino dimensional.

```text
Origem OLTP (3NF) ─► [ETL/ELT: limpar, juntar, desnormalizar, historizar] ─► OLAP (star)
```

Decisões típicas na ponte:

- **Grão** do fato (ver [modelagem dimensional](../04-dimensional-modeling/README.md)).
- **Surrogate keys** em vez de chaves de negócio ([chaves](../09-surrogate-natural-keys/README.md)).
- **Histórico** de dimensões ([SCD](../10-slowly-changing-dimensions/README.md)) — o OLTP
  guarda só o estado atual; o OLAP guarda a evolução.
- **Conformidade** de dimensões entre vários fatos
  ([dimensões conformadas](../08-dimension-tables/README.md)).

## Abordagens de arquitetura (Inmon vs Kimball vs Data Vault)

- **Kimball (bottom-up, dimensional)** — construir *data marts* dimensionais por processo
  de negócio, com dimensões conformadas. Pragmático e popular; foco deste módulo
  ([star](../05-star-schema/README.md)).
- **Inmon (top-down)** — um warehouse corporativo normalizado (3NF) como fonte única, do
  qual derivam data marts dimensionais. Mais rígido/robusto, mais lento de construir.
- **[Data Vault](../11-data-vault/README.md)** — camada intermediária auditável
  (hubs/links/satellites), boa para integração e histórico; alimenta marts dimensionais.

Na prática moderna (warehouse na nuvem + [dbt](../../28-dbt/README.md)), o padrão comum é:
*raw* → *staging* (limpeza) → *marts* dimensionais (Kimball), às vezes com Data Vault no
meio para integração.

## Erros comuns

- Copiar o schema OLTP (normalizado) para o warehouse e sofrer com joins.
- Desnormalizar o OLTP de produção "para facilitar relatório" (quebra a operação).
- Ignorar histórico no OLAP (perder a capacidade de analisar "como era na época").
- Misturar as duas cargas no mesmo banco.

## Boas práticas

- Normalize a origem; dimensione o destino.
- Separe fisicamente OLTP (produção) de OLAP (warehouse).
- Defina grão, chaves e estratégia de histórico ao modelar o OLAP.
- Use dimensões conformadas para consistência entre marts.

## Relação com outros conceitos

- Cargas: [OLTP vs OLAP](../../01-foundations/07-oltp-vs-olap/README.md).
- [Normalização](../02-normalization-denormalization/README.md) ⇄
  [modelagem dimensional](../04-dimensional-modeling/README.md).
- Implementado em [warehouse](../../13-data-warehouse/README.md) via
  [ETL/ELT](../../09-etl-elt/README.md)/[dbt](../../28-dbt/README.md).

## Exercícios

1. Dado um modelo OLTP de e-commerce (3NF), desenhe o modelo OLAP dimensional
   correspondente.
2. Liste 4 transformações que o ETL faz ao mover do OLTP para o OLAP.
3. Explique, com um exemplo de pergunta de negócio, por que o 3NF seria ruim no
   warehouse.
4. Compare Kimball, Inmon e Data Vault em uma frase cada.

## Referências

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed.
- Inmon, W. *Building the Data Warehouse*.
- Reis & Housley, *Fundamentals of Data Engineering* — modelagem.
