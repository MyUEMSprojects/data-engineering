# 23 — CI/CD e DataOps

> 🟣 Nível 7 — Production · Pré: [03 — Git/SWE](../03-git-software-engineering/README.md),
> [20 — Containers](../20-containers/README.md), [22 — IaC](../22-infrastructure-as-code/README.md) ·
> Próximo: [24 — Observability](../24-observability/README.md)

**CI/CD** automatiza validar e entregar mudanças; **DataOps** aplica a mentalidade DevOps (automação,
colaboração, feedback rápido, qualidade contínua) ao ciclo de vida de **dados e pipelines**. Juntos, são
o que transforma código de pipeline em **produção confiável**: toda mudança passa por testes
automáticos e é implantada de forma repetível e reversível.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [CI — integração contínua](01-continuous-integration/README.md) | Validar cada mudança automaticamente |
| 02 | [CD — entrega/deploy contínuos](02-continuous-delivery/README.md) | Entregar com segurança |
| 03 | [Testing, build e deploy](03-testing-build-deploy/README.md) | O pipeline de ponta a ponta com GitHub Actions |
| 04 | [Ambientes e artefatos](04-environments-artifacts/README.md) | dev/stg/prod, artefatos versionados |
| 05 | [DataOps](05-dataops/README.md) | Práticas e cultura para dados |
| 06 | [Estratégias de deploy](06-deployment-strategies/README.md) | Blue/green, canary, rollback |

## Dependências internas

```text
CI ─► CD ─► Testing/build/deploy ─► Ambientes/artefatos ─► Estratégias de deploy
                    │
                    └────────────► DataOps (junta tudo para dados)
```

## Checkpoint

- [ ] Explicar CI, CD (delivery) e deployment contínuo.
- [ ] Montar um workflow no GitHub Actions: lint → testes → build → deploy.
- [ ] Gerenciar ambientes e artefatos versionados e imutáveis.
- [ ] Aplicar testes de dados e de pipeline no CI.
- [ ] Escolher estratégia de deploy (rolling, blue/green, canary) e planejar rollback.
- [ ] Descrever os princípios de DataOps e como aplicá-los.

## Referências do módulo

- Humble, J.; Farley, D. *Continuous Delivery*. Addison-Wesley.
- Documentação do GitHub Actions; *Accelerate* (Forsgren et al.) — métricas DORA.
- DataOps Manifesto (dataopsmanifesto.org).
