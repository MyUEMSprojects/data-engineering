# Incident response

> 🟣 Production · Parte de [24 — Observability](../README.md)

## O que é

**Incident response** é o processo de **detectar, responder, mitigar, resolver e aprender** com falhas que
afetam consumidores de dados/sistemas. Em plataformas de dados, incidentes típicos: dados atrasados/
incorretos, pipeline quebrado, vazamento de dados, custo descontrolado, schema quebrado na origem.

## Por que ter um processo

Sob pressão, improvisar leva a confusão, demora e erros (e a piorar o incidente). Um processo claro
reduz o **MTTD** (tempo até detectar), **MTTA** (reconhecer) e **MTTR** (resolver), protege a confiança
nos dados e transforma falhas em **aprendizado**.

## O ciclo de vida

```text
Detectar ─► Triar/classificar ─► Comunicar ─► Mitigar ─► Resolver ─► Recuperar dados ─► Pós-mortem ─► Prevenir
```

### 1. Detecção

Idealmente por [alertas](../04-alerting/README.md)/monitores de [frescor e qualidade](../06-data-freshness/README.md),
**antes** do consumidor. Se o usuário detecta primeiro, melhore a observabilidade.

### 2. Triagem e severidade

Classifique por **impacto** (quem/o quê afeta, quão crítico, há dados incorretos já consumidos?):

| Sev | Exemplo em dados | Resposta |
| --- | --- | --- |
| **SEV1** | dados financeiros/regulatórios errados; vazamento de PII; plataforma toda fora | imediata, all-hands, comunicação executiva |
| **SEV2** | dataset tier-1 atrasado/incorreto, dashboard executivo afetado | prioritária, on-call + dono |
| **SEV3** | dataset secundário degradado, workaround existe | no expediente |
| **SEV4** | problema menor/cosmético | backlog |

### 3. Papéis (para incidentes maiores)

**Incident Commander** (coordena, decide), **responsáveis técnicos** (investigam/mitigam), **comunicação**
(atualiza stakeholders), **scribe** (registra a linha do tempo). Em incidentes pequenos, uma pessoa
acumula papéis.

### 4. Comunicação

Atualize **proativamente** consumidores e stakeholders (canal de incidente, status page): o que está
acontecendo, impacto, ETA/próxima atualização. Transparência preserva a confiança — **dado errado
silencioso é pior** que dado atrasado avisado. Marque datasets afetados ([catálogo](../../27-data-catalog-metadata/README.md)).

### 5. Mitigação (parar o sangramento primeiro)

Prioridade: **reduzir impacto**, mesmo antes de achar a causa raiz:

- **Pausar** pipelines/consumidores a jusante para não propagar dado ruim;
- **Reverter** a mudança recente (rollback de código/config — [deploy](../../23-cicd-dataops/06-deployment-strategies/README.md));
- **Servir o último estado bom** (snapshot/time travel — [lakehouse](../../15-lakehouse/README.md));
- Aplicar workaround/manual; **sinalizar** dados suspeitos.

### 6. Diagnóstico e resolução

Use [logs](../01-logging/README.md), [métricas](../02-metrics/README.md), [traces](../03-tracing/README.md) e
[lineage](../../10-data-pipelines/06-data-lineage/README.md) (de onde veio / quem é afetado). Método:
**o que mudou?** (deploy, fonte, schema, volume, config, nuvem) → hipótese → teste → registre. Siga o
[roteiro de troubleshooting](../../02-linux-shell-environment/08-logs-and-troubleshooting/README.md).

### 7. Recuperação de dados

Corrija a causa e **repare os dados**: reprocesse/[backfill](../../09-etl-elt/08-backfill/README.md)
(pipelines **idempotentes** tornam isso seguro), restaure de snapshot/backup
([DR](../../06-databases/09-backup-recovery-dr/README.md)), reconcilie com a fonte, notifique consumidores
sobre **janelas de dados corrigidas** (números históricos mudaram).

### 8. Pós-mortem (aprender)

Documento **blameless** (sem culpados; foco em sistema/processo) em até alguns dias:

- Resumo, **impacto** (quem/quanto tempo/quais dados), **linha do tempo**.
- **Causa raiz** (e fatores contribuintes — "5 porquês").
- O que funcionou/não funcionou na detecção e resposta.
- **Ações corretivas** com dono e prazo (testes novos, alertas, contrato, automação, runbook).
- Compartilhe amplamente; acompanhe a execução das ações.

## Runbooks e preparação

- **Runbooks** por alerta/cenário crítico (sintoma → diagnóstico → mitigação → escalonamento).
- **On-call** sustentável, com escalonamento e acesso adequado (menor privilégio + *break-glass*).
- **Simulações/game days**: ensaie falhas (queda de fonte, schema quebrado, restauração de backup).
- **Dependências mapeadas** (lineage/ownership) para saber quem acionar.
- Contatos de fornecedores/fontes upstream.

## Incidentes de segurança/privacidade (dados)

Vazamento/exposição de PII exige trilha própria: **contenção imediata**, preservar evidências, acionar
segurança/jurídico/DPO, e **notificação** a ANPD/titulares quando aplicável ([LGPD](../../26-security/08-lgpd/README.md),
[security](../../26-security/README.md)). Rotacione credenciais comprometidas.

## Métricas de resposta

**MTTD**, **MTTA**, **MTTR**, nº de incidentes por severidade, % detectados por monitoramento vs por
usuários, reincidência. Use para melhorar o processo, não para punir.

## Erros comuns

- Buscar causa raiz antes de mitigar (impacto cresce).
- Não comunicar (stakeholders descobrem sozinhos; perda de confiança).
- Deixar dado ruim propagar a jusante.
- Corrigir sem reparar/reprocessar os dados afetados nem avisar sobre números alterados.
- Pós-mortem com culpados ou sem ações/donos.
- Sem runbooks; conhecimento só na cabeça de uma pessoa.

## Boas práticas

- Severidades claras; papéis definidos; comunicação proativa; mitigar primeiro.
- Pipelines idempotentes + time travel/backups para recuperar dados.
- Pós-mortem blameless com ações rastreadas; runbooks e game days.
- Melhore a detecção a cada incidente (novo alerta/teste/contrato).

## Relação com outros conceitos

- [Alertas](../04-alerting/README.md), [SLOs](../05-sli-slo-sla/README.md),
  [freshness](../06-data-freshness/README.md), [handling failures](../../09-etl-elt/11-handling-failures/README.md),
  [backfill](../../09-etl-elt/08-backfill/README.md), [DR](../../06-databases/09-backup-recovery-dr/README.md),
  [DataOps](../../23-cicd-dataops/05-dataops/README.md).

## Exercícios

1. Classifique 4 incidentes de dados em SEV1–SEV4 e descreva a primeira ação de mitigação de cada.
2. Escreva um modelo de pós-mortem blameless para "tabela de vendas com valores duplicados por 6h".
3. Descreva como usar lineage para achar causa e raio de impacto de um número errado.
4. Planeje um game day: "a fonte mudou o tipo de uma coluna".

## Referências

- Google SRE Book — Managing Incidents, Postmortem Culture; *SRE Workbook* — Incident Response.
- PagerDuty Incident Response Guide; Atlassian Incident Management Handbook.
