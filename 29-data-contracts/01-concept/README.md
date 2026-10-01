# Conceito e motivação

> 🟣 Advanced · Parte de [29 — Data Contracts](../README.md)

## O que é

Um **data contract** é um **acordo formal** entre o **produtor** de um dado e seus **consumidores**,
descrevendo **o que o dado é, como se comporta e o que o produtor garante** — de forma **legível por humanos
e executável por máquinas**. Equivale a uma **API para dados**: assim como uma API tem contrato (OpenAPI),
um dataset publicado deve ter o seu.

> Já introduzido sob a ótica de qualidade em [data contracts (qualidade)](../../12-data-quality/02-data-contracts/README.md).
> Este módulo é o tratamento completo.

## O problema que resolve

```text
Time de App renomeia coluna "valor" → "amount" (sem avisar)
        │
        ▼
Pipeline de ingestão quebra (ou, pior, grava NULL em silêncio)
        │
        ▼
Dashboard executivo mostra receita zerada · modelo de ML degrada · time de dados apaga incêndio
```

Causas estruturais:

- **Acoplamento implícito** — o consumidor depende de detalhes internos (schema físico) do produtor, que nem
  sabe que é consumido.
- **Ownership difuso** — "o dado é de quem?"
- **Qualidade tratada a jusante** — o time de dados "conserta" o que o produtor quebra, repetidamente.
- **Mudança sem processo** — sem aviso, versão ou compatibilidade.

## O que o contrato resolve

- **Torna dependências explícitas** (quem consome o quê).
- **Coloca a responsabilidade na origem** ("shift-left"): quem produz **garante** a qualidade e **negocia**
  mudanças.
- **Estabilidade com evolução**: mudanças compatíveis fluem; incompatíveis exigem processo
  ([compatibilidade](../04-compatibility-versioning/README.md)).
- **Automação**: o contrato é **verificado** no CI e em runtime ([contract testing](../05-contract-testing/README.md)).
- **Confiança** para consumo em escala (self-service, ML, terceiros).

## O que um contrato cobre

| Elemento | Conteúdo | Tópico |
| --- | --- | --- |
| **Schema** | campos, tipos, nulabilidade, chaves, formatos | [02](../02-schema-semantics/README.md) |
| **Semântica** | significado, unidades, domínio de valores, regras de negócio, granularidade | [02](../02-schema-semantics/README.md) |
| **Qualidade** | unicidade, completude, faixas, integridade referencial ([dimensões](../../12-data-quality/01-dimensions-of-quality/README.md)) | [02](../02-schema-semantics/README.md) |
| **SLAs/SLOs** | frescor, disponibilidade, latência ([SLO](../../24-observability/05-sli-slo-sla/README.md)) | [03](../03-ownership-producer-consumer/README.md) |
| **Ownership** | dono, canal de suporte, on-call | [03](../03-ownership-producer-consumer/README.md) |
| **Compatibilidade/versão** | política de mudança, depreciação | [04](../04-compatibility-versioning/README.md) |
| **Segurança/privacidade** | classificação (PII), acesso, retenção, base legal ([governança](../../25-data-governance/README.md)) | [02](../02-schema-semantics/README.md) |
| **Termos de uso** | finalidade permitida, limites | [03](../03-ownership-producer-consumer/README.md) |

## Exemplo mínimo (YAML)

```yaml
dataContractSpecification: 1.0.0         # ilustrativo (ver ODCS/datacontract.com para o formato vigente)
id: orders.v1
info:
  title: Pedidos
  version: 1.2.0
  owner: time-pedidos@empresa.com
models:
  orders:
    description: "Um registro por pedido confirmado."
    fields:
      order_id:   { type: string,  required: true, unique: true }
      customer_id:{ type: string,  required: true, pii: false }
      amount:     { type: decimal, required: true, description: "Valor total em BRL, com impostos", minimum: 0 }
      status:     { type: string,  enum: [CREATED, PAID, SHIPPED, CANCELED] }
      created_at: { type: timestamp, required: true, description: "UTC" }
servicelevels:
  freshness: { threshold: 1h }
  availability: 99.5%
```

## Onde os contratos vivem

- **No repositório do produtor** (próximo ao código/schema) — versionados em Git, revisados por PR.
- Publicados num **catálogo/registry** para descoberta ([catálogo](../../27-data-catalog-metadata/README.md)).
- Complementam (não substituem) o [schema registry](../../08-data-formats/05-avro/README.md) (que cobre só
  schema) e os [testes de qualidade](../../12-data-quality/README.md).

## Contrato vs conceitos próximos

| | Foco | Relação |
| --- | --- | --- |
| **Schema registry** | schema + compatibilidade (Avro/Protobuf) | **parte** de um contrato (estrutura) |
| **Testes de qualidade** | verificar o dado que chegou | **mecanismo** de verificação do contrato |
| **SLA** | promessa de nível de serviço | **parte** do contrato |
| **Data product** (mesh) | dado como produto, com contrato, dono e SLAs | o contrato é a **interface** do produto |
| **Documentação** | explica | o contrato é **executável/verificável** |

## Origem das ideias

APIs (OpenAPI), **consumer-driven contracts** (Pact) em microsserviços, **schema registries** em streaming
e o movimento de **data mesh/data products**. O ecossistema converge para **especificações abertas**
(ODCS, Data Contract Specification).

## Quando adotar (e quando não)

- **Adote** onde há **dependências entre times**, dados críticos (financeiro, ML, regulatório), fontes
  internas que mudam, ou arquitetura federada/mesh.
- **Não precisa de peso total** para um script pessoal ou fonte estável sem consumidores — comece leve
  (schema + dono + SLA) e **evolua**.
- Contratos **não substituem cultura**: sem diálogo produtor↔consumidor e ownership real, viram papel.

## Erros comuns

- Escrever contratos que ninguém verifica (documento morto).
- Contrato só de schema, sem semântica/qualidade/SLA/dono.
- Impor aos produtores sem entender o consumo (resistência) ou criar contratos "no vácuo" pelo time de dados.
- Sem processo de mudança/versionamento; contratos desatualizados.
- Tentar cobrir **tudo** de uma vez (comece pelos datasets críticos).

## Boas práticas

- Contratos **no repositório do produtor**, versionados e verificados no CI.
- Cubra schema + semântica + qualidade + SLA + ownership + política de mudança.
- Negocie **com os consumidores**; comece pelos dados tier-1; iterar.
- Automatize verificação e notificação de mudanças ([contract testing](../05-contract-testing/README.md)).

## Relação com outros conceitos

- [Data quality/contracts (intro)](../../12-data-quality/02-data-contracts/README.md),
  [schema evolution](../../08-data-formats/10-schema-evolution/README.md),
  [governança](../../25-data-governance/README.md), [data mesh](../../30-advanced/03-data-mesh/README.md),
  [DataOps](../../23-cicd-dataops/05-dataops/README.md).

## Exercícios

1. Descreva um incidente real/hipotético causado por mudança não comunicada e como um contrato o evitaria.
2. Liste o que você incluiria num contrato do dataset `pedidos` (schema, semântica, qualidade, SLA, dono).
3. Diferencie contrato, schema registry e teste de qualidade.
4. Quando um contrato "leve" basta e quando é preciso o completo?

## Referências

- datacontract.com; Open Data Contract Standard (Bitol/Linux Foundation);
  Confluent — Data Contracts; Pact (pact.io); Dehghani, *Data Mesh*.
