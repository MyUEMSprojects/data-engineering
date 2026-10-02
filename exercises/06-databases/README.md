# Exercícios — Módulo 06: Bancos de dados

Teoria em [06-databases](../../06-databases/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Propriedades ACID

Dê um exemplo concreto de violação de cada propriedade **A, C, I, D** numa transferência bancária de A para B.

<details><summary>Gabarito</summary>

**A**tomicidade: debita A e o sistema cai antes de creditar B → dinheiro some. **C**onsistência: a transferência deixa A com saldo negativo violando uma constraint de negócio. **I**solamento: duas transferências concorrentes de A leem o mesmo saldo e ambas aprovam (*lost update*). **D**urabilidade: confirma ao cliente e o servidor reinicia sem ter gravado em disco (WAL não *flushed*).
</details>

## 2. 🟢 Conceitual — Quando usar NoSQL?

Associe: (a) carrinho de compras com acesso por chave e TTL; (b) catálogo de produtos com atributos muito variáveis; (c) rede de amizades e "amigos de amigos"; (d) métricas de sensores por série temporal. Tipos: chave-valor, documento, grafo, colunar/séries temporais.

<details><summary>Gabarito</summary>

(a) **chave-valor** (Redis/DynamoDB). (b) **documento** (MongoDB). (c) **grafo** (Neo4j). (d) **série temporal/colunar** (TimescaleDB, ClickHouse). Escolha pelo **padrão de acesso**, não pela moda. Ver [NoSQL](../../06-databases/04-nosql/README.md).
</details>

## 3. 🔵 SQL — Índice que não é usado

`CREATE INDEX ON orders (customer_id);` existe, mas `SELECT * FROM orders WHERE lower(email) = 'a@b.com'` faz *seq scan*. Por quê e como resolver? E por que `WHERE customer_id::text = '10'` também ignora o índice?

<details><summary>Gabarito</summary>

O índice é sobre `customer_id`, não sobre a **expressão** `lower(email)`. Crie `CREATE INDEX ON orders (lower(email));` (índice funcional) ou normalize o dado. Aplicar **função/cast na coluna** no `WHERE` impede o uso do índice comum — mova a conversão para o literal (`WHERE customer_id = 10`).
Sempre confirme com `EXPLAIN (ANALYZE)`. Ver [indexação](../../06-databases/05-indexing/README.md) e [EXPLAIN](../../05-sql/10-query-planning-explain/README.md).
</details>

## 4. 🔵 Debugging — Lost update

Duas sessões executam em `READ COMMITTED`: `SELECT stock FROM items WHERE id=1;` (ambas leem 5) e `UPDATE items SET stock = 4 WHERE id=1;`. Estoque final 4 em vez de 3. Corrija de **três** formas.

<details><summary>Gabarito</summary>

(1) **Atualização atômica no banco**: `UPDATE items SET stock = stock - 1 WHERE id=1 AND stock > 0;` (verifique `rowcount`). (2) **Bloqueio pessimista**: `SELECT ... FOR UPDATE` dentro da transação. (3) **Otimista**: coluna `version` e `UPDATE ... WHERE id=1 AND version = :v`, repetindo se `rowcount = 0`. Ou isolamento `SERIALIZABLE` com retry. Ver [concorrência](../../06-databases/08-concurrency-consistency/README.md).
</details>

## 5. 🟣 Arquitetura — Replicação e leitura

Um relatório pesado derruba o banco OLTP. Proponha uma solução com **réplica de leitura**, explique o **atraso de replicação** e uma consequência para a aplicação (*read-your-writes*).

<details><summary>Gabarito</summary>

Aponte o relatório para uma **réplica de leitura** (streaming replication assíncrona). O atraso (*lag*) significa que o dado recém-gravado pode **ainda não aparecer** na réplica → usuário grava e não vê. Mitigações: ler do primário logo após escrever (sessão "sticky"), esperar o LSN, ou aceitar consistência eventual para o relatório. Para analytics pesado de verdade: **CDC → warehouse**, não réplica. Ver [replicação](../../06-databases/07-replication/README.md).
</details>

## 6. 🟣 Arquitetura — RPO e RTO

O negócio exige **RPO = 5 min** e **RTO = 30 min** para o banco de pedidos. Que combinação de backup, WAL e replicação atende? Como **provar** que atende?

<details><summary>Gabarito</summary>

RPO 5 min ⇒ arquivar **WAL continuamente** (PITR) e/ou réplica síncrona/quase síncrona; backup base diário. RTO 30 min ⇒ **réplica quente com failover** automatizado (ou restauração testada que caiba em 30 min — raramente cabe em bancos grandes). **Prova:** *drills* periódicos de restauração cronometrados e verificação de integridade; backup que nunca foi restaurado **não é backup**. Ver [backup e DR](../../06-databases/09-backup-recovery-dr/README.md).
</details>
