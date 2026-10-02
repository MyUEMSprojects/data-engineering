# CD — Entrega e deploy contínuos

> 🟣 Production · Parte de [23 — CI/CD & DataOps](../README.md)

## O que é

**CD** tem dois significados, ambos sobre **levar mudanças validadas à produção**:

- **Continuous Delivery (entrega contínua)** — todo commit que passa no [CI](../01-continuous-integration/README.md)
  produz um artefato **pronto para ir à produção**; o deploy é **um clique/aprovação** manual.
- **Continuous Deployment (deploy contínuo)** — o deploy em produção é **totalmente automático** após
  passar nos testes, sem aprovação humana.

```text
commit ─► CI (testa/constrói artefato) ─► deploy dev (auto) ─► deploy stg (auto) ─► [aprovação] ─► deploy prod
                                                                                    └─ (deployment contínuo: sem aprovação)
```

## Por que importa

Deploys manuais são lentos, arriscados e inconsistentes ("só o Fulano sabe subir"). CD torna o deploy
**rotineiro, repetível e de baixo risco**: mudanças pequenas e frequentes são mais fáceis de entender,
testar e reverter que grandes releases raros.

## Pilares

1. **Pipeline automatizado e único** — o mesmo processo para todo deploy.
2. **Construa uma vez, promova o mesmo artefato** — a imagem/pacote construído e testado é **o mesmo** que
   vai a stg e prod (não reconstrua por ambiente) — ver [artefatos](../04-environments-artifacts/README.md).
3. **Configuração externa** — o que muda por ambiente é config/segredo injetado ([12-factor](../../21-kubernetes/05-configmaps-secrets/README.md)).
4. **Deploys pequenos e frequentes**, com **rollback** fácil ([estratégias](../06-deployment-strategies/README.md)).
5. **Verificação pós-deploy** (smoke tests, health checks, monitoramento) e **rollback automático** se
   falhar.
6. **Auditável** — quem implantou o quê e quando (Git + logs do pipeline).

## O que se "implanta" em dados

| Artefato | Como entregar |
| --- | --- |
| **Código de pipeline** (Python) | imagem de [container](../../20-containers/README.md) → registry → orquestrador/K8s |
| **DAGs** (Airflow) | sincronizar do Git (git-sync) / build da imagem; validar import |
| **Modelos dbt** | `dbt build` no ambiente alvo ([dbt deployment](../../28-dbt/09-deployment/README.md)) |
| **Infraestrutura** | `terraform apply` ([IaC](../../22-infrastructure-as-code/README.md)) |
| **Migrações de schema** | scripts versionados (Alembic/Flyway/dbt) |
| **Serviços de serving** | Deployment/Helm com estratégia gradual |
| **Modelos de ML** | registry + deploy do modelo ([MLOps](../../31-data-engineering-and-ml/README.md)) |

## Particularidades de dados (por que é mais difícil que app)

- **Estado/dados persistem**: deploy de código é reversível; **dados já processados/escritos não** voltam
  sozinhos — exige idempotência, versionamento de tabelas/time travel ([lakehouse](../../15-lakehouse/README.md))
  e [backfill](../../09-etl-elt/08-backfill/README.md) para corrigir.
- **Mudanças de schema** afetam consumidores — compatibilidade/[contratos](../../29-data-contracts/README.md).
- **Mudança de lógica pode exigir reprocessar histórico** (full-refresh/backfill) — planeje custo e janela.
- **Validação com dados reais** é difícil em pré-produção — use staging com dados amostrados/mascarados
  ([masking](../../26-security/07-data-masking-pii/README.md)) e testes de dados pós-deploy.
- **Dependências entre pipelines** (ordem de deploy: dimensões antes de fatos).

## Gates e aprovações

- **Gates automáticos**: testes, scans de segurança, `plan` do Terraform, testes de dados, checagem de
  custo estimado.
- **Aprovação manual** em prod (environment protection rules) para mudanças de risco — comum em dados e
  IaC.
- **Janelas de mudança** e *freeze* em períodos críticos (fechamento contábil).

## Rollback e roll-forward

- **Rollback** — voltar ao artefato/versão anterior (rápido para código; para dados, usar time travel/
  restauração/reprocessamento).
- **Roll-forward** — corrigir com um novo deploy (frequentemente mais seguro em dados que "desfazer").
- Mantenha artefatos antigos disponíveis; versione tudo ([SemVer](../../03-git-software-engineering/04-conventional-commits-versioning/README.md)).

## Exemplo conceitual (GitHub Actions: promoção com aprovação)

```yaml
jobs:
  build:   # constrói e publica a imagem UMA vez (tag = SHA)
  deploy-stg:
    needs: build
    environment: staging          # secrets/vars do ambiente
  deploy-prod:
    needs: deploy-stg
    environment: production       # regra de proteção: exige aprovação manual
```

Detalhes no tópico [testing, build e deploy](../03-testing-build-deploy/README.md).

## Erros comuns

- Reconstruir o artefato para cada ambiente (o que roda em prod ≠ o que foi testado).
- Config/segredos dentro da imagem.
- Deploys manuais, grandes e raros.
- Sem plano de rollback (especialmente para mudanças de schema/dados).
- Deploy sem verificação pós-deploy/monitoramento.
- Esquecer a ordem de dependências entre pipelines/tabelas.

## Boas práticas

- Pipeline único, artefato imutável promovido entre ambientes, config externa.
- Gates automáticos + aprovação em prod; deploys pequenos e frequentes.
- Smoke tests e monitoramento pós-deploy; rollback/roll-forward documentados.
- Mudanças de schema compatíveis e em etapas (expand/contract).

## Relação com outros conceitos

- [CI](../01-continuous-integration/README.md), [ambientes/artefatos](../04-environments-artifacts/README.md),
  [estratégias de deploy](../06-deployment-strategies/README.md), [DataOps](../05-dataops/README.md),
  [IaC](../../22-infrastructure-as-code/README.md).

## Exercícios

1. Diferencie delivery de deployment contínuo e escolha para um pipeline financeiro e para um blog interno.
2. Descreva o fluxo "build uma vez, promova o artefato" para uma imagem de pipeline.
3. Por que rollback de dados é mais difícil que de código? Como mitigar?
4. Planeje o deploy de uma mudança de schema em etapas (expand/contract).

## Referências

- Humble, J.; Farley, D. *Continuous Delivery*; Forsgren et al. *Accelerate*.
