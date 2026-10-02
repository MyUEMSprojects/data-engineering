# Idempotência e retries

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

- **Idempotência** — executar uma operação **várias vezes** produz o **mesmo resultado** que
  executá-la **uma vez**. Rodar o pipeline de novo (após falha, retry ou backfill) **não**
  duplica nem corrompe dados.
- **Retries** — reexecutar automaticamente uma operação que falhou por um erro transitório.

Juntos, são a base da **confiabilidade** de pipelines. Se há **um** conceito deste módulo
para levar para a vida, é idempotência.

## Por que é essencial

Falhas são inevitáveis: rede cai, job morre no meio, uma dependência fica fora do ar. Quando
isso acontece, você **reexecuta**. Se o pipeline não for idempotente, reexecutar **duplica**
linhas, soma valores duas vezes, ou deixa estado inconsistente. Além disso,
[retries](../11-handling-failures/README.md), [backfill](../08-backfill/README.md) e
reprocessamento de [CDC](../06-cdc/README.md) **dependem** de idempotência para serem
seguros.

```text
NÃO idempotente:  rodar 2x  →  dados duplicados / somas erradas  ❌
Idempotente:      rodar N vezes  →  mesmo estado final  ✅
```

## Como tornar um pipeline idempotente

### 1. Overwrite por partição (o padrão favorito)

Reprocessar uma janela **apaga e recria só aquela partição**:

```sql
DELETE FROM fato_vendas WHERE dt = '2024-01-15';
INSERT INTO fato_vendas SELECT * FROM vendas WHERE dt = '2024-01-15';
```

Rodar 10 vezes o dia 15 → sempre o mesmo resultado. Ver
[loading](../04-loading/README.md).

### 2. Upsert / merge por chave

Inserir-ou-atualizar pela chave é idempotente por natureza (o mesmo input leva ao mesmo
estado):

```sql
INSERT INTO dim_cliente (id, nome) VALUES (...)
ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome;
```

### 3. Chaves determinísticas / dedupe

Gere IDs determinísticos (hash dos atributos) para que a mesma linha produza a mesma chave e
possa ser deduplicada (ver [dedupe](../09-deduplication/README.md),
[surrogate keys](../../07-data-modeling/09-surrogate-natural-keys/README.md)).

### 4. Escrita atômica (tudo-ou-nada)

Nunca deixe estado parcial: escreva em temporário e **mova/renomeie atômico**, ou use
[transação](../../05-sql/08-transactions-isolation/README.md)/
[lakehouse](../../15-lakehouse/README.md) (staging + swap). Ver
[loading/escrita atômica](../04-loading/README.md).

### 5. Saídas determinísticas (caminhos/nomes fixos)

A execução do dia 15 sempre grava em `.../dt=2024-01-15/` (não em um nome com timestamp
aleatório), para que reexecutar sobrescreva em vez de acumular.

## O anti-padrão: append cego

```sql
INSERT INTO fato_vendas SELECT * FROM vendas_do_dia;   -- rodar 2x = duplica!
```

Append puro **não** é idempotente. Para usá-lo com segurança, combine com
partição determinística + dedupe, ou prefira overwrite/upsert.

## Retries: fazer certo

Retentar é seguro **se** a operação for idempotente. Regras:

- **Só retente erros transitórios** (timeout, 429, 5xx, indisponibilidade). **Não** retente
  permanentes (400, 401, 404, dado inválido) — ver
  [erros e logging](../../04-python-for-data-engineering/04-errors-and-logging/README.md).
- **Exponential backoff + jitter** — espere cada vez mais, com aleatoriedade, para não
  martelar a dependência (ver [HTTP clients](../../04-python-for-data-engineering/08-http-clients/README.md)).
- **Limite de tentativas** + *dead letter* para o que falhar definitivamente.
- **Timeout** em cada tentativa.

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
@retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(initial=1, max=30))
def carregar(partition): ...
```

Orquestradores ([Airflow](../../11-orchestration/02-airflow/README.md)/Dagster/Prefect)
têm retries nativos por tarefa — mas eles só são **seguros** se a tarefa for idempotente.

## Exactly-once é idempotência disfarçada

Em sistemas distribuídos, "exactly-once" de verdade é difícil; o que se faz é
**at-least-once + idempotência** (entregar talvez mais de uma vez, mas processar de forma
que duplicatas não tenham efeito). Ver
[delivery semantics](../../17-streaming/04-delivery-semantics/README.md).

## Checklist de idempotência para uma tarefa

- [ ] Reexecutar produz o mesmo resultado?
- [ ] A saída tem caminho/chave determinística?
- [ ] Usa overwrite-por-partição ou upsert (não append cego)?
- [ ] A escrita é atômica (sem estado parcial em falha)?
- [ ] Deduplica entradas repetidas?
- [ ] Retries só em erros transitórios, com backoff e limite?

## Erros comuns

- Append cego → duplicação em retry/backfill.
- Nomes de saída com timestamp aleatório → reexecução acumula arquivos.
- Retentar erros permanentes (loop infinito, martelar a fonte).
- Backoff sem jitter → "thundering herd" (todos retentam juntos).
- Achar que o retry do orquestrador basta sem a tarefa ser idempotente.

## Boas práticas

- Projete **toda** tarefa para ser idempotente desde o início.
- Overwrite por partição / upsert / escrita atômica.
- Retries com backoff+jitter só para transitórios; dead letter para o resto.
- Teste a idempotência (rodar 2x = mesmo resultado — ver
  [testes](../../04-python-for-data-engineering/09-testing-python/README.md)).

## Relação com outros conceitos

- Base de [loading](../04-loading/README.md), [backfill](../08-backfill/README.md),
  [incremental](../05-full-vs-incremental/README.md), [CDC](../06-cdc/README.md).
- [Fault tolerance](../../10-data-pipelines/05-fault-tolerance/README.md),
  [delivery semantics](../../17-streaming/04-delivery-semantics/README.md).

## Exercícios

1. Pegue um pipeline com `INSERT ... SELECT` e torne-o idempotente (overwrite por partição).
2. Escreva um upsert idempotente e prove que rodar 3x dá o mesmo estado.
3. Implemente retries com backoff+jitter que retentam só erros transitórios.
4. Escreva um teste que roda a transformação duas vezes e verifica que não duplicou.

## Referências

- Reis & Housley, *Fundamentals of Data Engineering* — idempotência.
- Documentação do `tenacity`; retries de Airflow/Dagster.
- Kleppmann, M. *DDIA* — cap. 11 (processamento exactly-once).
