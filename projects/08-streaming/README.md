# Projeto 08 — Streaming: Kafka → Spark Structured Streaming → PostgreSQL (tempo de evento, watermark, dedup)

> 🟣 Nível: avançado · Módulos: [17 Streaming](../../17-streaming/README.md),
> [18 Message brokers](../../18-message-brokers/README.md), [16 Spark](../../16-distributed-processing/README.md) ·
> Anterior: [Projeto 07](../07-kafka/README.md) · Próximo: [Projeto 09](../09-cloud/README.md)

## Objetivo

O [Projeto 07](../07-kafka/README.md) moveu eventos do Kafka para um banco, **uma mensagem por vez**. Aqui o
problema é outro: **calcular sobre o fluxo** — contar visualizações por página em **janelas de 1 minuto do
tempo do evento**, mesmo com eventos **fora de ordem**, **atrasados**, **duplicados** e **inválidos**. O que se
aprende, com verificação automática:

- **tempo de evento × tempo de processamento** e por que janelas usam o primeiro ([tempo e janelas](../../17-streaming/03-time-and-windows/README.md));
- **watermark**: até quando esperar dados atrasados — e o que acontece com os *muito* atrasados;
- **estado** (janelas abertas, deduplicação) e **checkpoint** (offsets + estado) ([processamento com estado](../../17-streaming/05-stateful-processing/README.md));
- **update mode + sink idempotente** com livro-razão de micro-lotes (*exactly-once* efetivo);
- **validar o job contra uma implementação de referência** — a única forma honesta de testar streaming.

## Arquitetura

```text
 produtor (Python)     Kafka (topic `clicks`, 3 partições)        Spark Structured Streaming (trigger availableNow)              PostgreSQL
 3 FASES do cenário ─► [{"event_id","user_id","page",     ─►  parse ──► válidas ─► withWatermark(2 min) ─► dropDuplicatesWithinWatermark ─► window(1 min) × page
  (chegada ≠ ordem      "event_time"}]                          │                                                 │ update mode (foreachBatch)
   dos eventos)                                                 └─► inválidas ─────────────────────────────────────┼─────────────────────────────►  stream_rejects
                                                                 checkpoint: offsets + estado + watermark          └─► UPSERT page_views_1m  +  batch_log (mesma transação)
```

### O cenário (determinístico) — janela 1 min, tolerância (watermark) 2 min

```text
eixo do tempo de EVENTO (min)  0────────10────12──13──14─15
fase 1  tráfego min 0-9, desordem ≤ 50 s, 10 duplicatas, 2 inválidas          → WM ao fim: 12:07:58
fase 2  tráfego min 10-13 + 15 ATRASADOS-MAS-TOLERADOS (min 8-9) + 5 duplicatas entre fases + 1 inválida
                                                                               → WM ao fim: 12:11:58
fase 3  tráfego min 14-15 + 8 TOLERADOS (min 12) + 18 MUITO ATRASADOS (min 2 e 10) ⇒ DESCARTADOS
```

- O evento do **minuto 9** que só chega na fase 2 (depois do tráfego do minuto 9 já ter sido processado) **ainda é
  contado**: a janela dele termina em 12:10, **após** o watermark (12:07:58).
- O do **minuto 2** que chega na fase 3 **não é**: janela termina em 12:03, bem **antes** do watermark (12:11:58).
- Regra do Spark (e do gabarito): descarta-se o evento se **o fim da janela dele ≤ watermark**, e o watermark usado num
  micro-lote é `max(event_time dos lotes anteriores) − tolerância`.
- As margens são ≥ 30 s: o resultado **não depende** de como o Spark parte os micro-lotes (testado).

## Requisitos

Docker + Compose. Tudo roda em contêineres (Spark 4.0, Java 17, **conector Kafka pré-baixado na imagem** — o
build resolve os JARs uma vez; depois não precisa de internet).

## Estrutura

