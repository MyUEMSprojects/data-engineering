# ACID sobre object storage

> 🔵 Analytics Platforms · Parte de [15 — Lakehouse](../README.md)

## O que é

Como oferecer garantias **[ACID](../../05-sql/08-transactions-isolation/README.md)** (atomicidade,
consistência, isolamento, durabilidade) em cima de [object storage](../../14-data-lake/02-object-storage/README.md)
— que, sozinho, **não** tem transações. É o mecanismo central que transforma um lake de arquivos
num [lakehouse](../README.md) confiável.

## Por que é difícil (o object storage não ajuda)

Object storage tem propriedades que tornam transações não-triviais (ver
[object storage](../../14-data-lake/02-object-storage/README.md)):

- **Objetos são imutáveis** — não há "update parcial"; escreve-se objetos novos.
- **Sem transação multi-arquivo** — gravar 10 Parquet não é atômico; uma falha no meio deixa estado
  parcial.
- **Listagem não é fonte confiável de "o que é a tabela"** — arquivos podem estar sendo escritos,
  órfãos, meio-prontos.

Resultado num **lake cru**: um leitor pode ver uma escrita pela metade; dois escritores se
sobrepõem; não há como "desfazer". É o que o lakehouse conserta.

## A solução: um log/manifesto transacional

A ideia central dos table formats ([Delta](../04-delta-lake/README.md),
[Iceberg](../05-apache-iceberg/README.md), [Hudi](../06-apache-hudi/README.md)): **a tabela não é
"os arquivos que existem no diretório"; a tabela é "os arquivos que o log diz que fazem parte da
versão N"**.

```text
Escrita:
  1. escreve NOVOS arquivos Parquet (ainda não "fazem parte" da tabela)
  2. faz UM commit atômico no log: "versão N+1 = versão N - arquivos X + arquivos novos"
  → leitores só veem a nova versão QUANDO o commit do passo 2 acontece (atômico)
```

- **Atomicidade** — a mudança só "existe" quando o commit no log é feito (um único ponto atômico).
  Se o passo 1 falhar, os arquivos novos ficam órfãos (ignorados), e a tabela permanece na versão
  anterior.
- **Isolamento (snapshot)** — cada leitor lê a **versão** do log que estava vigente quando começou
  → *snapshot isolation* (não vê escritas em andamento).
- **Durabilidade** — garantida pelo object storage (altamente durável).
- **Consistência** — o commit valida schema/invariantes.

## Como o commit atômico é garantido

O desafio é tornar "atualizar o log" atômico em object storage:

- **Delta** — escreve arquivos de log numerados (`000.json`, `001.json`...); a atomicidade do
  "criar o próximo número" depende de garantias do storage/serviço de coordenação (em S3, usa
  mecanismos para evitar dois writers criarem o mesmo número; em cloud gerenciada isso é resolvido).
- **Iceberg** — usa um **catálogo** (metastore/Glue/Nesse/REST) que faz um *compare-and-swap*
  atômico do ponteiro para o metadado mais recente → dois commits concorrentes, só um vence (o
  outro retenta).
- **Hudi** — timeline de commits com controle de concorrência.

A base teórica é a mesma: um **ponto único de commit** (append no log ou swap atômico do ponteiro) =
atomicidade.

## O que o ACID habilita no lakehouse

- **Upserts/MERGE/DELETE** atômicos — atualizar/deletar linhas (SCD, [CDC](../../09-etl-elt/06-cdc/README.md),
  apagar PII por [LGPD](../../26-security/08-lgpd/README.md)) reescrevendo arquivos e commitando.
- **Time travel** — cada commit é uma versão; ler versões antigas (`VERSION AS OF`) para auditoria/
  DR.
- **Leituras consistentes** durante escritas (snapshot isolation).
- **Compaction segura** — reorganizar arquivos (`OPTIMIZE`) sem quebrar leitores (é só mais um
  commit atômico).

## Controle de concorrência

- **Optimistic concurrency** — escritores assumem que não haverá conflito; no commit, verificam se
  a versão base ainda é a atual. Se outro commitou no meio, **retentam** (como
  [SERIALIZABLE otimista](../../05-sql/08-transactions-isolation/README.md)). Bom para muitas
  leituras e escritas esporádicas.
- Conflitos (dois writers mexendo nos mesmos arquivos) → um vence, o outro refaz.

## Garantias vs um banco OLTP

Lakehouse dá ACID **em nível de tabela/batch**, com *snapshot isolation* — excelente para
analytics. **Não** substitui um [banco OLTP](../../06-databases/README.md) para transações de
alta frequência, baixa latência e multi-linha concorrentes. É ACID para o mundo analítico.

## Erros comuns

- Esperar ACID de um lake **cru** (precisa de table format).
- Misturar escritas via table format com escritas "por fora" (arquivos soltos no diretório) →
  corrompe a visão transacional.
- Achar que lakehouse = OLTP (é analítico/batch, não transacional de alta frequência).
- Ignorar limpeza de versões antigas (time travel acumula storage — `VACUUM`/expire snapshots).

## Boas práticas

- Sempre escreva/leia via o table format (nunca mexa nos arquivos "por fora").
- Aproveite MERGE/DELETE para SCD/CDC/LGPD; use time travel para auditoria/recuperação.
- Gerencie retenção de versões/snapshots (custo de storage).
- Entenda a concorrência otimista (prepare-se para retries em escrita concorrente).

## Relação com outros conceitos

- [ACID/transações](../../05-sql/08-transactions-isolation/README.md),
  [object storage](../../14-data-lake/02-object-storage/README.md),
  [metadata](../../14-data-lake/07-metadata/README.md).
- Implementações: [Delta](../04-delta-lake/README.md), [Iceberg](../05-apache-iceberg/README.md),
  [Hudi](../06-apache-hudi/README.md); [DR/time travel](../../06-databases/09-backup-recovery-dr/README.md).

## Exercícios

1. Explique por que gravar 10 Parquet num lake cru não é atômico e como o log resolve.
2. Descreva o fluxo de um commit atômico (escrever arquivos → commit no log).
3. Explique snapshot isolation: como um leitor não vê uma escrita em andamento.
4. Dê 3 operações que o ACID do lakehouse habilita e um caso de uso para cada.

## Referências

- Documentação de Delta Lake (transaction log), Iceberg (spec + catalog commit), Hudi (timeline).
- Armbrust et al. "Lakehouse" (CIDR 2021); Kleppmann, *DDIA* — cap. 7.
