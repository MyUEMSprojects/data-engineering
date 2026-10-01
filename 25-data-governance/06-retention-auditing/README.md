# Retenção e auditoria

> 🟣 Production · Parte de [25 — Data Governance](../README.md)

## Retenção de dados

### O que é

**Retenção** é a política de **por quanto tempo** guardar cada tipo de dado e o que fazer ao fim
(**arquivar, anonimizar ou excluir**). Equilibra: **necessidade de negócio/analítica**, **obrigação legal**
(guardar por X anos), **custo** e **risco/privacidade** (não guardar além do necessário).

### Por que importa

- **Privacidade (LGPD)**: princípio da **necessidade/limitação de finalidade e de armazenamento** — dados
  pessoais só pelo tempo necessário à finalidade; depois, eliminar ou anonimizar ([compliance](../07-compliance-privacy/README.md)).
- **Obrigações legais**: certos registros devem ser **mantidos** (fiscais/contábeis, trabalhistas, logs de
  acesso — Marco Civil, regulação setorial).
- **Custo**: storage/backup/time travel acumulam ([cost](../../19-cloud/08-cost-management/README.md)).
- **Risco**: quanto mais dado guardado, maior a superfície em caso de vazamento.
- **Litígio**: *legal hold* pode **suspender** exclusões.

### Definindo a política

Por **categoria de dado** (não por tabela), com base legal/negócio:

| Categoria | Exemplo de retenção | Fim do ciclo |
| --- | --- | --- |
| Logs de aplicação/acesso | 6–12 meses (ou conforme lei) | excluir/agregar |
| Eventos brutos de clique (PII/IDs) | 13–24 meses | anonimizar/agregar |
| Dados transacionais/fiscais | prazo legal (ex.: 5+ anos) | arquivar (frio) → excluir |
| Dados pessoais de cliente | enquanto relação ativa + prazo legal | anonimizar/excluir |
| Agregados anonimizados | indefinido | manter |
| Backups | conforme RPO/legal | rotação |

Documente: **o quê, por quanto tempo, por quê (base), quem aprova, como é executado e verificado**. Owner
decide ([ownership](../04-ownership-stewardship/README.md)); jurídico/DPO valida.

### Implementação técnica

- **Lifecycle policies** em object storage (mover para frio / expirar) — [object storage](../../19-cloud/02-object-storage/README.md).
- **Particionamento por data** facilita expirar por partição (`DROP PARTITION`) em vez de `DELETE` caro
  ([partitioning](../../14-data-lake/05-partitioning/README.md)).
- **Tabelas/datasets com expiração** (BigQuery table expiration, TTL de partição); **TTL** em NoSQL/Kafka
  ([retenção do Kafka](../../18-message-brokers/05-ordering-retention-replay/README.md)).
- **Jobs de purge** orquestrados e auditados ([orquestração](../../11-orchestration/README.md)).
- **Anonimização/pseudonimização** para manter valor analítico sem identificar ([masking](../../26-security/07-data-masking-pii/README.md)).
- **Legal hold**: mecanismo para suspender a exclusão de dados sob investigação/litígio.

### O desafio: exclusão real em sistemas de dados

Excluir um titular (direito de eliminação — LGPD art. 18) é difícil em plataformas de dados:

- **Imutabilidade**: object storage/Parquet (precisa reescrever arquivos), logs Kafka (compactação/
  retenção), **backups**, time travel/snapshots ([lakehouse](../../15-lakehouse/README.md): `DELETE` +
  `VACUUM`/expire snapshots para realmente apagar).
- **Cópias e derivados** (lake, warehouse, extratos, BI, ML/features) → use [lineage](../03-lineage/README.md)
  para achar todos os lugares.
- **Backups** — política de rotação + *crypto-shredding* (apagar a chave de criptografia do titular/dataset).
- **Modelos de ML** treinados com o dado.

Projete para exclusão desde o início: **chave de titular** consistente, separar PII em tabelas isoladas
(facilita apagar), criptografia por titular/tenant, retenção curta em camadas brutas.

## Auditoria

### O que é

