# CI — Integração contínua

> 🟣 Production · Parte de [23 — CI/CD & DataOps](../README.md)

## O que é

**Continuous Integration** é a prática de **integrar mudanças ao branch principal com frequência**
(várias vezes ao dia), com **verificação automática** a cada integração: build, lint, testes. O objetivo é
detectar problemas **cedo, quando são baratos de corrigir**, e manter a `main` sempre saudável.

## Por que existe

Integrações grandes e raras geram "merge hell" e bugs descobertos tarde. Em dados, o custo é maior: uma
transformação errada que chega à produção pode **corromper números** usados em decisões. CI cria uma
**rede de segurança automática** em cada PR ([PRs](../../03-git-software-engineering/03-pull-requests-code-review/README.md)).

## O que roda no CI (para pipelines de dados)

```text
PR aberto ─► [lint/format] ─► [testes unitários] ─► [testes de integração] ─► [dbt build/tests] ─► [segurança/scan] ─► ✅ merge permitido
```

| Etapa | O que verifica | Ferramentas |
| --- | --- | --- |
| **Lint/format** | estilo e erros estáticos | `ruff`, `black`, `sqlfluff`, `shellcheck`, `terraform fmt` ([lint](../../03-git-software-engineering/06-linting-formatting/README.md)) |
| **Type check** | tipos | `mypy` |
| **Testes unitários** | lógica das transformações | `pytest` ([testes](../../04-python-for-data-engineering/09-testing-python/README.md)) |
| **Testes de integração** | código + DB/serviços efêmeros | Docker/Testcontainers ([pipeline testing](../../10-data-pipelines/07-pipeline-testing/README.md)) |
| **Testes de dados/modelos** | `dbt build` em ambiente de teste | [dbt](../../28-dbt/09-deployment/README.md) |
| **Validação de DAGs** | DAG Airflow importa sem erro | `pytest` + `DagBag` |
| **IaC** | `terraform validate/plan`, policy-as-code | [IaC](../../22-infrastructure-as-code/README.md) |
| **Segurança** | segredos vazados, CVEs de deps/imagens | gitleaks, Trivy, `pip-audit` ([container security](../../20-containers/07-container-security/README.md)) |
| **Links/docs** | Markdown e links (como neste repo) | markdownlint, check de links |

## Princípios de um bom CI

- **Rápido** (minutos) — feedback lento é ignorado. Paralelize, use cache, rode o caro só quando preciso
  (path filters, *slim CI* do dbt com `state:modified+`).
- **Determinístico/confiável** — sem testes flaky; ambientes reprodutíveis (containers, lockfile).
- **Falha alto e claro** — mensagens acionáveis.
- **Bloqueia o merge** — proteção de branch exige CI verde + revisão ([PRs](../../03-git-software-engineering/03-pull-requests-code-review/README.md)).
- **`main` sempre verde** e deployável.
- **Fonte única da verdade**: o que passa no CI é o mesmo que roda local (`make test`, pre-commit).

## Exemplo: workflow de CI (GitHub Actions)

```yaml
name: CI
on:
  pull_request:
  push: { branches: [main] }

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: test }
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U postgres" --health-interval 5s --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check . && black --check .
      - run: mypy src/
      - run: pytest -q --cov=src
        env: { DATABASE_URL: postgresql://postgres:test@localhost:5432/postgres }
```

(O CI deste repositório está em `.github/workflows/ci.yml` — [ver](../../.github/workflows/ci.yml).)

## CI para dados: particularidades

- **Dados de teste** pequenos/sintéticos (fixtures), nunca produção/PII ([segurança](../../26-security/README.md)).
- **Ambiente efêmero** de warehouse/schema por PR (schema `ci_pr_123`) para rodar dbt, limpo ao final.
- **Teste de idempotência** e de schema/contrato ([contracts](../../29-data-contracts/README.md)).
- **Custo**: limite o que roda em CI (amostras, `--select state:modified+`).

## Métricas (DORA)

Frequência de deploy, *lead time* de mudança, taxa de falha de mudança e tempo de recuperação — o CI
saudável melhora todas.

## Erros comuns

- CI lento (>15–20 min) → devs o evitam.
- Testes flaky → ignorados; "re-run até passar".
- CI que não bloqueia merge.
- Segredos de produção no CI sem escopo; dados reais em testes.
- Só testar código e esquecer dbt/dados/IaC.

## Boas práticas

- Pipeline curto, paralelo, com cache; mesma ferramenta local/CI; branch protection.
- Testes de pirâmide; ambientes efêmeros; slim CI.
- Credenciais via OIDC/segredos do CI com menor privilégio.

## Relação com outros conceitos

- [Testes](../../03-git-software-engineering/05-testing/README.md), [lint](../../03-git-software-engineering/06-linting-formatting/README.md),
  [CD](../02-continuous-delivery/README.md), [DataOps](../05-dataops/README.md),
  [dbt deploy](../../28-dbt/09-deployment/README.md).

## Exercícios

1. Escreva um workflow que roda lint, mypy e pytest com Postgres como serviço.
2. Adicione um job que valida que todos os DAGs Airflow importam sem erro.
3. Proponha como rodar `dbt build` por PR em schema efêmero sem custo excessivo.
4. Liste 4 causas de CI lento e correções.

## Referências

- Fowler, M. "Continuous Integration"; Humble & Farley, *Continuous Delivery*; GitHub Actions docs.
