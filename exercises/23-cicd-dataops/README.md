# Exercícios — Módulo 23: CI/CD e DataOps

Teoria em [23-cicd-dataops](../../23-cicd-dataops/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — CI × CD

O que cada um automatiza e qual a diferença entre *continuous delivery* e *continuous deployment*?

<details><summary>Gabarito</summary>

**CI:** a cada mudança, build + lint + testes. **CD (delivery):** o artefato fica sempre **pronto** para produção, com um gatilho manual. **Deployment:** vai a produção **automaticamente** após passar nos testes. Ver [CI](../../23-cicd-dataops/01-continuous-integration/README.md) e [CD](../../23-cicd-dataops/02-continuous-delivery/README.md).
</details>

## 2. 🟢 Conceitual — O que testar num pipeline de dados

Cite quatro tipos de teste para um pipeline e o que cada um pega.

<details><summary>Gabarito</summary>

**Unitário** (funções puras de transformação); **de schema/contrato** (formato e tipos); **de dados** (unicidade, nulos, integridade, volume — *data tests*); **de integração/ponta a ponta** (fluxo completo em ambiente de teste); **de regressão** (resultado contra gabarito). Ver [testes e deploy](../../23-cicd-dataops/03-testing-build-deploy/README.md).
</details>

## 3. 🔵 Implementação — Workflow de CI

Escreva um workflow do GitHub Actions que roda `ruff` e `pytest` em Python 3.12 a cada PR, com cache de dependências.

<details><summary>Gabarito</summary>

```yaml
name: CI
on: {pull_request: {branches: [main]}}
permissions: {contents: read}
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12", cache: pip}
      - run: pip install -r requirements.txt ruff pytest
      - run: ruff check .
      - run: pytest -q
```
Valide com `actionlint` (como feito nos workflows do repositório). Exemplos reais: [`capstone.yml`](../../.github/workflows/capstone.yml), [`projects.yml`](../../.github/workflows/projects.yml).
</details>

## 4. 🔵 Debugging — Pipeline verde, produção quebrada

O CI passou, mas o deploy falhou em produção por uma variável de ambiente ausente. Como o processo deveria evitar isso?

<details><summary>Gabarito</summary>

Paridade de ambientes: **configuração como código**, validada no início da execução (falhar cedo com mensagem clara), ambiente de **staging** com os mesmos segredos/estrutura, *smoke test* pós-deploy e estratégia de *rollback*. Ver [ambientes e artefatos](../../23-cicd-dataops/04-environments-artifacts/README.md).
</details>

## 5. 🟣 Arquitetura — Estratégias de deploy

Compare **rolling**, **blue/green** e **canary** para um job de streaming que mantém estado. Qual o maior risco de cada um?

<details><summary>Gabarito</summary>

**Rolling:** troca gradual — risco: versões antigas e novas **coexistem** (compatibilidade de schema/estado). **Blue/green:** dois ambientes, troca instantânea — risco: custo dobrado e **estado/offsets** que precisam migrar. **Canary:** pequena fração de tráfego — risco: comparar corretamente os resultados (precisa de métricas). Para streaming com estado, planeje **compatibilidade de estado** (savepoints/checkpoints) e *dual-run* de validação. Ver [estratégias de deploy](../../23-cicd-dataops/06-deployment-strategies/README.md).
</details>

## 6. 🟣 Arquitetura — DataOps na prática

Defina **cinco práticas** DataOps que reduzem o tempo entre "mudança no modelo" e "dado confiável em produção".

<details><summary>Gabarito (um caminho)</summary>

(1) Tudo versionado (código, SQL, IaC, contratos). (2) **CI** com testes de dados em ambiente efêmero (ex.: `dbt build --select state:modified+`). (3) **Gates de qualidade** automáticos antes de publicar. (4) **Observabilidade** de frescor/volume com alertas e *runbooks*. (5) Deploy automatizado com rollback (ex.: time travel/`restore`). Ver [DataOps](../../23-cicd-dataops/05-dataops/README.md) e o [capstone](../../projects/10-capstone/README.md).
</details>
