# 25 — Data Governance

> 🟣 Nível 7 — Production · Pré: [12 — Data Quality](../12-data-quality/README.md),
> [24 — Observability](../24-observability/README.md) · Próximo: [26 — Security](../26-security/README.md)

**Governança de dados** é o conjunto de **políticas, papéis, processos e controles** que garante que os
dados sejam **confiáveis, seguros, conformes e utilizáveis** pela organização. Não é burocracia — bem
feita, **habilita** o uso de dados em escala ao dar confiança e clareza sobre *o que existe, quem é dono,
quem pode acessar e como deve ser tratado*.

## Por que importa

Sem governança, plataformas viram **data swamps**: ninguém sabe o que significa cada tabela, quem é
responsável, se pode usar determinado dado (PII, [LGPD](../26-security/08-lgpd/README.md)), nem de onde
veio. Com ela, dados viram **produto confiável** e a empresa reduz risco regulatório.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Conceitos de governança](01-governance-concepts/README.md) | O que é, pilares, frameworks |
| 02 | [Metadados e catálogo](02-metadata-catalog/README.md) | Saber o que existe |
| 03 | [Lineage](03-lineage/README.md) | De onde vem e para onde vai |
| 04 | [Ownership e stewardship](04-ownership-stewardship/README.md) | Quem responde pelo dado |
| 05 | [Controle de acesso e classificação](05-access-control-classification/README.md) | Quem acessa o quê; sensibilidade |
| 06 | [Retenção e auditoria](06-retention-auditing/README.md) | Quanto tempo guardar; rastrear acessos |
| 07 | [Compliance e privacidade](07-compliance-privacy/README.md) | LGPD/GDPR e regulações |
| 08 | [Arquitetura de governança](08-governance-architecture/README.md) | Centralizada, federada, ferramentas |

## Dependências internas

```text
Conceitos ─► Metadados/catálogo ─► Lineage
     │
     ├─► Ownership/stewardship ─► Controle de acesso/classificação
     │                                  │
     └─► Retenção/auditoria ─► Compliance/privacidade ─► Arquitetura de governança
```

## Checkpoint

- [ ] Explicar os pilares da governança e seu valor (habilitar, não bloquear).
- [ ] Descrever metadados técnicos/negócio e o papel do catálogo.
- [ ] Usar lineage para impacto e auditoria.
- [ ] Definir ownership e stewardship para domínios/datasets.
- [ ] Classificar dados e aplicar controle de acesso por sensibilidade.
- [ ] Definir políticas de retenção e trilhas de auditoria.
- [ ] Mapear requisitos de LGPD/GDPR a controles técnicos.
- [ ] Comparar governança centralizada e federada.

## Referências do módulo

- DAMA International, *DAMA-DMBOK* (Data Management Body of Knowledge).
- Reis & Housley, *Fundamentals of Data Engineering* — data management.
- Eryurek, E. et al. *Data Governance: The Definitive Guide*. O'Reilly.
