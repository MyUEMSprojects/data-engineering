# Backpressure

> 🟣 Distributed Systems · Parte de [18 — Message Brokers](../README.md)

## O que é

**Backpressure** (contrapressão) é o fenômeno e o mecanismo pelo qual um componente **mais lento**
sinaliza (ou impõe) a componentes a montante que **desacelerem**, evitando que acumule trabalho sem
limite. Ocorre quando o **produtor** gera mais rápido do que o **consumidor** consegue processar.

## Por que importa

Sem tratamento, o desequilíbrio produz: filas/buffers crescendo até **estourar memória/disco**,
latência cada vez maior, perda de mensagens ou colapso em cascata. Em pipelines de streaming, é a
causa clássica de "o dashboard está atrasado há horas".

## Como aparece em cada modelo

### Em log (Kafka)

O broker **absorve** o excesso: o log retém as mensagens, e o consumidor atrasado vira **lag**
(offset commitado ≪ fim do log). O log funciona como **buffer durável** — backpressure "natural", pois
produtor e consumidor são desacoplados. O risco é o lag crescer além da **retenção** (dados expiram antes de
serem lidos → perda).

```text
produtor 10k msg/s ─► [ log retém ] ─► consumidor 6k msg/s     → lag cresce 4k msg/s
```

### Em filas ([RabbitMQ](../08-rabbitmq-and-others/README.md))

A fila cresce; brokers aplicam **flow control** (bloqueiam produtores ao atingir limites de memória/
disco) — o produtor sente a pressão diretamente.

### Em engines de streaming

[Flink](../../17-streaming/07-flink/README.md) propaga backpressure operador a operador (buffers de rede
limitados: se um operador lento enche o buffer, o anterior para) até a fonte reduzir a leitura. Spark SS
controla via limites por trigger (`maxOffsetsPerTrigger`).

## Diagnóstico

- **Consumer lag** crescente por grupo/partição (métrica principal).
- Latência fim-a-fim aumentando; *processing time* por batch > intervalo do trigger.
- Em Flink: indicadores de backpressure/busy time na UI; checkpoints demorando.
- Uso de memória/disco do broker subindo.

## Estratégias de mitigação

1. **Escalar o consumo** — mais consumidores (até o nº de partições), mais paralelismo
   ([partitions/groups](../04-partitions-offsets-consumer-groups/README.md)); mais partições se preciso.
2. **Otimizar o consumidor** — processar em lote, I/O assíncrono, reduzir trabalho por mensagem,
   *bulk writes* no sink.
3. **Limitar a taxa** — rate limiting no produtor, `max.poll.records`, `maxOffsetsPerTrigger`.
4. **Buffer + retenção adequada** — retenção suficiente para absorver picos até o consumidor alcançar.
5. **Shed load / amostragem** — descartar ou agregar dados de baixa prioridade sob pressão (aceitável
   para telemetria).
6. **Pausar/retomar** partições (`pause()`) quando o sink está lento.
7. **Dead letter** para mensagens problemáticas que travam o consumo.
8. **Autoscaling** guiado por lag (ex.: KEDA em [Kubernetes](../../21-kubernetes/README.md)).

## Backpressure para sinks lentos

Frequentemente o gargalo é o **destino** (banco, API, warehouse). Use batching, filas intermediárias,
retries com backoff e limites de concorrência; considere desacoplar com um tópico adicional.

## Erros comuns

- Não monitorar lag → descobrir o atraso pelo usuário.
- Retenção menor que o tempo de recuperação do lag (perda de dados).
- Escalar consumidores além das partições (sem efeito).
- Retry agressivo sem backoff amplificando a pressão.
- Buffers ilimitados em memória no consumidor (OOM).

## Boas práticas

- Alerta de lag (por tempo, não só por contagem); dimensionar capacidade para picos.
- Consumidores com batching e limites de memória; sinks otimizados para escrita em lote.
- Retenção ≥ pior caso de recuperação; autoscaling por lag.
- Defina a política sob sobrecarga (bloquear, descartar ou degradar) conscientemente.

## Relação com outros conceitos

- [Partitions/consumer groups](../04-partitions-offsets-consumer-groups/README.md),
  [retenção](../05-ordering-retention-replay/README.md), [Flink](../../17-streaming/07-flink/README.md).
- [Observabilidade](../../24-observability/README.md), [escalabilidade](../../01-foundations/05-distributed-systems-fundamentals/README.md).

## Exercícios

1. Explique por que o log do Kafka "absorve" backpressure e qual limite ainda existe.
2. Dado produtor 10k/s e consumidor 6k/s, como evolui o lag e o que fazer?
3. Liste 4 mitigações e quando aplicar cada.
4. Defina alertas de lag adequados para um pipeline com SLA de 5 minutos.

## Referências

- Documentação de Flink (backpressure) e Kafka (consumer lag); Reactive Streams spec.
- Kleppmann, M. *DDIA* — cap. 11 (backpressure e buffering).
