# Deployment (dbt)

> 🔵 Analytics Platforms · Parte de [28 — dbt](../README.md)

## O que é

**Deployment** é como você leva um projeto dbt do laptop para **produção** de forma confiável:
ambientes separados, [CI/CD](../../23-cicd-dataops/README.md), agendamento por um
[orquestrador](../../11-orchestration/README.md) e monitoramento. É o que transforma "rodei dbt na
minha máquina" numa plataforma de analytics operável — a essência do
[DataOps](../../23-cicd-dataops/05-dataops/README.md).

## Ambientes (dev / staging / prod)

dbt usa **targets** (no `profiles.yml`) para rodar o **mesmo** código em ambientes diferentes
(schemas/bancos distintos), isolando dev de produção:

```yaml
# profiles.yml
meu_projeto:
  target: dev
  outputs:
    dev:  {schema: dbt_felipe, ...}       # cada dev tem seu schema
    prod: {schema: analytics, ...}
```

- **dev** — cada desenvolvedor materializa em seu próprio schema (sem pisar no do outro).
- **prod** — o schema oficial consumido por BI/ML.
- Segredos/credenciais vêm de env vars/secret manager, não hardcoded (ver
  [security](../../26-security/04-secrets-management/README.md)).

## CI (integração contínua)

A cada PR, rode dbt contra um ambiente de teste para validar a mudança **antes** do merge:

```yaml
# .github/workflows/dbt-ci.yml (esboço)
- run: dbt deps
- run: dbt build --target ci      # roda models + testes
```

- `dbt build` = run + [test](../05-tests/README.md) na ordem do DAG → se um model falha nos testes,
  bloqueia.
- **Slim CI / state** — `dbt build --select state:modified+ --defer` roda **só os models que
  mudaram** (e seus dependentes), comparando com o estado de produção (`--state`). Isso acelera muito
  o CI em projetos grandes.

## CD (deploy para produção)

Após o merge, um **job de produção** roda o dbt (geralmente disparado pelo
[orquestrador](../../11-orchestration/README.md)):

```bash
dbt deps
dbt build --target prod        # ou: dbt run && dbt test
dbt docs generate              # publica docs/lineage atualizados
dbt source freshness
```

## Orquestração (quem dispara o dbt em produção)

dbt **não se agenda sozinho** (o `dbt Cloud` tem scheduler; o `dbt Core` precisa de um disparador):

- **[Airflow](../../11-orchestration/02-airflow/README.md)** — operadores/Cosmos para rodar dbt.
- **[Dagster](../../11-orchestration/03-dagster/README.md)** — integra models dbt como **assets**
  (lineage unificado).
- **[Prefect](../../11-orchestration/04-prefect/README.md)**, dbt Cloud scheduler, ou cron para casos
  simples.

O dbt é uma **etapa** (o "T") num pipeline maior: E/L (ingestão) → dbt (transform) → testes/docs.

## Estratégias de deploy e segurança

- **Build em staging + swap** — construir no schema de staging, validar, e só então expor (evita
  usuários vendo dados meio-prontos) — ver [deployment strategies](../../23-cicd-dataops/06-deployment-strategies/README.md).
- **Blue/green** de schemas para trocas sem downtime.
- **`--full-refresh`** planejado para mudanças de lógica em [modelos incrementais](../08-incremental-models/README.md).

## Observabilidade do deploy

- Capture os **artefatos** do run (`run_results.json`, `manifest.json`) para métricas (durações,
  falhas, lineage) — ver [observabilidade](../../10-data-pipelines/08-pipeline-observability/README.md).
- **Alerte** em falhas de `dbt build`/`source freshness`.
- Pacotes como **Elementary** adicionam observabilidade/anomalias sobre o dbt (ver
  [anomaly detection](../../12-data-quality/07-anomaly-detection/README.md)).

## Versionamento e governança do projeto

- Projeto dbt é **código**: versionado em Git, revisado por [PR](../../03-git-software-engineering/03-pull-requests-code-review/README.md),
  com [conventional commits](../../03-git-software-engineering/04-conventional-commits-versioning/README.md).
- Pin de versão do dbt e dos pacotes (`packages.yml` + `dbt deps`) para reprodutibilidade.

## Erros comuns

- Rodar dbt direto em prod sem CI/testes (dados ruins em produção).
- `dbt run` sem `dbt test` em produção (ver [tests](../05-tests/README.md)).
- Todos materializando no mesmo schema (devs pisando uns nos outros).
- Segredos no `profiles.yml` comitado.
- Não usar Slim CI (CI lento) nem publicar docs.

## Boas práticas

- Ambientes isolados (target por dev + prod); segredos fora do código.
- `dbt build` em CI (Slim CI com state) a cada PR; só mergeia verde.
- Produção disparada por orquestrador; build em staging + swap; `--full-refresh` planejado.
- Capture artefatos, alerte em falhas, publique docs/lineage; pin de versões.

## Relação com outros conceitos

- [CI/CD & DataOps](../../23-cicd-dataops/README.md),
  [deployment strategies](../../23-cicd-dataops/06-deployment-strategies/README.md),
  [orquestração](../../11-orchestration/README.md).
- [Tests](../05-tests/README.md), [incremental](../08-incremental-models/README.md),
  [observabilidade](../../10-data-pipelines/08-pipeline-observability/README.md).
- Aplicado no [Projeto 02](../../projects/02-analytics-warehouse/README.md).

## Exercícios

1. Configure targets dev/prod no `profiles.yml` com schemas separados.
2. Escreva um workflow de CI que roda `dbt build` num ambiente de teste a cada PR.
3. Explique o Slim CI (`state:modified+ --defer`) e seu benefício.
4. Descreva como o dbt vira uma etapa num DAG de orquestração (E/L → dbt → testes/docs).

## Referências

- Documentação do dbt — Deployment, CI, `state`/`defer`, artefatos.
- Elementary (observabilidade para dbt); integrações Airflow/Dagster.
