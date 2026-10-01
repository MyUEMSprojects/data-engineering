# Constraints

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

**Constraints** (restrições) são regras declaradas no schema que o banco **impõe
automaticamente** para garantir integridade dos dados. São a primeira linha de defesa
de qualidade: dados inválidos simplesmente não entram.

## Por que importam em DE

Garantir qualidade no ponto de entrada (*schema-on-write*) é mais barato e confiável
que descobrir lixo depois. Constraints implementam o "C" (consistência) do
[ACID](../08-transactions-isolation/README.md) e codificam o modelo de dados (chaves,
relacionamentos). Em [warehouses](../../13-data-warehouse/README.md), porém, muitas
constraints são apenas **informativas** (não impostas) — por isso os
[testes de dados](../../12-data-quality/README.md) as complementam.

## Tipos de constraint

### NOT NULL

```sql
CREATE TABLE clientes (
  id    bigint,
  nome  text NOT NULL,
  email text NOT NULL
);
```

Impede valores ausentes onde eles não fazem sentido.

### PRIMARY KEY (chave primária)

Identifica unicamente cada linha; implica `UNIQUE` + `NOT NULL` e cria um índice.

```sql
CREATE TABLE clientes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ...
);
-- chave composta:
PRIMARY KEY (pedido_id, item_id)
```

Ver [chaves naturais vs surrogate](../../07-data-modeling/09-surrogate-natural-keys/README.md).

### UNIQUE

Garante que não há valores duplicados numa coluna/conjunto.

```sql
ALTER TABLE clientes ADD CONSTRAINT uq_email UNIQUE (email);
```

(Nota: vários `NULL` são permitidos em UNIQUE no padrão/Postgres, pois `NULL ≠ NULL`.)

### FOREIGN KEY (chave estrangeira)

Garante **integridade referencial**: um valor em uma tabela deve existir em outra.

```sql
CREATE TABLE pedidos (
  id          bigint PRIMARY KEY,
  cliente_id  bigint NOT NULL REFERENCES clientes(id)
                ON DELETE RESTRICT       -- impede apagar cliente com pedidos
                ON UPDATE CASCADE,
  valor       numeric(12,2) NOT NULL
);
```

Ações referenciais: `RESTRICT`/`NO ACTION` (bloqueia), `CASCADE` (propaga),
`SET NULL`, `SET DEFAULT`. Escolha com cuidado — `CASCADE` pode apagar muita coisa.

### CHECK

Valida uma condição arbitrária por linha.

```sql
CREATE TABLE pedidos (
  valor   numeric(12,2) CHECK (valor >= 0),
  status  text CHECK (status IN ('aberto','pago','cancelado')),
  desconto numeric CHECK (desconto BETWEEN 0 AND 1)
);
```

### DEFAULT (não é constraint, mas relacionado)

```sql
criado_em timestamptz NOT NULL DEFAULT now(),
status    text        NOT NULL DEFAULT 'aberto'
```

## Nomear constraints

Dê nomes explícitos — os erros ficam legíveis e a manutenção é mais fácil:

```sql
ALTER TABLE pedidos
  ADD CONSTRAINT fk_pedidos_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id);
```

## Constraints e performance

- PK/UNIQUE criam índices (ajudam leitura, custam na escrita).
- FKs exigem verificação em cada escrita (pequeno custo, grande benefício de
  integridade).
- `CHECK`/`NOT NULL` são baratíssimas.

## O ângulo do warehouse (atenção!)

Em muitos warehouses analíticos (BigQuery, Redshift, Snowflake), constraints como PK/
FK/UNIQUE são **declarativas/informativas** — o banco **não as impõe** em runtime
(para não sacrificar performance de carga em massa). Consequência:

- Você **não pode confiar** que a PK é única só porque está declarada.
- A validação vira responsabilidade dos [testes de dados](../../12-data-quality/README.md)
  (ex.: [dbt tests](../../28-dbt/05-tests/README.md) `unique`/`not_null`/
  `relationships`).

Em bancos OLTP (Postgres/MySQL), constraints **são** impostas — confie nelas.

## Validação deferida e em massa

```sql
ALTER TABLE pedidos ADD CONSTRAINT ... NOT VALID;   -- adiciona sem checar o existente
ALTER TABLE pedidos VALIDATE CONSTRAINT ...;        -- valida depois (sem travar tanto)
SET CONSTRAINTS ALL DEFERRED;                        -- adia checagem p/ o commit
```

Útil em migrações e cargas grandes.

## Erros comuns

- Confiar em PK/UNIQUE "declaradas" num warehouse que não as impõe.
- `ON DELETE CASCADE` apagando dados em cascata inesperadamente.
- Esquecer `NOT NULL` em colunas essenciais → nulos silenciosos.
- `UNIQUE` e esperar que bloqueie múltiplos `NULL` (não bloqueia).
- Não nomear constraints → erros ilegíveis.

## Boas práticas

- Modele constraints junto com o schema (não "depois").
- Nomeie-as; escolha ações de FK conscientemente.
- Em OLTP, use constraints como garantia; em warehouse, **complemente com testes de
  dados**.
- `NOT VALID`/`DEFERRED` para migrações sem downtime.

## Relação com outros conceitos

- Implementam o modelo de [data modeling](../../07-data-modeling/README.md) (chaves,
  relacionamentos).
- Complementadas por [data quality](../../12-data-quality/README.md) e
  [data contracts](../../29-data-contracts/README.md).
- Parte do [schema-on-write](../../14-data-lake/04-schema-on-read-write/README.md).

## Exercícios

1. Modele `clientes` e `pedidos` com PK, FK (com ação apropriada), NOT NULL, UNIQUE e
   CHECK.
2. Tente inserir dados que violem cada constraint e observe os erros.
3. Explique por que, num warehouse, a PK declarada pode não impedir duplicatas — e como
   você garantiria unicidade mesmo assim.
4. Adicione uma FK a uma tabela grande sem travá-la (`NOT VALID` + `VALIDATE`).

## Referências

- Documentação do PostgreSQL — "Constraints".
- Documentação de constraints de BigQuery/Snowflake (comportamento informativo).
