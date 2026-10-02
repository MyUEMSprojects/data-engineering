# Compliance e privacidade

> 🟣 Production · Parte de [25 — Data Governance](../README.md)
>
> Os controles técnicos de segurança e os detalhes da LGPD estão em
> [26 — Security](../../26-security/README.md) e [LGPD](../../26-security/08-lgpd/README.md). Aqui: a visão
> de **governança** — mapear obrigações regulatórias a práticas de dados.
>
> ⚠️ Conteúdo educacional, **não é aconselhamento jurídico**. Consulte o jurídico/DPO para decisões
> concretas.

## O que é

- **Compliance (conformidade)** — aderir a **leis, regulamentos, normas e contratos** aplicáveis aos dados.
- **Privacidade** — proteger os **dados pessoais** e os **direitos dos titulares**, tratando-os de forma
  lícita, justa e transparente.

## Panorama regulatório (principais)

| Regulação | Escopo | Pontos-chave para dados |
| --- | --- | --- |
| **LGPD** (Lei 13.709/2018, Brasil) | dados pessoais de pessoas no Brasil | bases legais, direitos do titular, DPO, ANPD, notificação de incidente |
| **GDPR** (UE) | dados de residentes da UE | similar à LGPD; multas altas; transferências internacionais |
| **CCPA/CPRA** (Califórnia) | consumidores da Califórnia | direito de saber/excluir/não vender |
| **PCI-DSS** | dados de cartão de pagamento | segmentação, criptografia, controle de acesso |
| **HIPAA** (EUA) | dados de saúde | proteção de PHI |
| **SOX / BCBS 239 / regulação bancária (BCB/CMN)** | relatórios financeiros e risco | integridade, lineage, auditabilidade, qualidade de dados |
| **ISO 27001 / 27701 / SOC 2** | gestão de segurança/privacidade | frameworks de controles certificáveis |

## LGPD em resumo (visão do engenheiro)

### Conceitos

- **Dado pessoal** — informação relacionada a pessoa natural identificada/identificável.
- **Dado pessoal sensível** — origem racial/étnica, convicção religiosa/política, filiação sindical, saúde,
  vida sexual, genético/biométrico — **proteção reforçada**.
- **Titular** — a pessoa a quem os dados se referem. **Controlador** — quem decide o tratamento.
  **Operador** — quem trata em nome do controlador (muitas vezes a engenharia/fornecedor de nuvem).
- **Encarregado (DPO)** — canal com titulares e a **ANPD**.

### Princípios (art. 6º) → implicações técnicas

| Princípio | Em dados |
| --- | --- |
| **Finalidade / adequação** | usar o dado só para o propósito informado; propósito registrado no catálogo |
| **Necessidade (minimização)** | coletar/reter só o necessário — evite "guardar tudo" |
| **Livre acesso / transparência** | o titular consegue saber o que se faz com seus dados |
| **Qualidade dos dados** | exatidão e atualização ([data quality](../../12-data-quality/README.md)) |
| **Segurança** | proteção técnica e administrativa ([security](../../26-security/README.md)) |
| **Prevenção** | evitar danos |
| **Não discriminação** | sem fins discriminatórios (atenção a ML/features) |
| **Responsabilização e prestação de contas** | demonstrar conformidade (auditoria, registros) |

### Bases legais (art. 7º)

Tratar dados exige uma **base legal** (consentimento, cumprimento de obrigação legal, execução de
contrato, legítimo interesse, etc.). A base **limita a finalidade e a retenção**. Registre a base por
dataset/finalidade (catálogo).

### Direitos dos titulares (art. 18) → capacidades que a plataforma precisa ter

- **Confirmação e acesso** — localizar **todos** os dados do titular ([lineage](../03-lineage/README.md),
  classificação, chave de titular).
- **Correção** de dados incorretos.
- **Anonimização, bloqueio ou eliminação** de dados desnecessários/tratados sem base
  ([retenção/exclusão](../06-retention-auditing/README.md)).
- **Portabilidade** — exportar em formato estruturado.
- **Revogação do consentimento**, informação sobre compartilhamento, **revisão de decisões automatizadas**.

### Incidentes e transferência

