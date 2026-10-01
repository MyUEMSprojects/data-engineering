# Conceitos de governança de dados

> 🟣 Production · Parte de [25 — Data Governance](../README.md)

## O que é

**Data governance** é o exercício de **autoridade e controle** (políticas, padrões, papéis e processos)
sobre o gerenciamento de dados, para garantir que sejam **disponíveis, utilizáveis, íntegros, seguros e
conformes**. Responde: *quem decide o quê sobre os dados, segundo quais regras, e como isso é verificado.*

Distinga:

- **Governança** — *decisão e responsabilização* (políticas, papéis, direitos de decisão).
- **Gestão de dados (data management)** — a *execução* (pipelines, qualidade, segurança, metadados).
- **Engenharia de dados** — constrói os sistemas que **implementam** as políticas (controles técnicos).

## Por que existe

- **Confiança** — consumidores sabem o que significa e quão confiável é cada dado.
- **Conformidade** — LGPD/GDPR, setoriais (financeiro/saúde) exigem controle sobre dados pessoais ([compliance](../07-compliance-privacy/README.md)).
- **Segurança** — reduzir risco de vazamento/uso indevido ([security](../../26-security/README.md)).
- **Eficiência** — evitar duplicação, "números divergentes", retrabalho; acelerar descoberta.
- **Valor** — dados bem governados viram ativo para analytics/ML.

## Pilares

| Pilar | Foco | Onde |
| --- | --- | --- |
| **Metadados e catálogo** | saber o que existe e o que significa | [02](../02-metadata-catalog/README.md) |
| **Qualidade** | dados corretos e confiáveis | [Data Quality](../../12-data-quality/README.md) |
| **Lineage** | origem e destino dos dados | [03](../03-lineage/README.md) |
| **Ownership/stewardship** | responsabilidade clara | [04](../04-ownership-stewardship/README.md) |
| **Acesso e classificação** | quem acessa o quê, por sensibilidade | [05](../05-access-control-classification/README.md) |
| **Retenção e auditoria** | ciclo de vida e rastreabilidade | [06](../06-retention-auditing/README.md) |
| **Privacidade e compliance** | conformidade legal | [07](../07-compliance-privacy/README.md) |
| **Segurança** | proteção técnica | [Security](../../26-security/README.md) |
| **Arquitetura/interoperabilidade** | padrões, contratos | [08](../08-governance-architecture/README.md), [contracts](../../29-data-contracts/README.md) |

## Políticas, padrões e processos

- **Política** — declaração de intenção ("PII só é acessível por quem tem necessidade de negócio").
- **Padrão** — regra técnica verificável ("colunas PII classificadas e mascaradas; dados em bucket
  criptografado").
- **Processo** — fluxo para pedir acesso, aprovar mudança de schema, tratar incidente.
- **Controles** — mecanismos que **impõem/verificam** (IAM, mascaramento, testes, auditoria).

## Governança como **habilitadora** (não burocracia)

Má governança = comitês lentos, formulários, bloqueio. Boa governança:

- **Automatizada e embutida** no fluxo (policy-as-code, classificação automática, testes, catálogo vivo).
- **Self-service com guarda-corpos** — usuários acham e usam dados rapidamente dentro de limites seguros.
- **Proporcional ao risco** — controles fortes para PII/financeiro; leves para dados públicos/internos.
- **Federada**: responsabilidade perto de quem conhece o dado ([arquitetura](../08-governance-architecture/README.md),
  [data mesh](../../30-advanced/03-data-mesh/README.md)).

## Frameworks e referências

- **DAMA-DMBOK** — corpo de conhecimento de gestão de dados (11 áreas).
- **DCAM** (EDM Council), **COBIT**, **ISO 27001/27701** (segurança/privacidade), **NIST**.
- Princípios **FAIR** (Findable, Accessible, Interoperable, Reusable) para dados.

## Papéis típicos

| Papel | Função |
| --- | --- |
| **Data Owner** | dono executivo/de negócio; decide acesso e uso ([ownership](../04-ownership-stewardship/README.md)) |
| **Data Steward** | zela por qualidade, definições, metadados do domínio |
| **Data Custodian / Engineer** | implementa controles técnicos (DE, DBA, plataforma) |
| **DPO/Encarregado** | privacidade/LGPD ([compliance](../07-compliance-privacy/README.md)) |
| **Conselho/comitê de governança** | políticas e priorização (leve) |
| **Consumidores** | usam dados conforme políticas |

## O papel do Data Engineer

Você **implementa** governança: cataloga e documenta ([dbt docs](../../28-dbt/07-documentation-lineage/README.md)),
captura lineage, aplica classificação/mascaramento, configura acesso de menor privilégio, implementa
retenção/exclusão, gera trilhas de auditoria e testes de qualidade/contratos. **Governança que não vira
código não é verificada.**

## Maturidade

```text
Ad hoc → Reativa (corrige após incidente) → Definida (políticas/papéis) → Gerenciada (métricas, automação) → Otimizada (embutida, self-service, contínua)
```

Comece pelo **mais valioso/arriscado**: dados críticos (tier 1) e dados pessoais; evolua incrementalmente.

## Erros comuns

- Governança como projeto/comitê burocrático desconectado da engenharia.
- Políticas no papel sem controles técnicos que as imponham.
- Tentar governar tudo de uma vez (paralisia).
- Sem donos claros; catálogo desatualizado.
- Tratar governança como "problema de TI" (é compartilhado com o negócio).
- Segurança/compliance como bloqueio em vez de parceria.

## Boas práticas

- Foque em dados de maior risco/valor; automatize (policy-as-code, classificação, lineage).
- Papéis e ownership explícitos; métricas de governança (cobertura de catálogo, % classificado, SLAs).
- Self-service com guarda-corpos; revisão contínua das políticas.

## Relação com outros conceitos

- [Catálogo](../02-metadata-catalog/README.md), [ownership](../04-ownership-stewardship/README.md),
  [segurança](../../26-security/README.md), [data contracts](../../29-data-contracts/README.md),
  [data quality](../../12-data-quality/README.md), [data mesh](../../30-advanced/03-data-mesh/README.md).

## Exercícios

1. Diferencie governança, gestão de dados e engenharia de dados com exemplos.
2. Liste 5 controles técnicos que implementam uma política "PII só para quem precisa".
3. Proponha um plano em 3 fases para introduzir governança numa empresa sem nenhuma.
4. Descreva como a governança pode ser self-service e segura ao mesmo tempo.

## Referências

- DAMA-DMBOK 2; Eryurek et al., *Data Governance: The Definitive Guide*; princípios FAIR.