**Auditoria** é o **registro rastreável e imutável** de **quem fez o quê, quando, onde e (se possível)
por quê** com os dados e a infraestrutura — para **detecção, investigação, responsabilização e
comprovação de conformidade**.

### O que auditar

| Categoria | Exemplos |
| --- | --- |
| **Acesso a dados** | quem consultou/exportou tabelas sensíveis (query logs, data access logs) |
| **Mudanças de dados** | inserts/updates/deletes em dados críticos (CDC/audit tables) |
| **Mudanças de schema/config** | DDL, políticas, IAM, regras de mascaramento |
| **Acessos/permissões** | concessões, revogações, uso de break-glass, logins |
| **Operações de pipeline** | runs, quem acionou backfill/reprocessamento |
| **Infraestrutura** | chamadas de API de nuvem (CloudTrail/Audit Logs/Activity Log) |
| **Privacidade** | solicitações de titulares e atendimento |

### Como (técnico)

- **Logs nativos**: CloudTrail + S3 data events, GCP Cloud Audit Logs (Data Access), Azure Activity/Diagnostic
  Logs, `QUERY_HISTORY`/`ACCESS_HISTORY` (Snowflake), `INFORMATION_SCHEMA.JOBS` (BigQuery), pgaudit (Postgres).
- **Imutabilidade e integridade**: armazenar em bucket **WORM/Object Lock**, conta separada, com acesso
  restrito; assinatura/hash; proteger contra adulteração.
- **Centralização e retenção** (SIEM/data lake de auditoria); retenção conforme lei/política (muitas vezes
  anos).
- **Alertas sobre anomalias** (acesso em massa a PII, fora de horário, novo local) — [alertas](../../24-observability/04-alerting/README.md).
- **Revisões periódicas** de logs de acesso e de **recertificação de permissões** ([acesso](../05-access-control-classification/README.md)).
- **Não logar o próprio conteúdo sensível** nos logs de auditoria (registre quem/qual objeto, não o dado).

### Auditoria vs observabilidade

Logs operacionais ([logging](../../24-observability/01-logging/README.md)) servem à depuração e podem ser
descartáveis; **logs de auditoria** são **evidência** — com retenção, imutabilidade e acesso controlado.

## Erros comuns

- Sem política de retenção (acumular tudo "por via das dúvidas") ou reter menos que o exigido legalmente.
- Exclusão "lógica" que deixa dados em backups/snapshots/derivados/logs.
- Não conseguir localizar todas as cópias de um titular (sem lineage/classificação).
- Auditoria desligada ou sem retenção; logs de auditoria alteráveis por admins.
- Logs de auditoria com PII em claro; sem revisão (ninguém olha).
- Legal hold ignorado por jobs de purge automáticos.

## Boas práticas

- Política de retenção **por categoria**, aprovada por owner/jurídico, **automatizada** e verificada.
- Particionar por data; lifecycle/TTL; anonimizar para manter valor analítico; legal hold previsto.
- Projetar para exclusão (chaves de titular, PII isolada, crypto-shredding).
- Auditoria centralizada, imutável, retida e **monitorada**; revisão periódica de acessos.

## Relação com outros conceitos

- [Compliance/privacidade](../07-compliance-privacy/README.md), [classificação/acesso](../05-access-control-classification/README.md),
  [lineage](../03-lineage/README.md), [backup/DR](../../06-databases/09-backup-recovery-dr/README.md),
  [security](../../26-security/README.md), [cost](../../19-cloud/08-cost-management/README.md).

## Exercícios

1. Defina a política de retenção (período, base, fim do ciclo) para 5 categorias de dados de uma empresa.
2. Descreva como excluir os dados de um titular do lake (Parquet/Iceberg), warehouse, Kafka e backups.
3. Liste 6 eventos que você auditaria numa plataforma de dados e onde registrá-los.
4. Explique por que logs de auditoria devem ser imutáveis e como garantir isso.

## Referências

- LGPD (arts. 15, 16, 18); Marco Civil da Internet (guarda de logs); documentação de CloudTrail/Cloud Audit
  Logs/Snowflake ACCESS_HISTORY; Delta/Iceberg (DELETE, VACUUM/expire snapshots).
