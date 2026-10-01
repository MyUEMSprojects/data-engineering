# LGPD (Lei Geral de Proteção de Dados)

> 🟣 Production · Parte de [26 — Security](../README.md)

> ⚠️ **Aviso**: material **educacional**, não é aconselhamento jurídico. A LGPD é interpretada pela **ANPD**
> e pelo Judiciário; para decisões concretas, consulte o jurídico/DPO. Verifique sempre o texto legal e as
> orientações vigentes da ANPD (gov.br/anpd).

## O que é

A **Lei nº 13.709/2018 (LGPD)** regula o **tratamento de dados pessoais** no Brasil — por pessoa natural ou
jurídica, de direito público ou privado, **inclusive em meios digitais** — com o objetivo de proteger
direitos de **liberdade, privacidade e livre desenvolvimento da personalidade**. Em vigor (sanções desde
ago/2021); fiscalizada pela **ANPD** (Autoridade Nacional de Proteção de Dados). Tem forte inspiração no
GDPR europeu.

## Por que o Data Engineer precisa conhecer

Plataformas de dados **concentram** dados pessoais e os replicam por lake, warehouse, BI, ML e logs. Atender
a LGPD **depende de capacidades técnicas** que a engenharia constrói: localizar dados de um titular,
corrigir/excluir/exportar, limitar acesso, reter só o necessário, registrar tratamentos, notificar
incidentes. Compliance que não vira **controle técnico** não é verificável.

## Conceitos (art. 5º)

| Termo | Significado |
| --- | --- |
| **Dado pessoal** | informação relacionada a pessoa natural **identificada ou identificável** |
| **Dado pessoal sensível** | origem racial/étnica, convicção religiosa, opinião política, filiação sindical/religiosa/política, **saúde, vida sexual, dado genético ou biométrico** |
| **Titular** | pessoa natural a quem os dados se referem |
| **Controlador** | quem **decide** sobre o tratamento (a empresa) |
| **Operador** | quem trata dados **em nome** do controlador (fornecedores, nuvem, SaaS; às vezes a engenharia/terceiros) |
| **Encarregado (DPO)** | canal entre controlador, titulares e ANPD |
| **Tratamento** | qualquer operação: coleta, armazenamento, uso, compartilhamento, eliminação... |
| **Anonimização** | dado que **não permite** identificar o titular por meios técnicos razoáveis (deixa de ser dado pessoal) |
| **Consentimento** | manifestação livre, informada e inequívoca para finalidade determinada |

## Princípios (art. 6º) → implicações técnicas

| Princípio | O que exige | Controle típico |
| --- | --- | --- |
| **Finalidade** | propósito legítimo, específico e informado | registrar finalidade por dataset; barrar uso incompatível |
| **Adequação** | tratamento compatível com a finalidade | revisão de uso |
| **Necessidade (minimização)** | só o **mínimo necessário** | coletar menos; descartar campos; [mascarar/segregar](../07-data-masking-pii/README.md) |
| **Livre acesso** | titular consulta de forma fácil e gratuita | fluxo de acesso aos dados |
| **Qualidade dos dados** | exatidão, clareza, atualização | [data quality](../../12-data-quality/README.md), correção |
| **Transparência** | informações claras ao titular | catálogo/registro de tratamentos |
| **Segurança** | medidas técnicas e administrativas | [criptografia](../03-encryption/README.md), [IAM](../02-iam/README.md), [rede](../05-network-security/README.md) |
| **Prevenção** | evitar danos | [observabilidade](../../24-observability/README.md), [incident response](../../24-observability/07-incident-response/README.md) |
| **Não discriminação** | sem fins discriminatórios/abusivos | atenção a viés em [ML/features](../../31-data-engineering-and-ml/README.md) |
| **Responsabilização e prestação de contas** | **demonstrar** conformidade | [auditoria](../../25-data-governance/06-retention-auditing/README.md), documentação |

## Bases legais (art. 7º; sensíveis: art. 11)

O tratamento exige **base legal**. Principais (art. 7º): **consentimento**; **cumprimento de obrigação
legal/regulatória**; execução de **políticas públicas**; **estudos por órgão de pesquisa**; execução de
**contrato** ou procedimentos preliminares; exercício regular de direitos em processo; **proteção da vida**;
**tutela da saúde**; **legítimo interesse** (com avaliação e salvaguardas); **proteção do crédito**. Para
**dados sensíveis**, o rol é mais restrito (art. 11).

Engenharia: **registre a base legal por dataset/finalidade** (catálogo) — ela **limita finalidade e
retenção**. Se a base é consentimento, é preciso **rastrear e honrar a revogação**.

## Direitos dos titulares (art. 18) → capacidades da plataforma

| Direito | Capacidade técnica necessária |
| --- | --- |
| **Confirmação e acesso** | localizar **todos** os dados do titular em todos os sistemas (identificador consistente, [lineage](../../25-data-governance/03-lineage/README.md), inventário) |
| **Correção** | corrigir em origem e propagar ([CDC/pipelines](../../09-etl-elt/06-cdc/README.md)) |
| **Anonimização, bloqueio ou eliminação** de dados desnecessários/excessivos/tratados irregularmente | **exclusão** em lake/warehouse/backups ([retenção/exclusão](../../25-data-governance/06-retention-auditing/README.md)) |
| **Portabilidade** | exportar em formato estruturado ([formatos](../../08-data-formats/README.md)) |
| **Eliminação dos dados tratados com consentimento** | idem + revogação |
| **Informação sobre compartilhamento** | registro de com quem os dados foram compartilhados |
| **Revogação do consentimento** | desativar uso e propagar |
| **Revisão de decisões automatizadas** | explicabilidade em ML ([DE + ML](../../31-data-engineering-and-ml/README.md)) |

