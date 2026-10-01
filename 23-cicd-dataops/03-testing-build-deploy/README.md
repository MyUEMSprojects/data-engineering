# Testing, build e deploy (GitHub Actions)

> 🟣 Production · Parte de [23 — CI/CD & DataOps](../README.md)

## O que é

O pipeline de ponta a ponta que **testa**, **constrói** e **implanta** um projeto de dados, implementado
com **GitHub Actions** (a mesma lógica vale para GitLab CI, Jenkins, CircleCI, Cloud Build). Aqui juntamos
[CI](../01-continuous-integration/README.md) e [CD](../02-continuous-delivery/README.md) num exemplo
concreto.

## Conceitos do GitHub Actions

| Conceito | Significado |
| --- | --- |
| **Workflow** | arquivo YAML em `.github/workflows/` |
| **Event** (`on:`) | gatilho: `push`, `pull_request`, `schedule`, `workflow_dispatch`, `release` |
| **Job** | conjunto de steps num runner (rodam em paralelo por padrão; `needs:` define ordem) |
| **Step** | comando (`run`) ou *action* reutilizável (`uses`) |
| **Runner** | máquina (GitHub-hosted ou self-hosted) |
| **Secrets / Variables** | segredos e config por repo/ambiente |
| **Environment** | alvo (`staging`, `production`) com regras de proteção/aprovação e secrets próprios |
| **Artifacts / cache** | compartilhar saídas entre jobs / acelerar dependências |

## Pipeline completo (exemplo)

```yaml
name: pipeline
on:
  pull_request:
  push: { branches: [main] }

permissions: { contents: read, id-token: write, packages: write }   # OIDC + registry

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check . && black --check . && mypy src/
      - run: pytest -q --cov=src

  build:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    outputs: { tag: ${{ steps.meta.outputs.version }} }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
      - id: meta
        run: echo "version=sha-${GITHUB_SHA::7}" >> "$GITHUB_OUTPUT"
      - uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}/pipeline:${{ steps.meta.outputs.version }}

  scan:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/${{ github.repository }}/pipeline:${{ needs.build.outputs.tag }}
          severity: CRITICAL,HIGH
          exit-code: "1"

  deploy-staging:
    needs: [build, scan]
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: aws-actions/configure-aws-credentials@v4     # OIDC, sem chaves estáticas
        with: { role-to-assume: ${{ vars.DEPLOY_ROLE }}, aws-region: us-east-1 }
      - run: ./scripts/deploy.sh staging ${{ needs.build.outputs.tag }}

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production        # exige aprovação (protection rule)
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ vars.DEPLOY_ROLE }}, aws-region: us-east-1 }
      - run: ./scripts/deploy.sh production ${{ needs.build.outputs.tag }}
```

> Pin de versões de actions: prefira `@vN` fixo ou SHA (em `trivy-action`, use uma tag/SHA fixa em vez de
> `@master` em produção) por segurança da cadeia de suprimentos.

## Estágios e o que cada um garante

1. **Test** — lint/tipos/unitários/integração ([CI](../01-continuous-integration/README.md)); para dados:
   `dbt build` em schema efêmero, validação de DAGs, testes de contrato.
2. **Build** — artefato imutável (imagem/pacote/wheel) com **tag rastreável** (SHA/SemVer), publicado em
   registry ([registries](../../20-containers/05-registries/README.md)).
3. **Scan** — vulnerabilidades/segredos; falha bloqueia ([container security](../../20-containers/07-container-security/README.md)).
4. **Deploy** — promove **o mesmo artefato** (staging → prod) via script/Helm/Terraform/`dbt`/orquestrador,
   com verificação pós-deploy.

## Deploy de pipelines de dados (formas comuns)

```bash
# imagem de pipeline: atualizar a tag usada pelo orquestrador (Helm/K8s)
helm upgrade --install etl ./chart --set image.tag=sha-a1b2c3d -n dados-prod

# infraestrutura
terraform -chdir=envs/prod plan  -out tfplan   # revisado no PR
terraform -chdir=envs/prod apply tfplan

# modelos dbt
dbt build --target prod --select state:modified+ --defer --state ./prod-artifacts
```

(ver [dbt deployment](../../28-dbt/09-deployment/README.md), [IaC](../../22-infrastructure-as-code/README.md),
[Kubernetes](../../21-kubernetes/README.md)).

## Autenticação segura: OIDC

Em vez de guardar **chaves de nuvem de longa duração** em secrets, use **OIDC federado**: o GitHub emite um
token de curta duração que a nuvem troca por credenciais temporárias de uma role de **menor privilégio**
([IAM](../../19-cloud/06-iam-secrets/README.md)). Escopo por `environment` (prod só com aprovação).

## Boas práticas de pipeline

- **Cache** de dependências; **jobs paralelos**; `paths` filters; reusable workflows/composite actions (DRY).
- **Concurrency groups** para não rodar deploys simultâneos no mesmo ambiente.
- **Permissões mínimas** (`permissions:`) por workflow/job.
- **Pin** de actions/versões; revisar workflows como código ([PR](../../03-git-software-engineering/03-pull-requests-code-review/README.md)).
- **Notificações** de falha (Slack) e *summary* do job.
- **Idempotência do deploy** (reexecutar não quebra) e **verificação pós-deploy** (smoke test).

## Erros comuns

- Secrets de produção acessíveis a PRs de forks / sem escopo por ambiente.
- Chaves estáticas de nuvem no CI.
- Reconstruir a imagem em cada ambiente.
- `latest`/`@master` sem pin; permissões `write-all`.
- Pipeline sem scan nem gate de aprovação em prod.
- Deploys concorrentes sobrepondo-se.

## Relação com outros conceitos

- [CI](../01-continuous-integration/README.md), [CD](../02-continuous-delivery/README.md),
  [ambientes/artefatos](../04-environments-artifacts/README.md), [IaC](../../22-infrastructure-as-code/README.md),
  [containers/registries](../../20-containers/05-registries/README.md); CI deste repo: [`ci.yml`](../../.github/workflows/ci.yml).

## Exercícios

1. Monte um workflow test → build → scan → deploy-staging → deploy-prod (com aprovação).
2. Substitua chaves estáticas por OIDC e descreva a role de menor privilégio.
3. Adicione `concurrency` para evitar deploys simultâneos no mesmo ambiente.
4. Torne o workflow reutilizável (reusable workflow) para vários pipelines.

## Referências

- Documentação do GitHub Actions (workflows, environments, OIDC, reusable workflows).
- Documentação de Trivy, docker/build-push-action, aws-actions/configure-aws-credentials.