```text
08-streaming/
├── Dockerfile · docker-compose.yml · run.sh · main.py   # Spark+conector, Kafka (2 listeners), PostgreSQL, atalho
├── sql/init.sql                  # page_views_1m · stream_rejects · batch_log
├── src/streamlab/
│   ├── events.py                 # cenário em 3 fases (chegada ≠ tempo de evento), parse espelho
│   ├── reference.py              # GABARITO em Python puro: a semântica esperada
│   ├── job.py                    # o job Spark (parse → watermark → dedup → janela → sinks)
│   ├── db.py                     # apply_batch(): dados + livro-razão na MESMA transação
│   ├── producer.py · cli.py      # envio por fase · demo/report/reset/job
└── tests/                        # 20 testes: 14 sem infra + Spark/PostgreSQL + o demo ponta a ponta
```

## Execução

```bash
cd projects/08-streaming
export KAFKA_PORT=9092 POSTGRES_PORT=5432          # (portas ocupadas? troque; mantenha EXPORTADAS em todo comando)
docker compose build                               # ~1 min na 1ª vez (baixa o conector Kafka)
./run.sh demo                                      # 3 fases + reexecução + verificação (~30 s)

# explorar
./run.sh reset                                     # limpa tópico, checkpoint e tabelas
./run.sh produce --phase 1 && ./run.sh job         # fase 1 → processa e encerra
./run.sh produce --phase 2 && ./run.sh job         # retoma DO CHECKPOINT: só o que chegou de novo
./run.sh report
docker compose exec postgres psql -U de -d analytics \
  -c "select to_char(window_start,'HH24:MI') w, page, views, users, updated_batch from page_views_1m order by 1,2 limit 10"
docker compose down -v
```

Saída verificada:

```text
== FASE 1: ... ==  produzidas=412 · micro-lotes=2 · linhas lidas=412 · descartadas por atraso (Spark)=0 (esperado: 0)
   watermarks reportados: ['00:00:00', '12:07:58']          ← 00:00:00 = ainda sem watermark; depois 12:09:58 − 2 min
== FASE 2: ... ==  produzidas=181 · ... descartadas=0 (esperado: 0)  · watermark no início da fase: 12:07
== FASE 3: ... ==  produzidas=106 · ... descartadas por atraso (Spark)=18 (esperado: 18) · watermark no início: 12:11
== REEXECUÇÃO sem dados novos ==  linhas lidas=0 · janelas iguais antes/depois: True
== VERIFICAÇÃO contra a implementação de referência (Python puro) ==
   ✔ mesmas janelas (chaves)
   ✔ mesmas contagens de views e usuários distintos em TODAS as janelas
   ✔ total de views = 663
   ✔ eventos muito atrasados descartados pelo watermark = 18
   ✔ mensagens inválidas guardadas em stream_rejects = 3
   ✔ reexecução sem dados novos não alterou o resultado
   (duplicatas removidas: 15)
```

Ponto-chave para olhar no banco — `updated_batch` mostra **quando** cada janela foi atualizada:

```text
   w   |   page   | views | users | updated_batch
 12:08 | checkout |     3 |     3 |             0      ← fechou na fase 1, nunca mais mudou
 12:08 | home     |    11 |     9 |             2      ← REABERTA na fase 2 por eventos atrasados-mas-tolerados
```

> **Por que 2 micro-lotes por fase?** Com `availableNow`, o Spark roda 1 lote com os dados e **mais 1 lote
> "sem dados"** só para avançar o watermark e liberar estado. O watermark que aparece no progresso de um lote é o
> que valerá para o **próximo**.

## Testes

```bash
export KAFKA_PORT=9092 POSTGRES_PORT=5432
docker compose run --rm app "python3 -m pytest /app/tests -c /app/pyproject.toml -q -p no:cacheprovider"
#   20 passed (~20 s) — inclui o demo ponta a ponta contra Kafka/Spark/PostgreSQL reais
# só a parte pura (sem Docker):  pip install pytest 'psycopg[binary]' && PYTHONPATH=src pytest tests/test_scenario_and_reference.py
```

