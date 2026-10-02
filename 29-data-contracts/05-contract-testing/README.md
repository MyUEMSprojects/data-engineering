# Contract testing

> 🟣 Advanced · Parte de [29 — Data Contracts](../README.md)

## O que é

**Contract testing** é verificar **automaticamente** que o produtor **cumpre** o contrato e que os
consumidores **dependem apenas do que está contratado**. É o que transforma o contrato de **documento** em
**garantia executável**. Verifica em **três momentos**: antes de mudar (CI), antes de publicar (gate) e
continuamente em produção (monitoramento).

```text
PR do produtor ──► [CI: compatibilidade + testes de contrato] ──► deploy ──► [gate/runtime: valida dado publicado] ──► [monitor: SLAs/qualidade]
                          ▲ consumidores declaram expectativas (consumer-driven)
```

## O que testar

| Aspecto | Teste | Quando |
| --- | --- | --- |
| **Schema** | o dado/evento/tabela tem os campos/tipos esperados | CI + runtime |
| **Compatibilidade** | a mudança proposta não quebra versões/consumidores | CI (PR) |
| **Qualidade/semântica** | unicidade, nulos, faixas, enums, FKs, regras de negócio | runtime/gate |
| **SLA/frescor/volume** | dado chegou no prazo e no volume esperado | runtime/monitor |
| **Expectativas do consumidor** | campos/garantias que **cada consumidor** usa continuam válidos | CI (consumer-driven) |
| **Privacidade/segurança** | campos PII classificados/mascarados conforme contrato | CI + runtime |

## Estratégias

### 1. Provider-side (verificação pelo produtor) — a base

O **produtor** valida seu dado/evento/tabela **contra o contrato** antes de publicar:

- **No CI**: gera dados/exemplos, valida contra o schema/regras; testa o **código** que produz o dado.
- **No pipeline (gate)**: antes de promover/publicar (`write-audit-publish`): escreve numa tabela de
  *staging*, **audita** (testes de contrato/qualidade) e só então **publica** (swap) — consumidores nunca
  veem dado que viola o contrato ([deploy de tabelas](../../23-cicd-dataops/06-deployment-strategies/README.md)).
- **No produtor de eventos**: serialização com **Schema Registry** (rejeita payload incompatível) +
  validação de regras semânticas antes de emitir ([Kafka producers](../../18-message-brokers/03-producers-consumers/README.md)).

### 2. Consumer-driven contract testing (CDC)

**Consumidores declaram** o que **precisam** (campos, tipos, valores); o **produtor** roda esses testes no CI
**antes de mudar**, garantindo que **nenhum consumidor real quebra**. Origem: **Pact** em microsserviços.

```text
Consumidor A: "uso order_id (string), amount (decimal>=0), status ∈ {PAID,CANCELED}"
Consumidor B: "uso created_at (UTC) e customer_id"
Produtor: mudança proposta remove `status` → CI FALHA: consumidor A quebraria
```

Vantagem: protege **usos reais** (e permite remover o que ninguém usa). Custo: coordenação entre times.
Em dados, ainda é menos padronizado que em APIs — combine com [lineage](../../27-data-catalog-metadata/02-lineage-column-lineage/README.md)
para descobrir consumidores e seus campos usados.

### 3. Consumer-side (defesa na entrada)

O **consumidor** também **valida** o que recebe (não confia cegamente): rejeita/quarentena registros
inválidos e **alerta** quando o contrato é violado ([validação](../../09-etl-elt/10-data-validation/README.md),
[schema validation](../../12-data-quality/03-schema-validation/README.md)). Defesa em profundidade.

### 4. Monitoramento contínuo (runtime)

Testes agendados/em cada run sobre o dado em produção (frescor, volume, distribuição, qualidade) com
**alertas ao dono** ([data freshness](../../24-observability/06-data-freshness/README.md),
[alertas](../../24-observability/04-alerting/README.md), [anomalias](../../12-data-quality/07-anomaly-detection/README.md)).

## Ferramentas

| Ferramenta | Uso |
| --- | --- |
| **Data Contract CLI** (`datacontract`) | `lint`, `test` (roda checagens do contrato na fonte), `breaking` (diff entre versões), `export` (gera SQL/dbt/Avro/JSON Schema) |
| **dbt** — *model contracts* + tests | `contract: {enforced: true}` impõe colunas/tipos; tests (`unique`, `not_null`, `relationships`, `accepted_values`) ([dbt tests](../../28-dbt/05-tests/README.md)) |
| **Great Expectations / Soda / Pandera** | expectativas de qualidade sobre os dados ([qualidade](../../12-data-quality/README.md)) |
| **Schema Registry** (Confluent/Apicurio) | compatibilidade de schema Avro/Protobuf/JSON em streaming |
| **Pact / Pactflow** | consumer-driven contracts (APIs; adaptável a eventos) |
| **buf** (Protobuf), `oasdiff` (OpenAPI) | detectar breaking changes |
| **OpenMetadata/DataHub** | contratos + qualidade + lineage integrados ([ferramentas](../../27-data-catalog-metadata/04-tools/README.md)) |

