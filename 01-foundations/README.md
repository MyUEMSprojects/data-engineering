# 01 — Fundamentos de Data Engineering

> 🟢 Nível 1 — Foundations · Pré-requisitos: nenhum · Próximo:
> [02 — Linux & Shell](../02-linux-shell-environment/README.md)

Este módulo constrói o **modelo mental** que todo o resto do repositório assume.
Antes de qualquer ferramenta, você precisa entender: o que é Engenharia de
Dados, como os dados fluem por uma organização, que tipos de sistemas existem e
quais leis fundamentais governam sistemas distribuídos. Sem isso, cada
ferramenta parece mágica desconexa; com isso, cada ferramenta vira "ah, é uma
resposta a *este* problema".

## Por que começar por aqui

Ferramentas mudam a cada poucos anos; os problemas, não. *Shuffle*, consistência,
particionamento, OLTP vs OLAP, batch vs streaming — esses conceitos têm décadas
e vão sobreviver ao Spark, ao Kafka e ao que vier depois. Investir aqui é o que
diferencia quem *opera* ferramentas de quem *projeta* sistemas.

## Tópicos

| # | Tópico | O que você sai sabendo |
| --- | --- | --- |
| 01 | [Introdução a Data Engineering](01-introduction-to-data-engineering/README.md) | O que é DE, por que existe, o que um DE entrega |
| 02 | [Data Engineer vs outros papéis](02-data-engineer-vs-other-roles/README.md) | Fronteiras com DS, Analyst, Backend, MLE, DevOps, MLOps |
| 03 | [Ciclo de vida dos dados](03-data-lifecycle/README.md) | Geração → ingestão → armazenamento → transformação → serving |
| 04 | [Sistemas de dados](04-data-systems/README.md) | Componentes e topologias de uma plataforma de dados |
| 05 | [Fundamentos de sistemas distribuídos](05-distributed-systems-fundamentals/README.md) | CAP, consistência, replicação, particionamento, escala |
| 06 | [Batch vs Streaming](06-batch-vs-streaming/README.md) | Dois paradigmas de processamento e quando usar cada um |
| 07 | [OLTP vs OLAP](07-oltp-vs-olap/README.md) | Cargas transacionais vs analíticas e suas implicações |

## Como estes tópicos se conectam

```text
Introdução ──► Papéis (onde o DE atua)
     │
     ▼
Ciclo de vida dos dados ──► Sistemas de dados (o que constrói cada etapa)
     │                              │
     ▼                              ▼
OLTP vs OLAP                 Sistemas distribuídos (CAP, replicação...)
     │                              │
     └──────────► Batch vs Streaming ◄──────────┘
```

Tudo o que vem depois (SQL, modelagem, warehouse, Spark, streaming) é uma
instância concreta destas ideias.

## Checkpoint

Antes de avançar, você deve conseguir:

- [ ] Explicar, em uma frase, o que um Data Engineer entrega e por quê.
- [ ] Diferenciar DE, Data Analyst, Data Scientist, ML Engineer, Backend,
      DevOps e MLOps, e desenhar como eles se encaixam.
- [ ] Descrever as etapas do ciclo de vida dos dados e dar um exemplo de
      ferramenta/decisão em cada uma.
- [ ] Explicar OLTP vs OLAP e por que não se usa o mesmo banco para os dois.
- [ ] Enunciar o CAP theorem corretamente (é sobre *partição de rede*) e dar um
      exemplo de trade-off CP vs AP.
- [ ] Explicar diferença entre consistência, disponibilidade, particionamento e
      replicação.
- [ ] Decidir, para um cenário dado, entre batch e streaming — e justificar.

## Referências do módulo

- Kleppmann, M. *Designing Data-Intensive Applications*. O'Reilly, 2017 — caps.
  1, 5, 6, 9 (a base de sistemas distribuídos para dados).
- Reis, J.; Housley, M. *Fundamentals of Data Engineering*. O'Reilly, 2022 —
  caps. 1–3 (definição, ciclo de vida, arquitetura).
- Brewer, E. "CAP Twelve Years Later". *IEEE Computer*, 2012.