| Grupo | O que garante |
| --- | --- |
| **Parse (Python)** | roundtrip; 8 formas de inválido (JSON quebrado, vazio, `[1]`, campo ausente/vazio, data impossível, tipo errado, `None`) |
| **Semântica do gabarito** | **nada é tardio no 1.º lote** (mesmo desordenado); watermark usa **só lotes anteriores**; regra é **fim da janela ≤ watermark** (borda testada); dedup **antes** da agregação e `users` = distintos; inválidas contam e **não avançam** o watermark |
| **Cenário** | determinístico; números esperados (15 duplicatas, 18 atrasados, 3 inválidas, 663 views); **margens ≥ 30 s** (independe da divisão em micro-lotes); contém todos os casos difíceis |
| **PARIDADE Spark × Python** | para **cada** mensagem do cenário, a validade no Spark == a do gabarito; os 2 motivos de rejeição aparecem |
| **Sink (PostgreSQL)** | aplicar o mesmo `batch_id` 2× é **no-op**; *update mode* sobrescreve com valor **absoluto**; livro-razão e dados são **atômicos** (falha não marca o lote como aplicado); livros por query são independentes |
| **Ponta a ponta** | o demo inteiro contra Kafka+Spark+PostgreSQL reais bate com a referência |

> 🐞 **Armadilha real encontrada nos testes de paridade**: `from_json` é **PERMISSIVE** — um JSON *malformado* não
> devolve `NULL`, devolve um *struct com todos os campos nulos*. Meu `bad_json = j IS NULL` classificava o JSON
> truncado como `missing_or_bad_field`. O demo passava (a *contagem* de rejeitadas estava certa), mas o **motivo** estava
> errado. Correção: incluir `_corrupt_record` no schema (`columnNameOfCorruptRecord`). Moral: teste a **classificação**, não só o total.
>
> 🐞 Outros dois tropeços, ambos de ambiente: a imagem do Spark usa **Python 3.10** (sem `datetime.UTC`, que é 3.11+), e o
> volume de checkpoint precisa pertencer ao usuário `spark` (senão `mkdir of file:/data/checkpoints failed`).

## Decisões arquiteturais e trade-offs

- **`availableNow` em vez de trigger contínuo**: mesmo código e mesma semântica (estado, watermark, checkpoint), com
  custo de batch e **determinismo para testar**. Em produção contínua use `processingTime`/`continuous` —
  o checkpoint é o mesmo ([Spark Structured Streaming](../../17-streaming/08-spark-structured-streaming/README.md)).
- **Watermark de 2 min** é uma **aposta**: maior = mais completo e **mais lento/mais estado**; menor = rápido e
  **descarta mais**. Meça o atraso real da sua fonte (percentil 99) antes de escolher; descartados devem ser **contados e
  alertados** (aqui, via `numRowsDroppedByWatermark`).
- **Update mode + `foreachBatch` + UPSERT por (janela, página)**: o resultado analítico fica **sempre consultável**
  (janela aberta aparece parcial) e a escrita é idempotente. *Append mode* só emitiria a janela depois do watermark
  (latência = tolerância); *complete mode* reescreveria tudo a cada lote (não escala).
- **Livro-razão `batch_log` na mesma transação**: o Spark garante *at-least-once* para `foreachBatch` — após uma
  falha, o **último lote pode rodar de novo**. O livro-razão torna isso inofensivo mesmo para sinks **não**
  idempotentes (contadores incrementais, por exemplo). Aqui o UPSERT absoluto já seria seguro; o livro é a defesa
  em profundidade ([semânticas de entrega](../../17-streaming/04-delivery-semantics/README.md)).
- **`dropDuplicatesWithinWatermark(event_id)`** (e não `dropDuplicates`): o estado de deduplicação é **podado pelo
  watermark**; sem isso cresceria para sempre (um `event_id` guardado eternamente). Garantia vale **dentro da tolerância** —
  duplicata que chega depois disso passa. Por isso o cenário só repete eventos *recentes* entre fases.