- **Notificação** de incidente de segurança relevante à ANPD e aos titulares em prazo razoável
  ([incident response](../../24-observability/07-incident-response/README.md)).
- **Transferência internacional** (ex.: nuvem fora do Brasil) exige mecanismos/garantias.

## Privacy by design / by default

Embutir privacidade **desde a concepção**: coletar o mínimo, **pseudonimizar/anonimizar cedo**, segregar
PII, restringir acesso por padrão, definir retenção no desenho do pipeline — mais barato que retrofit.

## Técnicas de proteção de privacidade

- **Pseudonimização** — substituir identificadores por tokens/hashes (reversível com chave guardada à
  parte); ainda é dado pessoal.
- **Anonimização** — impossibilitar a reidentificação razoável (deixa de ser dado pessoal). Cuidado:
  **reidentificação** por combinação de atributos (k-anonimato, ruído/privacidade diferencial para
  agregados).
- **Mascaramento** (estático/dinâmico), **tokenização**, **criptografia** (por coluna/titular,
  *crypto-shredding*) — ver [masking/PII](../../26-security/07-data-masking-pii/README.md),
  [encryption](../../26-security/03-encryption/README.md).
- **Minimização e agregação** (publicar agregados, não linhas individuais).
- **Separação** de PII em schemas/tabelas restritas; tabela de **mapeamento titular↔token** isolada.

## Operacionalizando conformidade em dados

1. **Inventário e mapeamento** (ROPA — registro das operações de tratamento): quais dados pessoais, onde,
   por quê, base legal, quem acessa, retenção, compartilhamento — alimentado pelo [catálogo](../02-metadata-catalog/README.md)
   - [classificação](../05-access-control-classification/README.md) + [lineage](../03-lineage/README.md).
2. **Controles técnicos** automatizados (acesso, mascaramento, criptografia, retenção, auditoria).
3. **Processo de atendimento ao titular** (fluxo, SLAs, localizar/corrigir/excluir/exportar).
4. **RIPD/DPIA** (Relatório de Impacto) para tratamentos de alto risco (ML, dados sensíveis).
5. **Gestão de terceiros/operadores** (contratos, nuvem, SaaS de dados).
6. **Treinamento, auditoria e melhoria contínua**; evidências para a ANPD.

## Erros comuns

- Coletar e guardar "tudo" sem finalidade/base legal.
- Achar que anonimizar = trocar nome por ID (pseudonimização ainda é dado pessoal).
- Não conseguir localizar/excluir dados de um titular (sem inventário/lineage/chave).
- PII em ambientes de dev/teste, logs, notebooks, extratos soltos.
- Treinar ML com dados pessoais sem avaliar base/impacto/viés.
- Tratar compliance só como assunto jurídico, sem controles técnicos verificáveis.

## Boas práticas

- Privacy by design: minimizar, pseudonimizar cedo, segregar, reter pouco.
- Inventário vivo (catálogo+classificação+lineage); automatizar atendimento a titulares.
- Evidência contínua (auditoria, testes de política); RIPD para alto risco; incidente ensaiado.
- Trabalhar com jurídico/DPO desde o desenho.

## Relação com outros conceitos

- [Classificação/acesso](../05-access-control-classification/README.md), [retenção/auditoria](../06-retention-auditing/README.md),
  [lineage](../03-lineage/README.md), [security](../../26-security/README.md),
  [LGPD](../../26-security/08-lgpd/README.md), [DE + ML](../../31-data-engineering-and-ml/README.md).

## Exercícios

1. Mapeie 5 princípios da LGPD para controles técnicos concretos numa plataforma de dados.
2. Diferencie pseudonimização e anonimização e dê um risco de reidentificação.
3. Desenhe o fluxo técnico para atender um pedido de **eliminação** de dados de um titular.
4. Descreva um registro (ROPA) para o tratamento "dados de clientes para recomendação".

## Referências

- Lei nº 13.709/2018 (LGPD) e guias da **ANPD** (gov.br/anpd); GDPR (eur-lex); ISO/IEC 27701.
- Eryurek et al., *Data Governance: The Definitive Guide* — privacidade e conformidade.
