# Replicação

> 🔵 Core · Parte de [06 — Databases](../README.md)

## O que é

**Replicação** é manter cópias dos mesmos dados em vários nós. Enquanto o
[particionamento](../06-partitioning-sharding/README.md) **divide** os dados, a
replicação os **copia** — para alta disponibilidade, escala de leitura e proximidade
geográfica.

## Por que existe / que problema resolve

- **Alta disponibilidade (HA)** — se um nó cai, outra réplica assume (*failover*).
- **Escala de leitura** — distribuir consultas por réplicas tira carga do primário
  (crucial para o DE: extrair/relatar de uma réplica, não da produção).
- **Latência geográfica** — réplicas próximas dos usuários.
- **Backup/analytics** — rodar jobs pesados numa réplica sem afetar o primário.

## Topologias

### Leader–follower (primary–replica) — a mais comum

```text
            escritas
  app ───────────────►  LÍDER (primary)
                           │ replica o log (WAL/binlog)
              ┌────────────┼────────────┐
              ▼            ▼             ▼
          FOLLOWER     FOLLOWER      FOLLOWER
          (leituras)   (leituras)    (standby/failover)
```

- Todas as **escritas** vão ao líder; ele envia o log de mudanças
  ([WAL](../01-relational-concepts/README.md) no Postgres, binlog no MySQL) aos
  *followers*, que o aplicam.
- **Leituras** podem ir aos followers → escala de leitura.
- No *failover*, um follower é promovido a líder.

### Multi-leader

Vários nós aceitam escrita (ex.: um por região). Melhora disponibilidade de escrita e
latência, mas gera **conflitos de escrita** a resolver (o mesmo registro alterado em
dois lugares).

### Leaderless (Dynamo-style)

Qualquer réplica aceita leitura/escrita; a consistência é obtida por **quórum** (`W + R
> N`) e reconciliação. Usado por [Cassandra](../04-nosql/03-column-family/README.md)/
DynamoDB — consistência ajustável e alta disponibilidade.

## Síncrona vs assíncrona (o trade-off central)

| | Síncrona | Assíncrona |
| --- | --- | --- |
| Confirma a escrita | só após réplica(s) confirmarem | assim que o líder grava |
| Latência de escrita | maior | menor |
| Risco de perda em falha | ~nenhum (dado já replicado) | pode perder o que não replicou |
| Disponibilidade | se a réplica trava, a escrita trava | líder segue sozinho |

Comum: **semissíncrona** — pelo menos uma réplica confirma (equilíbrio). A escolha é um
trade-off entre durabilidade e latência.

## Replication lag (o problema prático nº 1)

Na replicação assíncrona, os followers ficam **atrás** do líder por um intervalo (o
*lag*). Consequência: ler de uma réplica pode retornar **dado desatualizado**
(consistência eventual). Anomalias:

- **Read-your-writes** — o usuário escreve e, ao reler na réplica, não vê (porque ainda
  não replicou). Solução: ler do líder dados recém-escritos pelo próprio usuário.
- **Monotonic reads** — duas leituras seguidas "voltam no tempo" (réplicas diferentes com
  lags diferentes).

O DE precisa saber disso ao extrair: uma extração de uma réplica com lag alto pode
perder os registros mais recentes.

## Como se liga ao CDC

O mesmo **log de replicação** (WAL/binlog) que alimenta os followers é usado pelo
[CDC](../../09-etl-elt/06-cdc/README.md) (Debezium) para capturar mudanças e levá-las ao
lake/warehouse. Ou seja: a infraestrutura de replicação é a base da ingestão incremental
em tempo quase real. No Postgres isso aparece como **logical replication / replication
slots**.

## Replicação × Particionamento (combinados)

Sistemas em escala usam **os dois**: particionam os dados **e** replicam cada partição.
Ver [particionamento/sharding](../06-partitioning-sharding/README.md).

## O ângulo de Data Engineering

- **Extraia de réplicas de leitura**, não do primário de produção.
- Esteja ciente do **lag** ao decidir a janela/garantia de uma extração.
- Use o **log lógico** para [CDC](../../09-etl-elt/06-cdc/README.md).
- Em object storage/lake, "replicação" vira **durabilidade por redundância** embutida
  (ver [object storage](../../19-cloud/02-object-storage/README.md)) e
  *cross-region replication* para DR.

## Erros comuns

- Supor que a réplica está sempre atualizada (ignorar lag).
- Ler-após-escrever na réplica e "perder" o próprio dado (read-your-writes).
- Confundir replicação (cópias) com sharding (divisão).
- Assíncrona sem entender o risco de perda em *failover*.

## Boas práticas

- Direcione leituras analíticas para réplicas; escritas para o líder.
- Monitore o **replication lag** e defina limites aceitáveis.
- Escolha o nível de sincronia pelo trade-off durabilidade × latência.
- Use CDC via log lógico para ingestão incremental.

## Relação com outros conceitos

- [Particionamento/sharding](../06-partitioning-sharding/README.md),
  [consistência](../08-concurrency-consistency/README.md),
  [CAP](../../01-foundations/05-distributed-systems-fundamentals/README.md).
- [CDC](../../09-etl-elt/06-cdc/README.md), [backup/DR](../09-backup-recovery-dr/README.md).

## Exercícios

1. Desenhe uma topologia leader-follower e explique para onde vão leituras e escritas.
2. Explique a anomalia *read-your-writes* e como resolvê-la.
3. Compare replicação síncrona vs assíncrona em durabilidade e latência.
4. Descreva como o log de replicação habilita o CDC.

## Referências

- Kleppmann, M. *DDIA* — cap. 5 (replicação).
- Documentação do PostgreSQL — "Replication", "Logical Replication".
