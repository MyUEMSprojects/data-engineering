# Exercícios — Módulo 30: Tópicos avançados

Teoria em [30-advanced](../../30-advanced/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — CDC

Por que usar **CDC baseado em log** (Debezium) em vez de consultar `updated_at`? Cite duas vantagens.

<details><summary>Gabarito</summary>

Lê o **log de transações** do banco: captura **deleções**, a ordem exata das mudanças e tem baixo impacto no OLTP; `updated_at` perde deletes, depende de a aplicação preenchê-lo corretamente e exige varreduras. Ver [CDC](../../30-advanced/01-cdc-debezium/README.md).
</details>

## 2. 🟢 Conceitual — Event sourcing

O que é *event sourcing* e qual a relação com CQRS?

<details><summary>Gabarito</summary>

O **estado** é derivado de uma sequência imutável de **eventos** (o log é a fonte da verdade). **CQRS** separa o modelo de **escrita** (comandos/eventos) do de **leitura** (projeções otimizadas). Juntos: reconstrução do estado em qualquer ponto e múltiplas visões; custo: complexidade e consistência eventual. Ver [event sourcing e CQRS](../../30-advanced/02-event-sourcing-cqrs/README.md).
</details>

## 3. 🔵 Implementação — Projeção a partir de eventos

Dado um fluxo de eventos de pedido (`created`, `paid`, `canceled`) com `seq`, escreva a função que **reconstrói o estado atual** de cada pedido de forma idempotente e tolerante a ordem.

<details><summary>Gabarito</summary>

```python
def project(events):
    state = {}
    for e in events:
        cur = state.get(e["order_id"])
        if cur is None or e["seq"] > cur["seq"]:       # só avança; reentrega/desordem são inofensivas
            state[e["order_id"]] = {"status": e["status"], "seq": e["seq"]}
    return state
```
É o *upsert que só avança* do [Projeto 07](../../projects/07-kafka/README.md) (`WHERE seq novo > seq atual`).
</details>

## 4. 🔵 Arquitetura — Data mesh

Quais são os **quatro princípios** do data mesh e quando ele **não** vale a pena?

<details><summary>Gabarito</summary>

Propriedade por **domínio**, **dados como produto**, plataforma **self-service**, **governança federada**. Não vale em organizações pequenas/centralizadas, com poucos domínios ou sem maturidade de plataforma/produto de dados — o custo organizacional supera o ganho. Ver [data mesh](../../30-advanced/03-data-mesh/README.md).
</details>

## 5. 🟣 Arquitetura — Banco vetorial

Para busca semântica em 50 milhões de documentos, descreva o fluxo (embeddings → índice → consulta) e o trade-off de **ANN** (HNSW/IVF) × busca exata.

<details><summary>Gabarito</summary>

Gerar **embeddings** dos documentos (modelo), armazenar no índice vetorial com metadados, e na consulta embutir a pergunta e buscar os **k vizinhos mais próximos** (cosseno/produto interno), opcionalmente filtrando por metadados e fazendo *re-ranking*. **ANN** troca um pouco de **recall** por muita **velocidade/memória** (HNSW: grafo; IVF: clusters); busca exata é O(n) — inviável em escala. Pipeline de ingestão precisa atualizar embeddings quando o documento muda. Ver [bancos vetoriais](../../30-advanced/06-vector-databases/README.md).
</details>

## 6. 🟣 Arquitetura — Spark/Kafka avançado

Um job Spark e um consumidor Kafka sofrem de **skew** por uma chave quente. Compare as estratégias em cada sistema (salting, AQE, particionador customizado).

<details><summary>Gabarito</summary>

**Spark:** AQE *skew join*, *salting* manual ou broadcast da chave quente ([Projeto 06](../../projects/06-spark/README.md)). **Kafka:** a chave quente satura **uma partição** — use **particionador customizado** (ex.: sufixo/salt na chave e re-agregação no consumidor) ou separe a chave quente em outro tópico; lembre que isso **quebra a ordem** por chave. Em ambos: detectar por métricas por tarefa/partição. Ver [Spark avançado](../../30-advanced/09-advanced-spark/README.md) e [Kafka avançado](../../30-advanced/10-advanced-kafka/README.md).
</details>