- **`collect_set` para usuários distintos** (exato) em vez de `approx_count_distinct` (HLL): para validar contra um
  gabarito exato, e porque `COUNT(DISTINCT)` **não é suportado** em agregação de streaming. Custo: o estado guarda os ids.
  Em cardinalidade alta, volte ao HLL e aceite o erro (~2%).
- **Inválidas num segundo *query* com checkpoint próprio**: não bloqueiam o fluxo e ficam inspecionáveis (`stream_rejects`),
  com chave = coordenadas Kafka (idempotente). Alternativa: tópico DLQ (como no Projeto 07).
- **Kafka com dois *listeners* (INTERNAL/EXTERNAL)**: o cliente usa o endereço **anunciado**; contêineres precisam de
  `kafka:19092`, o host de `localhost:KAFKA_PORT`. É o erro nº 1 de Kafka em Docker.
- **Gabarito em Python puro**: streaming é difícil de testar com asserts "esperados à mão"; uma implementação de
  referência **simples e óbvia** (≈40 linhas) vira o oráculo. Se o job e o gabarito discordarem, **um dos dois tem bug**.
- **O que este projeto NÃO cobre**: janelas deslizantes/de sessão (`session_window`), *stream-stream joins*, escalar
  além de `local[2]`, *exactly-once* por transações Kafka, e *schema registry* ([exercícios](#possíveis-melhorias-exercícios)).

## Erros comuns que o projeto evita

1. **Janelar por tempo de processamento** (`now()`): a mesma execução gera resultados diferentes a cada reprocessamento.
2. **Sem watermark**: o estado cresce sem limite → OOM; e nunca se sabe quando uma janela "fechou".
3. **Descartar atrasados em silêncio**: aqui são **contados** e conferidos.
4. **Confiar em "o Spark garante exactly-once"**: vale para o *estado interno*; o **sink** precisa ser idempotente.
5. **`dropDuplicates` sem watermark** em stream (estado infinito).
6. **Testar só o caminho feliz**: sem atrasados, duplicatas e lixo, nada disso é exercitado.

## Possíveis melhorias (exercícios)

1. **Janela deslizante** (`window(ts, "5 minutes", "1 minute")`) e **de sessão** (`session_window`): adapte o gabarito e valide.
2. **Mude o watermark** para 30 s e 10 min no `reference.py` **e** no job; preveja quantos eventos serão descartados e confira.
3. **Stream-stream join**: junte `clicks` com um tópico de `purchases` (com *watermark* e limite de tempo na condição).
4. **Trigger contínuo** (`processingTime="5 seconds"`) com o produtor rodando em paralelo; observe o `lastProgress` e a latência.
5. **Crash no meio do lote**: faça `sink_windows` falhar *depois* de aplicar e *antes* do commit do checkpoint; reinicie e veja
   `reexecuções absorvidas` no relatório.
6. **Escala**: aumente para 12 partições e `local[6]`; relacione partições Kafka × tarefas Spark ([Projeto 06](../06-spark/README.md)).
7. **Métricas**: exporte `numRowsDroppedByWatermark`, `inputRowsPerSecond` e atraso do watermark para o Prometheus
   ([observabilidade](../../24-observability/README.md)).
8. **Reprocessamento**: apague `page_views_1m` e o checkpoint e reprocesse do início — o resultado é idêntico? Por quê?
9. **Flink**: reimplemente o job em PyFlink/SQL e compare modelo de estado e *watermarks* ([Flink](../../17-streaming/07-flink/README.md)).

## Referências

- [Structured Streaming Programming Guide](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) — *window operations, watermarking, dropDuplicatesWithinWatermark, foreachBatch*;
  [Kafka Integration Guide](https://spark.apache.org/docs/latest/streaming/structured-streaming-kafka-integration.html).
- Akidau et al., *The Dataflow Model* (VLDB 2015) e *Streaming Systems* (O'Reilly) — o vocabulário de **tempo de evento, janelas, watermarks e gatilhos**.
- Módulos [17](../../17-streaming/README.md) e [18](../../18-message-brokers/README.md).
