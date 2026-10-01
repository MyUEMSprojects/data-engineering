# Exercícios — Módulo 25: Governança de dados

Teoria em [25-data-governance](../../25-data-governance/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Owner × steward

Qual a diferença entre **dono (owner)** e **steward** de um dado? Quem aprova acessos?

<details><summary>Gabarito</summary>

**Owner:** responsável de negócio pelo conjunto (decide uso, acessos e política). **Steward:** garante qualidade, definições e metadados no dia a dia. O owner (ou delegado) **aprova acessos**. Dado sem dono é dado sem governança. Ver [ownership](../../25-data-governance/04-ownership-stewardship/README.md).
</details>

## 2. 🟢 Conceitual — Classificação

Classifique: e-mail do cliente, CPF, métricas agregadas por região, senha com hash. Defina níveis (público/interno/confidencial/restrito).

<details><summary>Gabarito (um caminho)</summary>

Métricas agregadas → **interno**; e-mail → **confidencial** (PII); CPF → **restrito** (PII sensível); hash de senha → **restrito**. Classificação orienta controles: mascaramento, criptografia, quem acessa, retenção. Ver [controle de acesso e classificação](../../25-data-governance/05-access-control-classification/README.md).
</details>

## 3. 🔵 Implementação — Política de retenção

Defina e implemente (SQL/lifecycle) a retenção: logs de acesso 12 meses; dados de clientes inativos 5 anos; **direito ao esquecimento** a pedido.

<details><summary>Gabarito</summary>

```sql
DELETE FROM access_logs WHERE ts < now() - interval '12 months';
-- esquecimento: anonimizar/excluir em TODAS as camadas (bronze/silver/gold/backups conforme política)
UPDATE customers SET name = NULL, email = NULL, cpf = NULL, erased_at = now() WHERE customer_id = :id;
```
Desafios: propagar a exclusão para cópias derivadas (lake, features), backups (expiram por ciclo) e registrar **auditoria**. Ver [retenção e auditoria](../../25-data-governance/06-retention-auditing/README.md) e [LGPD](../../26-security/08-lgpd/README.md).
</details>

## 4. 🔵 Debugging — "Quem acessou esse dado?"

Um incidente exige saber quem leu a tabela `customers` nos últimos 30 dias, mas não há registro. O que faltou e o que implementar?

<details><summary>Gabarito</summary>

Faltou **auditoria de acesso**: habilitar logs de consulta/acesso (ex.: *audit logs* do warehouse, CloudTrail para S3), centralizar, proteger contra adulteração e definir retenção. Acesso por **papéis** (não contas compartilhadas) para atribuir ações a pessoas. Ver [retenção e auditoria](../../25-data-governance/06-retention-auditing/README.md).
</details>

## 5. 🟣 Arquitetura — Governança que não trava o time

Descreva como equilibrar controle e velocidade: o que centralizar e o que federar. Cite um mecanismo de *self-service* com guarda-corpos.

<details><summary>Gabarito</summary>

Centralize **padrões** (classificação, segurança, catálogo, políticas); federe a **propriedade e a execução** aos domínios. *Self-service* com guarda-corpos: provisionamento por IaC com **policy-as-code**, tags obrigatórias, mascaramento por classificação aplicado automaticamente, contratos validados no CI. Ver [arquitetura de governança](../../25-data-governance/08-governance-architecture/README.md) e [data mesh](../../30-advanced/03-data-mesh/README.md).
</details>

## 6. 🟣 Arquitetura — LGPD: mapeamento

Para uma empresa de e-commerce, liste as **etapas** para se adequar à LGPD no lado de dados (do inventário ao atendimento de titulares).

<details><summary>Gabarito</summary>

1) **Inventário** de dados pessoais e fluxos (catálogo/linhagem); 2) base legal e finalidade por tratamento; 3) minimização e **retenção**; 4) controles (acesso mínimo, criptografia, **mascaramento/pseudonimização**); 5) processo de **direitos do titular** (acesso, correção, exclusão); 6) gestão de incidentes (notificação); 7) DPO e registro das operações (RoPA); 8) auditoria. Ver [compliance e privacidade](../../25-data-governance/07-compliance-privacy/README.md).
</details>
