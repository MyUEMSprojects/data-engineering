# Compatibilidade e versionamento

> 🟣 Advanced · Parte de [29 — Data Contracts](../README.md)

> Base conceitual em [schema evolution](../../08-data-formats/10-schema-evolution/README.md) e
> [versionamento/SemVer](../../03-git-software-engineering/04-conventional-commits-versioning/README.md).
> Aqui: aplicação a **contratos de dados** de ponta a ponta.

## O problema: evoluir sem quebrar

Dados vivem anos; necessidades mudam. O contrato precisa permitir **evolução** (novos campos, correções)
**sem quebrar** consumidores existentes — e, quando a quebra é inevitável, **gerenciá-la** com processo.

## Tipos de compatibilidade

Do ponto de vista de **quem lê** o dado (consumidor) vs **quem escreveu** (produtor):

| Tipo | Garantia | Mudanças permitidas (exemplos) |
| --- | --- | --- |
| **Backward** | consumidor **novo** lê dados **antigos** | remover campo (opcional); adicionar campo **com default** |
| **Forward** | consumidor **antigo** lê dados **novos** | adicionar campo opcional; remover campo **com default** |
| **Full** | ambas | só o que atende às duas |
| **None** | nenhuma garantia | qualquer mudança (perigoso) |

> Para **datasets/tabelas** (muitos consumidores com versões diferentes), geralmente se exige
> **compatibilidade total ou "aditiva"**: **só adicionar** (campos opcionais), nunca remover/renomear/mudar
> tipo sem nova versão major. Em **streaming** com Schema Registry, escolha a política (BACKWARD é comum;
> `*_TRANSITIVE` considera todas as versões anteriores).

## Mudanças seguras vs quebradoras

```text
SEGURAS (não quebram):
  + adicionar campo OPCIONAL/nullable (ou com default)
  + adicionar valor a um enum — SÓ se o contrato diz que consumidores toleram valores novos
  + relaxar restrição (aceitar mais valores) no que o produtor emite*
  + ampliar precisão compatível (int32→int64), em formatos que suportem
  + melhorar documentação/descrição

QUEBRADORAS (breaking):
  - remover ou renomear campo
  - mudar TIPO ou SEMÂNTICA (unidade, fuso, grão, significado de enum)
  - tornar campo opcional → obrigatório (para o produtor) / apertar validações
  - mudar chave/unicidade, particionamento que consumidores assumem
  - mudar frequência/atraso (frescor) de forma que viole o SLA
  - remover valores de enum / reinterpretar valores existentes
```

> **Mudança de semântica sem mudança de schema é a pior breaking change** (silenciosa): a coluna `amount`
> passa de reais para centavos. Trate como **major** mesmo que o schema "não mude".

## Versionamento do contrato (SemVer)

`MAJOR.MINOR.PATCH`:

- **MAJOR** — mudança **incompatível** (breaking): exige migração dos consumidores.
- **MINOR** — adição **compatível** (novo campo opcional, novo dataset derivado).
- **PATCH** — correção sem alterar a interface (descrição, regra de qualidade que corrige bug).

Identifique a **versão major no endereço** do dado quando múltiplas versões coexistem:
`orders.v1`/`orders.v2`, tópico `orders-v2`, schema/dataset versionado. Consumidores **fixam a major** que
usam.

## Estratégia para breaking changes: **expand → migrate → contract**

```text
EXPAND:   publicar a nova versão ao lado da antiga (v2 junto de v1) — ou adicionar campo novo mantendo o antigo
MIGRATE:  consumidores migram para v2 dentro de um prazo; o produtor monitora quem ainda usa v1 (lineage/uso)
CONTRACT: após o prazo (e uso zero), desliga v1 (depreciação formal)
```

Elementos do processo:

- **Anúncio** antecipado e **janela de coexistência** definida no contrato (ex.: 90 dias).
- **Depreciação**: marcar `deprecated`, data de sunset, **alertas** aos consumidores que ainda leem v1
  (via catálogo/queries — [lineage](../../27-data-catalog-metadata/02-lineage-column-lineage/README.md)).
- **Dual-write/dual-publish** durante a transição: produtor mantém v1 e v2 alimentadas.
- **Ferramentas de transformação** podem derivar v1 a partir de v2 (camada de compatibilidade) para
  facilitar a migração.
- **Rollback**: possibilidade de reverter se a v2 falhar.

## Compatibilidade em cada camada técnica