### O desafio da exclusão (resumo técnico)
Dados vivem em **object storage imutável, Parquet, logs de Kafka, snapshots/time travel, backups, derivados,
features/modelos de ML, cópias em BI**. Estratégias: **chave de titular** consistente; **PII isolada** em
tabelas/schemas próprios; lakehouse `DELETE` + `VACUUM`/expiração de snapshots ([Delta](../../15-lakehouse/04-delta-lake/README.md)/[Iceberg](../../15-lakehouse/05-apache-iceberg/README.md));
**crypto-shredding** (apagar a chave); rotação de backups; **lineage** para achar derivados; Kafka com
compactação/retenção/tombstones.

## Governança do tratamento

- **Registro das operações de tratamento (ROPA)** — o que, por quê, base legal, quem acessa, retenção,
  compartilhamento (art. 37). Alimentado por **catálogo + classificação + lineage**
  ([governança](../../25-data-governance/07-compliance-privacy/README.md)).
- **RIPD (Relatório de Impacto à Proteção de Dados Pessoais)** — para tratamentos de risco (dados sensíveis,
  larga escala, ML, decisões automatizadas); a ANPD pode solicitar.
- **Privacidade desde a concepção e por padrão** (*privacy by design/by default*).
- **Gestão de operadores/terceiros** (contratos, nuvem, SaaS de dados) e de **transferência internacional**
  (nuvem fora do Brasil exige base/garantias — arts. 33–36).
- **Treinamento** e governança interna.

## Segurança e incidentes (arts. 46–49)

- Adotar **medidas de segurança** técnicas e administrativas aptas a proteger os dados (acesso, criptografia,
  rede, monitoramento — este módulo).
- **Comunicar à ANPD e ao titular** incidente de segurança que possa acarretar **risco ou dano relevante**,
  em prazo razoável (a ANPD regulamenta prazos/conteúdo) — tenha **plano de resposta** ensaiado
  ([incident response](../../24-observability/07-incident-response/README.md)).

## Sanções (art. 52)

Advertência, **multa simples de até 2% do faturamento** (limitada a R$ 50 milhões por infração), multa
diária, publicização da infração, **bloqueio/eliminação** dos dados, suspensão parcial/total do banco de
dados ou da atividade de tratamento. Além do dano reputacional e de ações dos titulares/MP.

## Mapeamento: LGPD → controles técnicos (resumo)

| Obrigação | Controle em dados |
| --- | --- |
| Saber o que se trata | catálogo, classificação, lineage, ROPA |
| Minimizar | coleta mínima; mascaramento; agregação; retenção curta |
| Base legal/finalidade | metadado por dataset; controle de uso |
| Segurança | IAM/menor privilégio, criptografia, rede privada, secrets, auditoria |
| Direitos do titular | busca por titular, exclusão/correção/exportação automatizadas |
| Retenção | lifecycle/TTL, expiração de snapshots, legal hold |
| Incidentes | monitoramento, runbook, notificação |
| Terceiros/transferência | contratos, avaliação de nuvem/SaaS, regiões de dados |
| Prestação de contas | trilhas de auditoria, documentação, testes de política |

## Erros comuns

- Tratar LGPD como "assunto do jurídico" sem controles técnicos que a sustentem.
- Coletar/guardar tudo "porque pode ser útil" (viola necessidade/finalidade).
- Não conseguir localizar/excluir os dados de um titular (sem inventário/chave/lineage).
- Achar que pseudonimizar = anonimizar (continua sendo dado pessoal).
- PII em dev/teste, logs, notebooks, planilhas e extratos soltos.
- Ignorar derivados e backups na exclusão; sem plano de incidente.
- Usar dados pessoais em ML sem avaliar base legal, finalidade e impacto.

## Boas práticas

- **Inventário vivo** (catálogo + classificação + lineage) e base legal/finalidade por dataset.
- **Privacy by design**: minimizar, pseudonimizar cedo, segregar PII, reter pouco.
- Capacidades **automatizadas** para atender titulares; exclusão projetada desde o início.
- Segurança em camadas + auditoria; incidente ensaiado; RIPD para alto risco.
- Trabalhe lado a lado com **jurídico e DPO**; revise conforme orientações da ANPD.

## Relação com outros conceitos

- [Mascaramento/PII](../07-data-masking-pii/README.md), [criptografia](../03-encryption/README.md),
  [IAM](../02-iam/README.md), [compliance/privacidade (governança)](../../25-data-governance/07-compliance-privacy/README.md),
  [retenção/auditoria](../../25-data-governance/06-retention-auditing/README.md),
  [lineage](../../25-data-governance/03-lineage/README.md), [DE + ML](../../31-data-engineering-and-ml/README.md).

## Exercícios

1. Para um pipeline de e-commerce, identifique dados pessoais, base legal plausível e finalidade de cada
   dataset (e quais seriam sensíveis).
2. Desenhe o fluxo técnico de atendimento a uma solicitação de **eliminação** de dados (lake, warehouse,
   Kafka, backups, ML).
3. Mapeie 6 princípios da LGPD a controles técnicos concretos na plataforma.
4. Escreva um esboço de registro de tratamento (ROPA) para "dados de clientes para recomendação".

## Referências

- **Lei nº 13.709/2018** (planalto.gov.br); site e guias da **ANPD** (gov.br/anpd), incluindo orientações sobre
  incidentes, encarregado e agentes de tratamento.
- GDPR (eur-lex.europa.eu) como referência comparada; ISO/IEC 27701.
- Eryurek et al., *Data Governance: The Definitive Guide* (privacidade).
