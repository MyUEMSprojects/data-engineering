# Ownership, produtor e consumidor

> 🟣 Advanced · Parte de [29 — Data Contracts](../README.md)

## A relação contratual

Um contrato de dados é, fundamentalmente, um **acordo entre pessoas/times** — com **direitos e deveres**
dos dois lados — que depois é **codificado e verificado**. Sem papéis claros, é só documentação.

```text
   PRODUTOR (owner)  ──publica dado conforme o contrato──►  CONSUMIDOR(ES)
   garante schema, qualidade, SLA,                          dependem do contrato; respeitam termos de uso;
   notifica/negocia mudanças                                avisam sobre necessidades e quebras
```

## Ownership (dono do contrato)

**Todo contrato tem um dono nomeado** — time/pessoa **responsável** pelo dataset: responde por qualidade,
suporte, mudanças e incidentes ([ownership/stewardship](../../25-data-governance/04-ownership-stewardship/README.md)).
Registre no contrato: `owner`, canal de suporte (Slack/e-mail), **on-call**, escalonamento.

> **Dado sem dono** = contrato sem validade. Em mesh, o dono é o **time de domínio produtor** do data
> product ([data mesh](../../30-advanced/03-data-mesh/README.md)).

## Responsabilidades do produtor

- **Publicar** o dado em conformidade com o contrato (schema, semântica, qualidade, frescor).
- **Verificar** o contrato **antes de publicar** (no CI e em runtime — [contract testing](../05-contract-testing/README.md)):
  quebrar o contrato bloqueia o deploy/publicação.
- **Gerir mudanças**: seguir a política de [compatibilidade e versionamento](../04-compatibility-versioning/README.md);
  **avisar** consumidores com antecedência (depreciação com prazo); manter versões antigas durante a
  transição.
- **Manter** SLAs/SLOs, monitorar, **responder a incidentes** ([incident response](../../24-observability/07-incident-response/README.md)).
- **Documentar** e manter o contrato atualizado; **conhecer seus consumidores** (via catálogo/lineage).
- **Tratar o dado como produto** (qualidade, estabilidade, suporte) e não como "exaustão" de um sistema.

## Responsabilidades do consumidor

- **Declarar a dependência** (registrar-se como consumidor — no catálogo/registry/contrato) para ser
  notificado de mudanças ([lineage/impacto](../../27-data-catalog-metadata/03-catalogs-discovery/README.md)).
- **Usar conforme os termos** (finalidade permitida, classificação/PII, retenção) —
  [LGPD](../../26-security/08-lgpd/README.md).
- **Ser tolerante a mudanças compatíveis**: ignorar campos novos, tolerar novos valores de enum quando o
  contrato assim definir (princípio de Postel/"leitor tolerante").
- **Comunicar necessidades**: pedir campos/garantias adicionais; reportar defeitos de qualidade ao dono.
- **Migrar** dentro do prazo quando uma versão é depreciada.
- **Não depender de comportamento não contratado** (campos não documentados, ordem de linhas, formatos
  incidentais).
- **Validar a entrada** na fronteira (defesa em profundidade) — [validação](../../09-etl-elt/10-data-validation/README.md).

## Quem escreve o contrato? (modelos)

| Modelo | Como funciona | Prós | Contras |
| --- | --- | --- | --- |
| **Produtor-driven** | produtor define e publica | escala; responsabilidade na origem | pode ignorar necessidades do consumo |
| **Consumidor-driven (CDC — Consumer-Driven Contracts)** | consumidores declaram o que **precisam**; produtor garante que não quebra | protege usos reais; evita over-spec | exige coordenação; muitos consumidores |
| **Negociado/colaborativo** (recomendado) | produtor propõe, consumidores revisam; mudança por **PR** | alinhamento, adesão | requer cultura/processo |

Na prática: **produtor é dono e publica**, **consumidores participam** (revisam PRs, declaram dependências).

## O processo de mudança (governança do contrato)

```text
1. Produtor propõe mudança (PR no contrato/schema)
2. CI: verifica compatibilidade; lista consumidores impactados (lineage/registro)
3a. Mudança COMPATÍVEL (adicionar campo opcional) → merge, notificação informativa
3b. Mudança INCOMPATÍVEL (breaking) → nova versão MAJOR + plano de migração:
      anúncio ─► período de coexistência (v1 e v2) ─► migração dos consumidores ─► depreciação ─► desligamento v1
4. Atualiza catálogo/documentação; comunica
```

Detalhes em [compatibilidade e versionamento](../04-compatibility-versioning/README.md). Acordos
(prazos de depreciação, janela de coexistência, canais) fazem parte do contrato.

## Níveis de serviço e consequências

Defina **SLOs** por dataset e o que acontece ao descumprir: alerta ao dono, *error budget*, **congelamento
de mudanças**, escalonamento; para fronteiras externas/críticas, **SLA** formal
([SLI/SLO/SLA](../../24-observability/05-sli-slo-sla/README.md)). Sem consequências, SLOs são aspiração.

## Mecanismos organizacionais

- **Registro de consumidores** no catálogo/contrato (quem consome o quê).
- **CODEOWNERS** e revisão obrigatória do dono/consumidores críticos em mudanças de contrato.
- **Canal/rito** de comunicação (anúncios de mudança, calendário de depreciações).
- **Fóruns/guilda** para padrões e resolução de conflitos.
- **Métricas**: % de datasets críticos com contrato, nº de breaking changes evitados, tempo de migração,
  incidentes por mudança de schema.

## Contratos entre times vs com terceiros

- **Internos**: foco em colaboração, automação, versionamento.
- **Externos/terceiros** (fornecedores de dados, APIs): contrato **formal/legal**, SLAs com penalidade,
  validação rigorosa na ingestão ("não confiar") e plano B ([validação](../../09-etl-elt/10-data-validation/README.md)).

## Erros comuns

- Contrato sem dono nomeado / sem canal de suporte.
- Produtor desconhece quem consome (muda sem avisar).
- Consumidor depende de campos/comportamentos não contratados.
- Breaking change sem coexistência/prazo de migração.
- Contrato imposto pelo time de dados à fonte sem consulta (resistência) — ou ignorado pelo produtor.
- SLOs sem consequência; contratos desatualizados.

## Boas práticas

- Dono + canal + on-call explícitos; registro de consumidores via catálogo/lineage.
- Mudança por PR com verificação automática de compatibilidade e notificação a consumidores.
- Política clara de depreciação e coexistência; consumidores tolerantes a mudanças compatíveis.
- Tratar dados como produto; medir adoção e incidentes por mudança.

## Relação com outros conceitos

- [Ownership/stewardship](../../25-data-governance/04-ownership-stewardship/README.md),
  [compatibilidade/versionamento](../04-compatibility-versioning/README.md),
  [contract testing](../05-contract-testing/README.md), [catálogo/lineage](../../27-data-catalog-metadata/README.md),
  [data mesh](../../30-advanced/03-data-mesh/README.md), [incident response](../../24-observability/07-incident-response/README.md).

## Exercícios

1. Liste direitos e deveres do produtor e dos consumidores de um dataset `pedidos`.
2. Descreva o processo de uma breaking change (renomear `valor`→`amount`) com prazos e coexistência.
3. Compare contrato produtor-driven, consumer-driven e colaborativo; recomende um para o seu contexto.
4. Defina 4 métricas para acompanhar a saúde dos contratos na organização.

## Referências

- Pact — Consumer-Driven Contracts (docs.pact.io); Dehghani, *Data Mesh* (data as a product);
  Open Data Contract Standard; Google SRE Book (SLOs/error budgets).