| Camada | Como garantir |
| --- | --- |
| **Streaming (Kafka)** | [Schema Registry](../../08-data-formats/05-avro/README.md) rejeita schemas incompatíveis conforme a política; regras de compatibilidade por tópico |
| **Tabelas (warehouse/lakehouse)** | contratos de modelo no dbt (`contract: enforced`), [schema evolution](../../15-lakehouse/README.md) controlada; **só adicionar colunas**; views estáveis sobre tabelas físicas |
| **APIs/arquivos** | JSON Schema/OpenAPI + testes de compatibilidade; versionamento no path/nome |
| **Parquet/arquivos** | evolução por **nome/ID de coluna** ([Iceberg](../../15-lakehouse/05-apache-iceberg/README.md) por ID); cuidado com reordenar/renomear |

### View estável como "interface pública"
Exponha aos consumidores uma **view/camada pública versionada** (`analytics.orders_v1`) sobre o modelo
interno, que pode **refatorar livremente** — a view é o **contrato**; absorve mudanças internas
([views](../../05-sql/06-views-materialized-views/README.md)).

## Detectando incompatibilidades automaticamente

- **Diff de schema** entre a versão publicada e a proposta (no PR): classificar mudanças em
  compatível/breaking.
- **Schema Registry compatibility check** no CI (Avro/Protobuf/JSON Schema).
- Ferramentas: `datacontract breaking`, `buf breaking` (Protobuf), `avro-compat`, dbt `contract`,
  **schemathesis/oasdiff** (APIs).
- **Regras semânticas**: testes de regressão sobre amostras (valores/escala não mudaram) e verificação de
  estatísticas (anomalia de distribuição pós-mudança — [anomaly detection](../../12-data-quality/07-anomaly-detection/README.md)).

```bash
# conceitual: o CI compara o contrato do PR com o publicado e falha em breaking change sem bump major
datacontract breaking datacontract.yaml --against origin/main:datacontract.yaml
```

## Política de mudança no contrato (exemplo)

```yaml
changePolicy:
  compatibility: backward_transitive    # ilustrativo
  breakingChange:
    requires: [major_version_bump, migration_plan, consumer_ack]
    coexistenceDays: 90
  deprecation:
    notice: 90d
    channels: ["#dados-anuncios", "email:consumers"]
  enumPolicy: consumers_must_tolerate_unknown_values
```

## Erros comuns

- Renomear/remover campo "porque ninguém usa" sem checar consumo.
- Mudar semântica/unidade sem tratar como breaking.
- Sem coexistência: cortar v1 imediatamente.
- Não saber quem consome (sem lineage/registro) → impossível avaliar impacto.
- Enum "fechado" no produtor e "aberto" no consumidor (ou vice-versa) sem política.
- Compatibilidade verificada só em schema, ignorando semântica/frescor.
- Versionar sem **fixar** versão no consumidor (migração forçada).

## Boas práticas

- **Evoluir por adição**; versionar com SemVer; breaking = major + coexistência + migração.
- **Automatizar** o check de compatibilidade no CI (schema + regras semânticas) e a notificação aos
  consumidores.
- Interface pública estável (view/tópico versionado) isolando refatorações internas.
- Consumidores **tolerantes** (ignoram campos novos; tratam enums desconhecidos).
- Medir uso de versões antigas; desligar com dados, não com achismo.

## Relação com outros conceitos

- [Schema evolution](../../08-data-formats/10-schema-evolution/README.md), [Avro/Schema Registry](../../08-data-formats/05-avro/README.md),
  [versionamento](../../03-git-software-engineering/04-conventional-commits-versioning/README.md),
  [estratégias de deploy (expand/contract)](../../23-cicd-dataops/06-deployment-strategies/README.md),
  [contract testing](../05-contract-testing/README.md).

## Exercícios

1. Classifique como compatível ou breaking: (a) novo campo opcional; (b) `amount` de reais → centavos;
   (c) novo valor em enum; (d) tornar `email` obrigatório; (e) renomear `uf`→`state`.
2. Planeje a migração `orders.v1`→`v2` (renomear campos) com coexistência de 90 dias.
3. Desenhe uma view pública versionada que isola o modelo interno e explique o benefício.
4. Descreva o check de compatibilidade no CI e o que ele deve bloquear.

## Referências

- Semantic Versioning 2.0.0; Confluent Schema Registry — Schema Evolution and Compatibility;
  Kleppmann, *DDIA* (cap. 4); Protobuf/Avro compatibility rules; Fowler, M. — Parallel Change (expand/contract).
