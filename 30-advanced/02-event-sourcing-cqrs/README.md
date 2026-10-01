# Event sourcing e CQRS

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: padrões arquiteturais (uso seletivo)*

## Event Sourcing

### O que é
Em vez de armazenar apenas o **estado atual** de uma entidade, armazena-se a **sequência imutável de
eventos** que levaram a ele (`PedidoCriado`, `ItemAdicionado`, `PagamentoAprovado`...). O **estado é
derivado** **reproduzindo (replay)** os eventos. O **log de eventos é a fonte da verdade**.

```text
CRUD tradicional:   pedido(id=7, status=PAGO, total=120)              ← só o "agora"
Event sourcing:     [PedidoCriado(7) → ItemAdicionado(7,x) → PagamentoAprovado(7)]  ← a história inteira
                    estado(7) = fold(eventos)
```

### Por que
- **Auditoria completa e nativa** — nada se perde (quem/quando/por quê).
- **Time travel** — reconstruir o estado em qualquer instante; depurar "como chegamos aqui".
- **Reprocessamento**: corrigir bug e **recomputar** projeções/derivados do log
  ([replay](../../18-message-brokers/05-ordering-retention-replay/README.md), arquitetura Kappa).
- **Múltiplas visões** (projeções) dos mesmos eventos para necessidades distintas.
- Naturalmente alinhado a **EDA** e ao fluxo analítico (eventos já são o dado) — ver
  [event-driven](../../17-streaming/02-event-driven-architecture/README.md).

### Como funciona
- **Event store** (append-only): EventStoreDB, **Kafka** (com retenção longa/compactação), Postgres (tabela
  de eventos), DynamoDB. Cada evento: `aggregateId`, `tipo`, `payload`, `versão/sequência`, `timestamp`,
  metadados (causalidade, usuário).
- **Agregado**: a unidade de consistência; eventos de um agregado são **ordenados** (versão) e gravados com
  **concorrência otimista** (`expectedVersion`).
- **Projeções / read models**: consumidores constroem **visões materializadas** a partir dos eventos
  (tabelas, índices de busca, agregados).
- **Snapshots**: salvar o estado periodicamente para não reproduzir milhões de eventos.
- **Upcasting/versionamento de eventos**: eventos são **imutáveis e vivem para sempre** → evolução de
  schema exige cuidado ([schema evolution](../../08-data-formats/10-schema-evolution/README.md)).

### Custos e armadilhas
- **Complexidade alta** (modelagem de eventos, projeções, consistência eventual).
- **Evolução de eventos** (compatibilidade a longo prazo) — pior que evoluir tabelas.
- **Consultas**: ler estado atual exige projeções; sem queries ad-hoc diretas no event store.
- **Exclusão/LGPD**: eventos imutáveis conflitam com "direito ao esquecimento" → **crypto-shredding**,
  separar PII, eventos referenciando dados externos ([retenção/exclusão](../../25-data-governance/06-retention-auditing/README.md),
  [LGPD](../../26-security/08-lgpd/README.md)).
- **Replay lento** em históricos grandes (snapshots).
- Fácil de **over-engineer**: nem todo domínio precisa.

### Quando usar / não usar
- **Use** em domínios onde **a história importa** (financeiro, pedidos, logística, compliance), auditoria
  forte, múltiplas visões, ou quando já se é fortemente orientado a eventos.
- **Evite** em CRUD simples, times sem experiência, ou onde um **log de auditoria/CDC** resolve (você ganha
  o histórico sem mudar o modelo de persistência).

> **Event sourcing ≠ usar eventos para integração.** Publicar eventos de domínio (EDA) ou CDC **não** exige
> que o evento seja a fonte da verdade.

## CQRS (Command Query Responsibility Segregation)

### O que é
**Separar o modelo de escrita (comandos)** do **modelo de leitura (consultas)**. Escritas tratam **regras de
negócio e consistência**; leituras são **otimizadas para consulta** (denormalizadas, indexadas, em outro
store). Os dois são sincronizados por **eventos** (consistência eventual).

