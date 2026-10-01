# Modelagem conceitual, lógica e física

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

Modelagem de dados acontece em **três níveis de abstração**, do mais abstrato (negócio)
ao mais concreto (implementação). Separá-los evita misturar "o que o negócio precisa"
com "detalhes do banco" cedo demais.

```text
Conceitual  →  "o quê" (entidades e relacionamentos de negócio)      — sem tecnologia
     ↓
Lógico      →  "como estruturar" (tabelas, atributos, chaves, tipos) — sem SGBD específico
     ↓
Físico      →  "como implementar" (DDL, índices, partições, tipos do SGBD) — concreto
```

## Nível conceitual

Captura **entidades**, seus **atributos** e **relacionamentos**, na linguagem do
negócio, sem pensar em tecnologia. Ferramenta clássica: **diagrama ER (Entidade-
Relacionamento)**.

```text
[CLIENTE] —faz—< [PEDIDO] >—contém—< [PRODUTO]
```

Perguntas respondidas: Quais são as entidades? Como se relacionam (1:1, 1:N, N:M)? Quais
regras de negócio? É a base da conversa com *stakeholders* — ninguém precisa saber SQL
para validá-lo.

## Nível lógico

Traduz o conceitual em uma **estrutura de dados** (tabelas, colunas, chaves primárias e
estrangeiras, cardinalidades, tipos genéricos), ainda **independente** do SGBD. Aqui se
aplica [normalização](../02-normalization-denormalization/README.md) (OLTP) ou
[modelagem dimensional](../04-dimensional-modeling/README.md) (OLAP).

```text
clientes(id PK, nome, email, uf)
pedidos(id PK, cliente_id FK→clientes.id, valor, criado_em)
itens(pedido_id FK, produto_id FK, qtd)   -- resolve o N:M pedido–produto
```

Decisões típicas: resolver relacionamentos N:M com tabela associativa, escolher chaves,
definir atributos obrigatórios.

## Nível físico

Implementa o modelo lógico em um **SGBD específico**, com todas as decisões de
performance e armazenamento:

```sql
CREATE TABLE clientes (
  id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nome  text NOT NULL,
  email text UNIQUE NOT NULL,
  uf    char(2),
  criado_em timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_pedidos_cliente ON pedidos (cliente_id);
-- + particionamento, tipos do SGBD, compressão, etc.
```

Decisões físicas: tipos exatos do SGBD, [índices](../../05-sql/07-indexes/README.md),
[particionamento](../../06-databases/06-partitioning-sharding/README.md),
[constraints](../../05-sql/09-constraints/README.md), armazenamento (linha vs
[colunar](../../08-data-formats/08-row-vs-columnar/README.md)).

## Comparação

| Nível | Público | Contém | Independe de |
| --- | --- | --- | --- |
| Conceitual | negócio | entidades, relacionamentos | tudo tecnológico |
| Lógico | analistas/DEs | tabelas, colunas, chaves, tipos genéricos | SGBD |
| Físico | DEs/DBAs | DDL, índices, partições, tipos do SGBD | — |

## Por que separar

- **Comunicação** — o conceitual alinha negócio e técnica sem jargão.
- **Flexibilidade** — mudar o SGBD afeta só o físico; o lógico sobrevive.
- **Qualidade** — pensar o modelo antes de sair criando tabelas evita retrabalho e
  esquemas inconsistentes.

## O ângulo do Data Engineering

- Na prática, times ágeis frequentemente comprimem conceitual+lógico, mas o **raciocínio
  em níveis** continua valioso.
- Modelagem é também **documentação viva**; diagramas e definições alimentam o
  [catálogo/governança](../../25-data-governance/README.md).
- Em [dbt](../../28-dbt/README.md), o modelo lógico vive como código SQL + testes +
  documentação — o físico é o que o warehouse materializa.

## Erros comuns

- Pular direto para DDL (físico) sem pensar entidades/relacionamentos → esquema confuso.
- Misturar decisões físicas (índices) no modelo lógico/conceitual.
- Não documentar o conceitual → ninguém sabe o que os dados significam depois.

## Boas práticas

- Comece pelo processo de negócio e pelas perguntas que o modelo deve responder.
- Valide o conceitual com *stakeholders* antes de implementar.
- Mantenha o modelo documentado e versionado.

## Relação com outros conceitos

- Precede [normalização](../02-normalization-denormalization/README.md) e
  [modelagem dimensional](../04-dimensional-modeling/README.md).
- Nível físico usa [constraints](../../05-sql/09-constraints/README.md),
  [índices](../../05-sql/07-indexes/README.md),
  [particionamento](../../06-databases/06-partitioning-sharding/README.md).

## Exercícios

1. Para uma locadora de filmes, desenhe o modelo conceitual (entidades e
   relacionamentos).
2. Converta-o em modelo lógico, resolvendo relacionamentos N:M.
3. Implemente o modelo físico em PostgreSQL com tipos, chaves e um índice.
4. Explique o que muda em cada nível se você trocar o SGBD de Postgres para MySQL.

## Referências

- Kimball, R. *The Data Warehouse Toolkit* — modelagem.
- Documentação sobre modelagem ER; *Database Design for Mere Mortals*, Hernandez.
