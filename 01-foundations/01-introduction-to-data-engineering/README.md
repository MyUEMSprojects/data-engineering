# Introdução a Data Engineering

> 🟢 Foundations · Parte de [01 — Fundamentos](../README.md)

## O que é

**Engenharia de Dados** é a disciplina que projeta, constrói e opera sistemas
que coletam, armazenam, transformam e disponibilizam dados de forma **confiável,
em escala e com qualidade** para quem precisa consumi-los — analistas, cientistas
de dados, modelos de ML e aplicações.

Uma definição útil (Reis & Housley): *Data Engineering é o desenvolvimento,
implementação e manutenção de sistemas e processos que transformam dados brutos
em informação consistente e de alta qualidade, habilitando casos de uso como
análise e machine learning.*

Repare no que a definição **não** diz: não é sobre uma ferramenta específica
(Spark, Airflow, dbt). Essas são implementações. A engenharia está em transformar
dado bruto, sujo e espalhado em algo confiável e acessível.

## Por que existe / que problema resolve

Organizações geram dados em muitos lugares: bancos operacionais, APIs de
terceiros, logs de aplicação, eventos de usuário, planilhas, arquivos. Esses
dados nascem:

- **Espalhados** — cada sistema tem o seu, em formatos diferentes.
- **Sujos** — valores faltando, duplicados, inconsistentes.
- **Voláteis** — bancos operacionais mudam o tempo todo e não guardam histórico.
- **Em formato errado para análise** — um banco de aplicação é ótimo para
  gravar um pedido, péssimo para calcular "faturamento por região nos últimos 3
  anos".

Sem Engenharia de Dados, cada analista ou cientista tenta puxar dados direto da
fonte, do seu jeito, repetindo trabalho, sobrecarregando bancos de produção e
chegando a números diferentes para a mesma pergunta ("por que seu relatório diz
R$ 2M e o meu R$ 2,3M?"). A Engenharia de Dados resolve isso criando uma
**fundação de dados confiável e compartilhada**.

## O que um Data Engineer entrega

- **Pipelines de dados** — processos automatizados que movem e transformam
  dados da origem ao destino ([ETL/ELT](../../09-etl-elt/README.md),
  [pipelines](../../10-data-pipelines/README.md)).
- **Armazenamento analítico** — [data warehouses](../../13-data-warehouse/README.md),
  [data lakes](../../14-data-lake/README.md) e
  [lakehouses](../../15-lakehouse/README.md) organizados e performáticos.
- **Modelos de dados** — estruturas ([modelagem](../../07-data-modeling/README.md))
  que tornam os dados compreensíveis e rápidos de consultar.
- **Garantias** — [qualidade](../../12-data-quality/README.md),
  [observabilidade](../../24-observability/README.md),
  [governança](../../25-data-governance/README.md) e SLAs de dados.
- **Acesso** — tabelas, views e APIs que os consumidores usam com confiança.

## Como funciona (visão de alto nível)

```text
            FONTES                      PLATAFORMA DE DADOS                 CONSUMO
┌──────────────────────────┐   ┌─────────────────────────────────┐   ┌──────────────┐
│ bancos (OLTP)            │   │  ingestão → armazenamento        │   │ BI / dashboards
│ APIs de terceiros        │──►│  → transformação → serving       │──►│ Data Science  │
│ eventos / logs / arquivos│   │  (+ qualidade, orquestração,     │   │ ML            │
│                          │   │   observabilidade, governança)   │   │ aplicações    │
└──────────────────────────┘   └─────────────────────────────────┘   └──────────────┘
```

O detalhamento de cada etapa está em
[Ciclo de vida dos dados](../03-data-lifecycle/README.md).

## Conceitos fundamentais que guiam a profissão

- **Confiabilidade** — o dado chega, está correto e no horário combinado.
- **Escala** — soluções que funcionam com 1 GB e com 100 TB.
- **Idempotência** — reprocessar não corrompe nem duplica (ver
  [ETL](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Reprodutibilidade** — mesmos dados + mesmo código = mesmo resultado.
- **Custo** — dados são caros; eficiência importa (compute e storage).
- **Trade-offs** — quase toda decisão troca algo por algo (latência vs custo,
  consistência vs disponibilidade, flexibilidade vs performance).

## Casos de uso típicos

- Centralizar dados de vários sistemas num warehouse para BI confiável.
- Construir tabelas de faturamento/retenção que o time de produto consome.
- Entregar *datasets* limpos e *features* para treino de modelos de ML.
- Capturar eventos em tempo real para detecção de fraude ou recomendação.
- Garantir conformidade (LGPD) sobre dados pessoais.

## Habilidades do Data Engineer moderno

| Área | Exemplos |
| --- | --- |
| Programação | [Python](../../04-python-for-data-engineering/README.md), [SQL](../../05-sql/README.md) |
| Sistemas | [Linux](../../02-linux-shell-environment/README.md), [sistemas distribuídos](../05-distributed-systems-fundamentals/README.md) |
| Dados | [modelagem](../../07-data-modeling/README.md), [formatos](../../08-data-formats/README.md), [warehouse/lake](../../13-data-warehouse/README.md) |
| Plataforma | [cloud](../../19-cloud/README.md), [containers](../../20-containers/README.md), [IaC](../../22-infrastructure-as-code/README.md) |
| Produção | [CI/CD](../../23-cicd-dataops/README.md), [observabilidade](../../24-observability/README.md), [segurança](../../26-security/README.md) |

Não se domina tudo de uma vez — por isso existe o
[roadmap por níveis](../../README.md#roadmap-e-níveis).

## Erros comuns de quem está começando

- **Colecionar ferramentas** em vez de entender problemas. Saber "o que é
  Airflow" vale pouco sem entender *por que orquestração existe*.
- **Ignorar fundamentos** (SQL, modelagem, sistemas) achando que ferramentas
  compensam. Não compensam.
- **Pular qualidade e idempotência** — pipelines que "funcionam uma vez" não são
  engenharia.
- **Copiar arquiteturas de big tech** sem precisar da escala delas. A maioria
  dos problemas cabe em um PostgreSQL bem modelado.

## Boas práticas (mentalidade)

- Comece pelo problema de negócio e pelo consumidor do dado.
- Prefira a solução **mais simples que resolve** (KISS). Escale quando doer.
- Trate dados como produto: com dono, contrato, SLA e documentação.
- Automatize e versione tudo que for repetível.

## Relação com outros conceitos

- É a base de [DE vs outros papéis](../02-data-engineer-vs-other-roles/README.md).
- Se materializa no [ciclo de vida dos dados](../03-data-lifecycle/README.md).
- Culmina nas [plataformas de dados](../04-data-systems/README.md) e na
  [integração com ML](../../31-data-engineering-and-ml/README.md).

## Exercícios

1. **Conceitual.** Em 5 linhas, explique para um gestor não-técnico por que a
   empresa precisa de um Data Engineer, usando um problema concreto.
2. **Mapeamento.** Liste 5 fontes de dados de uma empresa fictícia de e-commerce
   e, para cada uma, uma pergunta de negócio que exigiria combiná-las.
3. **Trade-off.** Dê um exemplo em que a solução "mais escalável" seria a
   *errada* por ser cara/complexa demais para o problema.

## Referências

- Reis, J.; Housley, M. *Fundamentals of Data Engineering*. O'Reilly, 2022 —
  cap. 1.
- Kleppmann, M. *Designing Data-Intensive Applications*. O'Reilly, 2017 —
  prefácio e cap. 1.
- Documentação e blog de engenharia de empresas de dados (como referência de
  casos reais, lidos criticamente).
