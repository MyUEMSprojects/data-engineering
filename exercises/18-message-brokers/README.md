# Exercícios — Módulo 18: Message brokers

Teoria em [18-message-brokers](../../18-message-brokers/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Fila × log

Qual a diferença fundamental entre uma **fila** (RabbitMQ/SQS) e um **log particionado** (Kafka) quanto à **retenção** e ao **replay**?

<details><summary>Gabarito</summary>

Fila: a mensagem é **removida** ao ser consumida (cada mensagem processada por um consumidor); sem replay. Log: mensagens ficam retidas por tempo/tamanho e cada consumidor mantém seu **offset** — vários grupos leem independentemente e é possível **reler** (replay). Ver [fila vs log](../../18-message-brokers/01-queue-vs-log/README.md).
</details>

## 2. 🟢 Conceitual — Ordem no Kafka

Onde o Kafka garante ordem? Como garantir que todos os eventos de um pedido sejam processados em ordem?

<details><summary>Gabarito</summary>

Apenas **dentro de uma partição**. Use `order_id` como **chave** da mensagem: o mesmo hash → mesma partição → ordem por pedido (não há ordem global). Ver [ordenação](../../18-message-brokers/05-ordering-retention-replay/README.md).
</details>

## 3. 🔵 Implementação — Commit de offset

Em que ordem fazer: processar, gravar no destino, commitar o offset? O que acontece com `enable.auto.commit=true`?

<details><summary>Gabarito</summary>

`processar → gravar → **commit**` (commit manual, síncrono, depois do destino). Com auto-commit por tempo, o offset pode avançar **antes** de você gravar ⇒ falha entre os dois causa **perda**. Combine com destino idempotente. Ver [producers e consumers](../../18-message-brokers/03-producers-consumers/README.md) e o [Projeto 07](../../projects/07-kafka/README.md).
</details>

## 4. 🔵 Debugging — Lag crescendo

O *consumer lag* sobe continuamente. Liste **quatro** causas possíveis e como investigar.

<details><summary>Gabarito</summary>

(1) Consumidor **mais lento** que a produção (destino lento) → perfil de latência do sink. (2) **Poucas partições/consumidores** (paralelismo limitado pelo nº de partições). (3) **Rebalance** frequente (processamento maior que `max.poll.interval`). (4) **Hot partition** (chave quente). Também: mensagens grandes, GC. Métrica: lag por partição, taxa de consumo × produção. Ver [partições e grupos](../../18-message-brokers/04-partitions-offsets-consumer-groups/README.md).
</details>

## 5. 🟣 Arquitetura — Mensagem-veneno

Uma mensagem malformada faz o consumidor falhar sempre, travando a partição. Projete o tratamento com **DLQ** e diga o que guardar nos headers.

<details><summary>Gabarito</summary>

Valide/parseie; se inválida, **publique na DLQ** (mesmo payload + chave) com headers `error` (motivo) e `source` (`tópico:partição:offset`), **faça flush da DLQ antes do commit** e siga adiante. Alertar quando a DLQ crescer; ferramenta para reprocessar após correção; deduplicar a DLQ pela origem (ela também é *at-least-once*). Implementado no [Projeto 07](../../projects/07-kafka/README.md).
</details>

## 6. 🟣 Arquitetura — Dimensionar partições

Um tópico receberá 50 MB/s e cada consumidor processa 5 MB/s. Quantas partições no mínimo? Que cuidados ao aumentar depois?

<details><summary>Gabarito</summary>

Paralelismo mínimo = 50 / 5 = **10 consumidores ⇒ ≥ 10 partições** (com folga: 12–20). Aumentar partições depois **muda o mapeamento chave→partição** (quebra a ordem para chaves já existentes) e não redistribui mensagens antigas; diminuir não é suportado. Planeje com folga desde o início. Ver [Kafka](../../18-message-brokers/02-apache-kafka/README.md).
</details>
