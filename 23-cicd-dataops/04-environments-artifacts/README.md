# Ambientes e artefatos

> 🟣 Production · Parte de [23 — CI/CD & DataOps](../README.md)

## Ambientes

Conjuntos isolados onde o software/dados rodam em estágios de maturidade:

| Ambiente | Propósito | Dados | Quem usa |
| --- | --- | --- | --- |
| **Local/dev** | desenvolvimento rápido | sintéticos/amostra | desenvolvedor |
| **CI/efêmero** | validar PRs | fixtures/schema efêmero | pipeline |
| **Staging/QA** | ensaio geral próximo de prod | amostras mascaradas / cópia reduzida | time, QA |
| **Produção** | valor real | dados reais | negócio/consumidores |

### Princípios

- **Isolamento** — dev nunca escreve em prod: contas/projetos/schemas/buckets/credenciais **separados**
  ([IaC/ambientes](../../22-infrastructure-as-code/05-environments-secrets/README.md)).
- **Paridade** — staging **estruturalmente igual** a prod (mesmos módulos/versões); diferem em escala/
  retenção/custo.
- **Promoção** — a mesma versão sobe dev → stg → prod, passando por gates.
- **Configuração por ambiente, não por código** — o artefato é o mesmo; muda config/segredos.

### O desafio dos dados

Diferente de apps, **dados reais são o que dá significado à validação**, mas não devem vazar para
ambientes inferiores:

- **Amostragem + mascaramento/anonimização** de PII para staging ([masking](../../26-security/07-data-masking-pii/README.md),
  [LGPD](../../26-security/08-lgpd/README.md)).
- **Dados sintéticos** para dev/CI.
- **Clones baratos** (zero-copy clone no Snowflake, branches/time travel em lakehouse) para testar com
  volume realista sem duplicar custo ([Snowflake](../../13-data-warehouse/06-snowflake/README.md)).
- **Ambiente efêmero por PR** (schema `pr_123`) destruído ao fechar o PR ([dbt CI](../../28-dbt/09-deployment/README.md)).
- **Custo** — ambientes inferiores com compute pequeno, auto-suspend e retenção curta
  ([cost](../../19-cloud/08-cost-management/README.md)).

## Artefatos

**Artefato** = a saída **imutável e versionada** do build que é implantada: imagem de container, wheel
Python, pacote, plano do Terraform, bundle de DAGs, manifesto dbt.

### Regras de ouro

1. **Construa uma vez, implante muitas** — o artefato testado no CI é **exatamente** o que vai a prod.
   Nunca reconstrua por ambiente (risco de divergência).
2. **Imutável** — um artefato publicado não muda; correção = nova versão.
3. **Versionado e rastreável** — identificador único (SemVer e/ou SHA do commit) ligando artefato ↔ commit
   ↔ pipeline ([versionamento](../../03-git-software-engineering/04-conventional-commits-versioning/README.md)).
4. **Sem config/segredos embutidos** — injetados em runtime ([secrets](../../19-cloud/06-iam-secrets/README.md)).
5. **Armazenado em repositório confiável** — registry de containers ([registries](../../20-containers/05-registries/README.md)),
   PyPI privado/Artifactory/CodeArtifact, buckets versionados.

### Tipos e onde guardar

| Artefato | Repositório | Identificação |
| --- | --- | --- |
| Imagem de container | ECR/GAR/ACR/GHCR | tag SemVer + `sha-<commit>`; digest em prod |
| Pacote Python (wheel) | PyPI privado / CodeArtifact / Artifactory | SemVer |
| Plano Terraform | artefato do CI (`tfplan`) | commit + run id |
| DAGs / bundles | imagem ou bucket versionado | commit |
| Manifest/artefatos dbt (`manifest.json`) | bucket (para slim CI/`--state`) | run id |
| Modelos de ML | model registry (MLflow etc.) | versão do modelo |

### Rastreabilidade e supply chain

- **SBOM** e **assinatura** (Cosign/Sigstore) para proveniência.
- **Scan** de vulnerabilidades antes de promover ([container security](../../20-containers/07-container-security/README.md)).
- **Retenção/limpeza** (lifecycle) para controlar custo; mantenha versões recentes para rollback.

## Configuração por ambiente

```text
mesma imagem pipeline:sha-a1b2c3d
   ├─ dev:   ENV=dev   DB=dw-dev   bucket=dados-dev
   ├─ stg:   ENV=stg   DB=dw-stg   bucket=dados-stg
   └─ prod:  ENV=prod  DB=dw-prod  bucket=dados-prod
```

Config via variáveis de ambiente/ConfigMap/Helm values por ambiente; segredos via secret manager
([K8s ConfigMaps/Secrets](../../21-kubernetes/05-configmaps-secrets/README.md)).

## Erros comuns

- Reconstruir artefatos por ambiente (prod ≠ testado).
- Tag `latest` / artefatos mutáveis (sem rastreabilidade nem rollback).
- Staging muito diferente de prod (falsa confiança) ou com PII real sem proteção.
- Dev com acesso de escrita a prod; contas/credenciais compartilhadas.
- Config/segredos dentro da imagem.
- Sem política de retenção de artefatos.

## Boas práticas

- Contas/projetos separados por ambiente; paridade estrutural; dados mascarados/sintéticos abaixo de prod.
- Artefato imutável, versionado, escaneado, assinado e promovido (não reconstruído).
- Config externa por ambiente; ambientes efêmeros por PR; custo controlado.

## Relação com outros conceitos

- [CD](../02-continuous-delivery/README.md), [testing/build/deploy](../03-testing-build-deploy/README.md),
  [IaC ambientes](../../22-infrastructure-as-code/05-environments-secrets/README.md),
  [registries](../../20-containers/05-registries/README.md), [DataOps](../05-dataops/README.md).

## Exercícios

1. Desenhe os ambientes de uma plataforma de dados e que dados cada um usa (e como protege PII).
2. Explique "construa uma vez, implante muitas" e o risco de reconstruir por ambiente.
3. Defina o esquema de versionamento/tag dos artefatos de um pipeline (imagem + dbt + terraform).
4. Proponha como criar/destruir um schema efêmero por PR.

## Referências

- Humble & Farley, *Continuous Delivery* (deployment pipeline, artefatos); 12-Factor App (config).
- Documentação do MLflow Model Registry, ECR/Artifact Registry, Sigstore.
