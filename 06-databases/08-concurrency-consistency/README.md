# Concorrência e consistência

> 🔵 Core · Parte de [06 — Databases](../README.md)

Este tópico reúne, no nível do sistema de banco, como múltiplos acessos simultâneos são
coordenados (**concorrência**) e o que diferentes nós/leituras garantem enxergar
(**consistência**). A mecânica transacional em SQL está em
[transações e isolamento](../../05-sql/08-transactions-isolation/README.md); aqui o foco
é o funcionamento interno e os modelos distribuídos.

## Concorrência: o problema

Muitos clientes leem e escrevem ao mesmo tempo. Sem coordenação, surgem anomalias
([lost update, dirty read, etc.](../../05-sql/08-transactions-isolation/README.md)). Há
duas grandes abordagens para coordenar:

### Locking (pessimista)

O recurso é **bloqueado** antes de ser alterado; outros esperam.

- Locks de leitura (compartilhados) vs escrita (exclusivos); de linha vs tabela.
- Simples, mas gera **contenção** e risco de **deadlock** (impasse mútuo — o banco aborta
  uma transação).

### MVCC (Multi-Version Concurrency Control) — o padrão moderno

Em vez de bloquear, o banco mantém **múltiplas versões** de cada linha. Leitores veem um
*snapshot* consistente; escritores criam uma nova versão. Resultado:

> **Leituras não bloqueiam escritas e escritas não bloqueiam leituras.**

É como Postgres (e InnoDB) alcançam alta concorrência. O custo: versões antigas
("tuplas mortas") precisam ser limpas — no Postgres, pelo **VACUUM**/autovacuum (se não
roda, a tabela "incha" e fica lenta).

```text
MVCC: cada transação "enxerga" o snapshot do banco no seu início/comando,
      ignorando versões criadas por transações não commitadas.
```

## Consistência: dois significados (não confunda)

A palavra "consistência" é sobrecarregada:

1. **O "C" de [ACID](../../05-sql/08-transactions-isolation/README.md)** — a transação
   respeita as regras/constraints, levando o banco de um estado válido a outro.
2. **Consistência de réplicas (distribuída)** — quão atualizada e coerente é a visão dos
   dados entre [réplicas](../07-replication/README.md). É deste que falamos aqui.

## O espectro da consistência distribuída

Do mais forte ao mais fraco:

- **Linearizability (strong)** — o sistema se comporta como se houvesse **uma única
  cópia**: toda leitura vê a escrita mais recente. Cara em latência/disponibilidade
  (exige coordenação).
- **Sequential / causal** — garante certas ordens (ex.: causa antes do efeito) sem o
  custo total da linearizabilidade.
- **Eventual** — réplicas **convergem** com o tempo; leituras podem ser antigas por um
  intervalo. Máxima disponibilidade/escala.

Garantias intermediárias úteis: **read-your-writes**, **monotonic reads**, **consistent
prefix**.

## CAP e PACELC (por que você escolhe)

Sob [partição de rede](../../01-foundations/05-distributed-systems-fundamentals/README.md),
é preciso escolher entre **Consistência** e **Disponibilidade** (CAP). PACELC acrescenta:
mesmo **sem** partição (*Else*), há trade-off entre **Latência** e **Consistência** —
consistência forte custa latência (coordenação entre nós).

```text
Sistema CP (ex.: etcd, ZooKeeper): recusa servir dado inconsistente sob partição.
Sistema AP (ex.: Cassandra, Dynamo): responde sempre, aceitando dado eventual.
```

## Consistência ajustável (tunable)

Alguns bancos (Cassandra, DynamoDB) deixam você **escolher por operação** o nível,
via quórum: com **N** réplicas, se **W** confirmam a escrita e **R** confirmam a leitura,
então `W + R > N` garante leitura consistente (há sobreposição). Você troca
consistência × latência × disponibilidade a cada chamada.

```text
N=3, W=2, R=2  → W+R=4 > 3  → leitura vê a última escrita (forte)
N=3, W=1, R=1  → W+R=2 <= 3 → rápido, mas pode ler dado velho (eventual)
```

## O ângulo de Data Engineering

- **Fontes com consistência eventual** (muitos NoSQL): "o que você extrai agora" pode não
  refletir a última escrita; cuidado em pipelines sensíveis a ordem/atualidade.
- **Idempotência** nos pipelines compensa a falta de transações globais em sistemas
  distribuídos (ver [idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Lakehouse** ([Delta/Iceberg/Hudi](../../15-lakehouse/README.md)) traz
  *snapshot isolation* e commits atômicos para object storage — consistência onde o lake
  cru não tinha.
- Entender o modelo de consistência da fonte evita conclusões erradas ("por que faltam
  registros recentes?").

## Erros comuns

- Confundir o "C" de ACID com consistência de réplicas.
- Assumir leituras fortes de um sistema eventualmente consistente.
- Esquecer o VACUUM/autovacuum (MVCC) → *bloat* e lentidão no Postgres.
- Enunciar CAP como "2 de 3" (é C vs A **sob partição**).

## Boas práticas

- Saiba a garantia de consistência de cada fonte/destino.
- Ajuste o nível (quórum/isolamento) ao requisito real, não ao máximo "por garantia".
- Projete pipelines idempotentes e tolerantes a dados tardios.
- Monitore manutenção do MVCC.

## Relação com outros conceitos

- Base: [sistemas distribuídos/CAP](../../01-foundations/05-distributed-systems-fundamentals/README.md).
- Transações em SQL: [isolamento](../../05-sql/08-transactions-isolation/README.md).
- [Replicação](../07-replication/README.md), [NoSQL](../04-nosql/README.md),
  [lakehouse ACID](../../15-lakehouse/03-acid-on-object-storage/README.md).

## Exercícios

1. Explique como o MVCC permite "leituras não bloqueiam escritas".
2. Diferencie os dois significados de "consistência" com um exemplo de cada.
3. Com N=3, escolha W e R para (a) leitura sempre consistente e (b) menor latência;
   explique o trade-off.
4. Dê um caso de pipeline que quebra se a fonte for eventualmente consistente e como
   mitigar.

## Referências

- Kleppmann, M. *DDIA* — caps. 7 e 9.
- Abadi, D. "PACELC", 2012.
- Documentação do PostgreSQL — "Concurrency Control (MVCC)".
