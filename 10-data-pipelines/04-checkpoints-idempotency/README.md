# Checkpoints e idempotência

> 🔵 Pipelines · Parte de [10 — Data Pipelines](../README.md)

Dois mecanismos que, juntos, permitem um pipeline **retomar** de onde parou e **reexecutar**
sem estragar dados. A idempotência já foi tratada em profundidade em
[ETL/idempotência](../../09-etl-elt/07-idempotency-retries/README.md); aqui focamos em
**checkpoints** e em como os dois se combinam no nível do pipeline.

## Checkpoints

### O que são

Um **checkpoint** salva o **progresso** de um processo para que, após uma falha, ele retome
do último ponto bom em vez de recomeçar do zero. Essencial para jobs longos (processar
bilhões de linhas) e para streaming.

```text
Sem checkpoint:  falha no item 900k de 1M  →  recomeça do item 0  (desperdício)
Com checkpoint:  falha no item 900k        →  retoma do item 800k (último checkpoint)
```

### Onde aparecem

- **Streaming** — o **offset** confirmado é o checkpoint: "já processei até aqui no
  [Kafka](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md)". Ao
  reiniciar, o consumidor retoma do último offset commitado (ver
  [delivery semantics](../../17-streaming/04-delivery-semantics/README.md)).
- **Spark Structured Streaming** — diretório de *checkpoint* guarda offsets e estado.
- **Batch longo** — marcar partições/lotes já concluídos (ex.: "dias 1–14 ok, retomar do
  15").
- **Watermark de ingestão** — a marca do último dado processado é um checkpoint (ver
  [incremental](../../09-etl-elt/05-full-vs-incremental/README.md)).

### Como implementar (batch)

Processe por **unidades** (partições/lotes) e registre quais terminaram (numa tabela de
controle, num arquivo `_SUCCESS`, ou pela existência da partição de saída). Ao reexecutar,
pule as unidades já concluídas (ou reprocesse-as — se for idempotente, tanto faz).

```text
lake/vendas/dt=2024-01-15/_SUCCESS   →  marca que o dia 15 terminou com sucesso
```

## A combinação checkpoint + idempotência

Checkpoint diz "retome daqui"; idempotência garante que "refazer uma unidade não duplica".
Juntos:

```text
falha no meio  →  retoma do último checkpoint  →  reprocessa a unidade em andamento
                  (idempotente: sem duplicar)   →  continua
```

Sem idempotência, retomar pode reprocessar parcialmente uma unidade e **duplicar**. Por isso
os dois andam juntos.

## Exactly-once prático

"Exactly-once" em streaming é alcançado combinando: **checkpoint de offsets** (não perder nem
reprocessar além do necessário) + **escrita idempotente/transacional** no destino (refazer
não duplica). Ver [delivery semantics](../../17-streaming/04-delivery-semantics/README.md).

## Checkpoint de estado (streaming stateful)

Operações com estado (agregações em janela, joins de stream) precisam **persistir o estado**
em checkpoints para sobreviver a reinícios sem perder o acumulado (ver
[stateful processing](../../17-streaming/05-stateful-processing/README.md)).

## Cuidados

- **Frequência do checkpoint** — muito frequente = overhead; muito esparso = reprocessa muito
  em falha. Equilibre.
- **Checkpoint consistente** — salve o progresso **só após** a saída estar durável (senão
  você marca "feito" algo que não foi gravado → perda de dados). A ordem é: processar →
  gravar saída → confirmar checkpoint.
- **Checkpoint corrompido/incompatível** — mudanças de código/estado podem invalidar
  checkpoints antigos (comum em Spark Streaming ao alterar a query).

## Erros comuns

- Confirmar o checkpoint **antes** de a saída estar durável → perda silenciosa de dados.
- Retomar sem idempotência → duplicação na unidade reprocessada.
- Não ter checkpoint em job longo → recomeçar do zero a cada falha.
- Alterar a lógica e reutilizar checkpoint incompatível (streaming).

## Boas práticas

- Processe por unidades reexecutáveis; marque conclusão (`_SUCCESS`/tabela de controle).
- Confirme o checkpoint **depois** da saída durável.
- Combine checkpoint com idempotência (retomar = seguro).
- Em streaming, gerencie offsets e estado com cuidado.

## Relação com outros conceitos

- [Idempotência](../../09-etl-elt/07-idempotency-retries/README.md),
  [fault tolerance](../05-fault-tolerance/README.md).
- Streaming: [offsets](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md),
  [delivery semantics](../../17-streaming/04-delivery-semantics/README.md),
  [stateful](../../17-streaming/05-stateful-processing/README.md).

## Exercícios

1. Implemente, em batch, um controle que pula partições já concluídas via arquivo
   `_SUCCESS`.
2. Explique por que confirmar o checkpoint antes de gravar a saída causa perda de dados.
3. Descreva como offset + escrita idempotente dão "exactly-once" em streaming.
4. Combine checkpoint e idempotência num cenário de falha no meio de um job de 1M de linhas.

## Referências

- Documentação do Spark Structured Streaming (checkpointing).
- Kleppmann, M. *DDIA* — cap. 11 (fault tolerance em stream).
- Documentação de offsets do Kafka.
