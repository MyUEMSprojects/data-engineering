# Transações e níveis de isolamento

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

Uma **transação** agrupa um conjunto de operações em uma unidade "tudo ou nada". Os
**níveis de isolamento** definem o quanto transações concorrentes enxergam umas às
outras. Entender isso evita corrupção de dados sob concorrência — e explica o "C" de
consistência no [CAP](../../01-foundations/05-distributed-systems-fundamentals/README.md).

## ACID

| Propriedade | Significado |
| --- | --- |
| **Atomicity** | tudo ou nada: ou todas as operações aplicam, ou nenhuma (rollback) |
| **Consistency** | a transação leva o banco de um estado válido a outro (respeita constraints) |
| **Isolation** | transações concorrentes não se corrompem (grau definido pelo isolation level) |
| **Durability** | commit confirmado sobrevive a falhas (persistido em disco/WAL) |

```sql
BEGIN;
  UPDATE contas SET saldo = saldo - 100 WHERE id = 1;
  UPDATE contas SET saldo = saldo + 100 WHERE id = 2;
COMMIT;      -- as duas aplicam juntas; ROLLBACK desfaz tudo
```

Se a segunda falhar, `ROLLBACK` garante que a primeira também não valha — o dinheiro
não "some".

## Fenômenos de concorrência (o que pode dar errado)

Quando transações rodam ao mesmo tempo, podem ocorrer anomalias:

- **Dirty read** — ler dado não commitado de outra transação (que pode sofrer
  rollback).
- **Non-repeatable read** — ler a mesma linha duas vezes e obter valores diferentes
  (outra transação a alterou e commitou no meio).
- **Phantom read** — reexecutar uma consulta de faixa e aparecerem **novas linhas**
  (outra transação inseriu).
- **Lost update** — duas transações lêem, modificam e gravam, e uma sobrescreve a
  outra.

## Os níveis de isolamento (SQL padrão)

Do mais fraco ao mais forte — cada um previne mais fenômenos, ao custo de mais
contenção:

| Nível | Dirty read | Non-repeatable | Phantom |
| --- | --- | --- | --- |
| READ UNCOMMITTED | possível | possível | possível |
| READ COMMITTED | não | possível | possível |
| REPEATABLE READ | não | não | possível* |
| SERIALIZABLE | não | não | não |

```sql
BEGIN ISOLATION LEVEL SERIALIZABLE;
  ...
COMMIT;
```

## Importante: o comportamento real varia por banco

A teoria acima é o padrão SQL; na prática cada banco implementa diferente:

- **PostgreSQL** usa **MVCC** (Multi-Version Concurrency Control): leituras não travam
  escritas e vice-versa.
  - Default: **READ COMMITTED** (cada comando vê um snapshot do início dele).
  - **REPEATABLE READ** no Postgres **também previne phantom reads** (snapshot do
    início da transação) — mais forte que o padrão.
  - **SERIALIZABLE** no Postgres usa SSI (Serializable Snapshot Isolation) e pode
    abortar transações com erro de serialização (você deve **retentar**).
- **READ UNCOMMITTED** no Postgres se comporta como READ COMMITTED (não há dirty read).
- MySQL/InnoDB tem default **REPEATABLE READ**, com semântica própria.

> Regra prática: saiba o **default do seu banco** e eleve o isolamento só onde a
> correção exigir. Em SERIALIZABLE, prepare-se para **retry** em erros de
> serialização.

## Locks

Transações usam **bloqueios** para coordenar acesso. Tipos: compartilhado (leitura) vs
exclusivo (escrita); de linha vs de tabela.

```sql
SELECT * FROM contas WHERE id = 1 FOR UPDATE;   -- trava a linha p/ update (evita lost update)
```

`SELECT ... FOR UPDATE` é a forma clássica de evitar *lost update* (lock pessimista).

### Deadlock

Duas transações esperam locks uma da outra em ordem oposta → impasse. O banco detecta e
**aborta uma** com erro. Prevenção: acesse recursos **sempre na mesma ordem** e
mantenha transações **curtas**.

## Otimista vs pessimista

- **Pessimista** — trava (`FOR UPDATE`) antes de alterar. Simples, mas contende.
- **Otimista** — não trava; detecta conflito no commit (via versão/timestamp) e
  **retenta**. Melhor sob baixa contenção (padrão em SERIALIZABLE do Postgres).

## O ângulo de Data Engineering

- **OLTP** (bancos de origem): entender isolamento importa ao escrever/consumir dados
  operacionais e ao fazer [CDC](../../09-etl-elt/06-cdc/README.md).
- **Analytics/warehouse**: transações longas analíticas se beneficiam de snapshots
  consistentes; muitos warehouses têm semântica própria (BigQuery é
  *snapshot*-based; Snowflake tem transações).
- **Idempotência vs transação**: em pipelines distribuídos nem sempre há transação
  global; você obtém "atomicidade" com escrita atômica (tmp+move),
  [idempotência](../../09-etl-elt/07-idempotency-retries/README.md) e *upserts*.
- **Lakehouse**: [Delta/Iceberg/Hudi](../../15-lakehouse/README.md) trazem ACID para
  object storage (commits atômicos de arquivos) — uma resposta ao fato de que lakes
  crus não têm transações.

## Erros comuns

- Transações longas segurando locks (bloqueiam o sistema).
- Assumir o padrão SQL em vez do default real do banco.
- Em SERIALIZABLE, não tratar erros de serialização com retry.
- Ler-modificar-gravar sem `FOR UPDATE` → *lost update*.
- Ordem inconsistente de acesso → deadlocks.

## Boas práticas

- Transações **curtas**; faça trabalho pesado fora delas.
- Eleve o isolamento só onde necessário; conheça o default do banco.
- `FOR UPDATE` ou retry otimista para read-modify-write.
- Acesse recursos em ordem consistente (anti-deadlock).

## Relação com outros conceitos

- Consistência conecta a [sistemas distribuídos/CAP](../../01-foundations/05-distributed-systems-fundamentals/README.md).
- [Constraints](../09-constraints/README.md) implementam o "C" de consistência.
- ACID sobre lake: [lakehouse](../../15-lakehouse/03-acid-on-object-storage/README.md).
- Pipelines: [idempotência](../../09-etl-elt/07-idempotency-retries/README.md).

## Exercícios

1. Escreva uma transferência entre contas atômica e explique o papel do `ROLLBACK`.
2. Para cada fenômeno (dirty/non-repeatable/phantom), diga qual nível o previne.
3. Demonstre um *lost update* e corrija com `SELECT ... FOR UPDATE`.
4. Descreva como você garantiria "atomicidade" ao gravar um lote num data lake sem
   transações (dica: tmp + move / commit do Iceberg).

## Referências

- Documentação do PostgreSQL — "Transaction Isolation", "Explicit Locking".
- Kleppmann, M. *DDIA* — cap. 7 (transações).
- Berenson et al. "A Critique of ANSI SQL Isolation Levels".