## Exemplo: teste de contrato no CI (conceitual)

```yaml
# .github/workflows/contract.yml
jobs:
  contract:
    steps:
      - uses: actions/checkout@v4
      - run: pip install datacontract-cli
      - run: datacontract lint datacontract.yaml
      - run: datacontract breaking datacontract.yaml --against origin/main:datacontract.yaml   # bloqueia breaking sem bump major
      - run: dbt build --select tag:contract --target ci                                       # contratos de modelo + testes
      - run: pytest tests/contract/                                                           # expectativas dos consumidores
```

(Confira comandos/flags na documentação da versão que usar.)

## Padrão Write–Audit–Publish (WAP)

```text
WRITE:   escreve o novo dado em staging (invisível aos consumidores)
AUDIT:   roda testes de contrato/qualidade sobre o staging
PUBLISH: se passou → publica atomicamente (swap/branch merge/partition exchange); senão → bloqueia + alerta (quarentena)
```

Com lakehouse (branches do Iceberg/Nessie, Delta) ou swap de tabelas, é a forma mais robusta de **nunca
expor dado que viola o contrato** ([lakehouse](../../15-lakehouse/README.md), [ACID](../../15-lakehouse/03-acid-on-object-storage/README.md)).

## Política de falha

Decida por regra: **bloquear** (violações graves: schema quebrado, PK duplicada), **quarentenar** linhas
ruins e seguir, ou **avisar** (violações leves) — mapeia hard vs soft ([expectation testing](../../12-data-quality/04-expectation-testing/README.md)).
Toda violação **notifica o dono** do contrato ([ownership](../03-ownership-producer-consumer/README.md)).

## Pirâmide de testes de contrato

```text
        ╱ monitoramento contínuo (prod) ╲        poucos checks críticos, sempre ligados
      ╱ gate/WAP antes de publicar        ╲
    ╱ CI: compatibilidade + testes de contrato ╲  em todo PR
  ╱ lint do contrato (sintaxe/campos obrigatórios) ╲  barato, sempre
```

## Erros comuns

- Contrato verificado só manualmente ou só em prod (tarde).
- Só checar schema; ignorar semântica/qualidade/frescor.
- Não rodar compatibilidade no PR (breaking descoberta após deploy).
- Consumidores sem testes de suas expectativas; produtor sem saber o que quebra.
- Falsos positivos que levam a ignorar/desligar os testes.
- Sem dono para tratar violações; alerta que ninguém recebe.
- Testes que dependem de dados de produção/PII.

## Boas práticas

- Verifique em **3 pontos**: CI (compatibilidade), gate (WAP) e runtime (monitor).
- Combine provider-side + consumer-driven + defesa na entrada.
- Gere testes **a partir do contrato** (fonte única) — dbt/GX/CLI — evitando divergência.
- Regras com severidade (hard/soft); alertas ao dono; dados de teste sintéticos.
- Mantenha os testes rápidos e confiáveis; revise regras quando o negócio mudar.

## Relação com outros conceitos

- [Compatibilidade/versionamento](../04-compatibility-versioning/README.md),
  [implementação](../06-implementation/README.md), [dbt tests](../../28-dbt/05-tests/README.md),
  [expectation testing](../../12-data-quality/04-expectation-testing/README.md),
  [pipeline testing](../../10-data-pipelines/07-pipeline-testing/README.md), [CI](../../23-cicd-dataops/01-continuous-integration/README.md).

## Exercícios

1. Escreva um conjunto de testes de contrato (schema + 4 regras de qualidade) para `orders`.
2. Desenhe um fluxo Write–Audit–Publish para uma tabela de fatos e o que acontece em falha.
3. Mostre como um teste consumer-driven impediria remover o campo `status`.
4. Configure (conceitualmente) um job de CI que bloqueia breaking changes sem bump major.

## Referências

- Pact docs (consumer-driven contracts); Data Contract CLI (datacontract.com);
  dbt model contracts; Confluent Schema Registry; padrão Write-Audit-Publish (Netflix/Iceberg).
