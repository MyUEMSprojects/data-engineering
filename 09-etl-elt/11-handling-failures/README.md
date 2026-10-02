# Tratamento de falhas

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

Projetar o pipeline para **falhar bem**: detectar o erro, não corromper dados, recuperar
automaticamente quando possível e alertar quando não. Falhas são inevitáveis; a diferença
entre um pipeline amador e um profissional é **como ele falha**.

## Princípio central: falhar é melhor que corromper

Diante de um problema, a pior saída é "continuar e gravar lixo". Prefira **parar** (ou
quarentenar) a propagar dados errados silenciosamente. Um job que falha visivelmente é
recuperável; dados errados que passam despercebidos custam meses de confiança.

## Tipos de falha (e a resposta certa)

| Tipo | Exemplo | Resposta |
| --- | --- | --- |
| **Transitória** | timeout, 429, DB momentaneamente fora | [retry com backoff](../07-idempotency-retries/README.md) |
| **Permanente** | credencial inválida, 404, bug | falhar + alertar (retry não ajuda) |
| **Dado inválido** | schema mudou, valor impossível | [validar](../10-data-validation/README.md): bloquear/quarentenar |
| **Parcial** | job morreu no meio da carga | escrita atômica + reexecutar (idempotente) |
| **Upstream** | fonte atrasada/indisponível | esperar/sensor, SLA, alerta |

Distinguir transitório de permanente é essencial — ver
[erros e logging](../../04-python-for-data-engineering/04-errors-and-logging/README.md).

## Mecanismos de resiliência

### Retries (para transitórios)

Exponential backoff + jitter, limite de tentativas, timeout por tentativa. **Só funciona com
tarefas [idempotentes](../07-idempotency-retries/README.md).** Orquestradores dão retries
nativos por tarefa.

### Escrita atômica (para falhas parciais)

Nunca deixe estado parcial: tmp + move, transação, ou staging + swap (ver
[loading](../04-loading/README.md)). Se o job morre no meio, a reexecução recomeça limpo.

### Checkpoints (para jobs longos)

Salvar progresso para retomar de onde parou, em vez de recomeçar do zero (ver
[checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md)). Em streaming,
são os offsets confirmados.

### Dead Letter Queue / quarentena (para dados ruins)

Registros que falham repetidamente vão para uma fila/tabela separada (*dead letter*), para
análise posterior, sem travar o fluxo bom. Ver [validação](../10-data-validation/README.md).

### Circuit breaker

Se a taxa de erro ultrapassa um limite, pare de tentar (evita martelar uma dependência
quebrada) e alerte.

### Timeouts

Toda operação externa (HTTP, DB) precisa de timeout — sem ele, uma dependência travada
pendura o pipeline indefinidamente.

## Idempotência: o alicerce

Quase todo tratamento de falha (retry, reexecução, backfill) **depende** de o pipeline ser
idempotente — reexecutar não pode duplicar/corromper. Ver
[idempotência](../07-idempotency-retries/README.md). Esse é o pré-requisito de tudo aqui.

## Alertas e observabilidade

Falhar silenciosamente é quase tão ruim quanto corromper. O pipeline deve:

- **Logar** com contexto suficiente para diagnosticar (ver
  [logging](../../04-python-for-data-engineering/04-errors-and-logging/README.md)).
- **Alertar** os responsáveis em falhas (e em degradações: atraso, volume anômalo).
- Expor **métricas** (sucesso/falha, duração, linhas) — ver
  [observabilidade](../../24-observability/README.md).

Evite "alert fatigue": alerte no que é acionável; agrupe/priorize.

## Graceful degradation

Quando possível, degrade em vez de quebrar tudo: servir dados do último run bom, pular uma
fonte opcional indisponível (e sinalizar), processar o que dá e marcar o resto. Decida caso
a caso — às vezes dados parciais são aceitáveis, às vezes não.

## Dependências upstream

Use **sensors**/esperas para fontes que podem atrasar, com timeout e SLA. Não assuma que a
fonte estará pronta no horário; o pipeline deve lidar com atraso (esperar, alertar, ou pular
conforme a política). Ver [dependências](../../10-data-pipelines/02-dags-dependencies/README.md).

## Runbooks

Documente, para cada falha comum, **o que fazer** (como diagnosticar, como reprocessar com
segurança, quem acionar). Em incidentes, um runbook economiza tempo precioso (ver
[incident response](../../24-observability/07-incident-response/README.md)).

## Erros comuns

- Engolir exceções (`except: pass`) → falhas invisíveis e dados corrompidos.
- Retry em erro permanente (loop) ou em tarefa não-idempotente (duplica).
- Sem timeout → pipeline pendurado.
- Continuar processando apesar de dado inválido (grava lixo).
- Falhar sem alertar → ninguém sabe até o dashboard estar errado.
- Sem escrita atômica → estado parcial após crash.

## Boas práticas

- Idempotência + escrita atômica como base; retries só para transitórios.
- Valide e quarentene dados ruins; dead letter + alerta.
- Timeouts, checkpoints e circuit breakers onde couber.
- Logue, meça e **alerte** no acionável; mantenha runbooks.
- Prefira falhar visível a corromper silencioso.

## Relação com outros conceitos

- [Idempotência/retries](../07-idempotency-retries/README.md),
  [validação](../10-data-validation/README.md), [loading atômico](../04-loading/README.md).
- [Fault tolerance](../../10-data-pipelines/05-fault-tolerance/README.md),
  [checkpoints](../../10-data-pipelines/04-checkpoints-idempotency/README.md),
  [observabilidade](../../24-observability/README.md).

## Exercícios

1. Para cada tipo de falha (transitória, permanente, dado inválido, parcial, upstream),
   escreva a estratégia de tratamento.
2. Implemente uma tarefa com retry (transitório), timeout e escrita atômica.
3. Projete um fluxo de dead letter + alerta para registros que falham a validação.
4. Escreva um mini-runbook para "o pipeline de vendas falhou às 2h".

## Referências

- Google SRE Book — tratamento de falhas, alerting, runbooks.
- Reis & Housley, *Fundamentals of Data Engineering*.
- Documentação de retries/sensors de Airflow/Dagster/Prefect.