```text
Comando ─► Modelo de ESCRITA (valida regras, agregado) ─► grava (estado ou eventos)
                                  │ eventos
                                  ▼
                       Projeção ─► Modelo de LEITURA (view otimizada: SQL denormalizado, ES, cache)
Consulta ─────────────────────────────────────────────► lê do modelo de leitura
```

### Por que
- **Escalar leitura e escrita independentemente** (perfis opostos — lembra OLTP vs OLAP,
  [OLTP vs OLAP](../../01-foundations/07-oltp-vs-olap/README.md)).
- **Modelos de leitura sob medida** para cada necessidade (relatórios, busca, telas).
- Simplifica o modelo de escrita (foco em invariantes).

### Níveis de adoção
1. **Mesmo banco**, modelos/camadas separados (leve).
2. **Bancos separados**, sincronizados por eventos/CDC (consistência eventual).
3. **CQRS + Event Sourcing** (combinação clássica — eventos alimentam as projeções).

### Custos
Consistência eventual na leitura (read-your-writes — [replicação/consistência](../../06-databases/08-concurrency-consistency/README.md)),
mais componentes, duplicação, complexidade operacional. **Não aplique por padrão.**

## Ligação com Data Engineering

- **O log de eventos é uma fonte analítica ideal**: ingerir eventos (Kafka → lake) dá histórico completo e
  permite reconstruir qualquer visão ([bronze imutável](../../14-data-lake/03-medallion-architecture/README.md)).
- **Projeções ≈ pipelines**: construir read models a partir de eventos é o mesmo problema de
  [stream processing](../../17-streaming/README.md) + [materializações](../../05-sql/06-views-materialized-views/README.md).
- **CDC como "event sourcing do pobre"**: [Debezium](../01-cdc-debezium/README.md) captura mudanças do banco
  como eventos **sem** que o sistema seja event-sourced (e o **Outbox** publica eventos de domínio de forma
  atômica).
- **Dados como produto** em mesh: eventos como interface ([data mesh](../03-data-mesh/README.md)).
- **Kappa**: reprocessar o log para recomputar derivados ([sistemas de dados](../../01-foundations/04-data-systems/README.md)).

## Erros comuns

- Adotar event sourcing/CQRS "por ser moderno" em CRUD simples.
- Eventos que são só "o registro mudou" (CRUD events) em vez de **fatos de negócio** com intenção.
- Não planejar **evolução de eventos** nem upcasting.
- Esquecer exclusão/LGPD em event store imutável.
- Ignorar consistência eventual nas telas (UX confusa).
- Event store sem snapshots; replay interminável.

## Boas práticas

- Use onde o histórico/auditoria/múltiplas visões justificam; comece pelo agregado mais valioso.
- Eventos **imutáveis, nomeados no passado, com intenção de negócio**; versionados e com contrato
  ([contratos](../../29-data-contracts/README.md)).
- Projeções **idempotentes e reconstruíveis**; snapshots; concorrência otimista por agregado.
- Planeje privacidade (PII fora do evento ou criptografada por titular).
- Combine com Outbox/CDC para publicação confiável.

## Relação com outros conceitos

- [EDA](../../17-streaming/02-event-driven-architecture/README.md), [Kafka (log/replay)](../../18-message-brokers/README.md),
  [CDC/Debezium](../01-cdc-debezium/README.md), [stateful processing](../../17-streaming/05-stateful-processing/README.md),
  [data mesh](../03-data-mesh/README.md).

## Exercícios

1. Modele um agregado `Pedido` com event sourcing (eventos, estado derivado) e uma projeção "pedidos por
   status".
2. Explique CQRS e o que muda na consistência de leitura; dê uma estratégia para read-your-writes.
3. Como atender uma exclusão LGPD em um event store imutável?
4. Compare event sourcing, CDC e log de auditoria para obter o histórico de mudanças.

## Referências

- Kleppmann, M. *DDIA* (cap. 11); Fowler, M. — Event Sourcing, CQRS; Young, G. — CQRS Documents;
  Stopford, B. *Designing Event-Driven Systems*; docs de EventStoreDB, Axon.
