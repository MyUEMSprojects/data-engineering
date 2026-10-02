# 26 — Security

> 🟣 Nível 7 — Production · Pré: [19 — Cloud](../19-cloud/README.md),
> [25 — Governance](../25-data-governance/README.md) · Próximo:
> [27 — Catalog & Metadata](../27-data-catalog-metadata/README.md)

**Segurança** em dados é proteger **confidencialidade, integridade e disponibilidade** das informações e dos
sistemas que as processam (a tríade **CIA**). Plataformas de dados concentram **ativos valiosos e
sensíveis** (PII, financeiro) — logo, são alvo e exigem segurança **embutida por design**, não adicionada
depois. Este módulo cobre os controles essenciais e a **LGPD**.

> Conteúdo educacional. Para decisões de conformidade/jurídicas, envolva segurança, jurídico e o DPO.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Autenticação e autorização](01-authn-authz/README.md) | Quem é você × o que pode fazer |
| 02 | [IAM](02-iam/README.md) | Identidade e acesso na nuvem/plataformas |
| 03 | [Criptografia](03-encryption/README.md) | Em repouso e em trânsito, chaves |
| 04 | [Gestão de secrets](04-secrets-management/README.md) | Credenciais e rotação |
| 05 | [Segurança de rede](05-network-security/README.md) | Isolamento e perímetro |
| 06 | [Menor privilégio](06-least-privilege/README.md) | Mínimo acesso necessário |
| 07 | [Mascaramento e PII](07-data-masking-pii/README.md) | Proteger dados pessoais |
| 08 | [LGPD](08-lgpd/README.md) | Lei Geral de Proteção de Dados |

## Dependências internas

```text
AuthN/AuthZ ─► IAM ─► Menor privilégio
                │
Criptografia ─► Gestão de secrets
                │
Segurança de rede ─► Mascaramento/PII ─► LGPD
```

## Checkpoint

- [ ] Explicar a tríade CIA e o modelo de ameaças básico para uma plataforma de dados.
- [ ] Diferenciar autenticação, autorização e contabilização (AAA).
- [ ] Aplicar IAM com roles/identidade federada em vez de chaves estáticas.
- [ ] Explicar criptografia em repouso/trânsito, KMS e envelope encryption.
- [ ] Gerenciar secrets com rotação e sem exposição em código/logs.
- [ ] Isolar rede (subnets privadas, endpoints, security groups).
- [ ] Aplicar menor privilégio, mascaramento, tokenização e tratar PII.
- [ ] Mapear obrigações da LGPD a controles técnicos.

## Referências do módulo

- OWASP (Top 10, Cheat Sheets); NIST Cybersecurity Framework e SP 800-53.
- AWS/GCP/Azure Security Best Practices e Well-Architected (Security Pillar).
- Anderson, R. *Security Engineering* (gratuito online).
- LGPD — Lei nº 13.709/2018; guias da ANPD.
