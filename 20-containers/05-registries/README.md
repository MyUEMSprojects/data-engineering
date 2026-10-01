# Registries

> 🟣 Cloud & Infra · Parte de [20 — Containers](../README.md)

## O que é

Um **container registry** é o serviço que **armazena e distribui imagens** de container (como um "Git
para imagens"). O fluxo: o CI **constrói** a imagem, **publica** no registry, e os ambientes (Kubernetes,
Airflow, servidores) **baixam** dela.

```text
git push ─► CI: docker build ─► docker push (registry) ─► prod: docker pull / K8s ImagePull
```

## Opções

| Registry | Notas |
| --- | --- |
| **Docker Hub** | público padrão; limites de pull anônimo; imagens oficiais |
| **GitHub Container Registry (ghcr.io)** | integrado ao GitHub Actions/permissões do repo |
| **Amazon ECR** | AWS; integra IAM, scanning; ([AWS](../../19-cloud/09-aws/README.md)) |
| **Google Artifact Registry** | GCP ([GCP](../../19-cloud/10-gcp/README.md)) |
| **Azure Container Registry (ACR)** | Azure ([Azure](../../19-cloud/11-azure/README.md)) |
| **Self-hosted** | Harbor, GitLab Registry, Nexus |

Prefira o registry **privado do seu provedor** (mesma região do compute → pulls rápidos e sem egress).

## Nomes e tags

```text
registro/namespace/imagem:tag
ghcr.io/minha-org/pipeline-vendas:1.4.2
```

- **Tag** — rótulo mutável (`1.4.2`, `latest`). **`latest` não é versão** — evite em produção.
- **Digest** (`@sha256:...`) — identificador **imutável** do conteúdo; garante exatamente a mesma imagem.
- Estratégia de tags: **SemVer** (`1.4.2`), **commit SHA** (`sha-a1b2c3d`) para rastreabilidade e/ou
  `main` para ambientes de integração. Ver [versionamento](../../03-git-software-engineering/04-conventional-commits-versioning/README.md).

## Fluxo básico

```bash
docker login ghcr.io
docker build -t ghcr.io/org/pipeline:1.4.2 .
docker push ghcr.io/org/pipeline:1.4.2
docker pull ghcr.io/org/pipeline:1.4.2
docker tag pipeline:dev ghcr.io/org/pipeline:1.4.2      # reetiquetar
```

No CI (GitHub Actions): `docker/login-action` + `docker/build-push-action` com credenciais por
**secrets/OIDC** (não senhas fixas) — ver [CI/CD](../../23-cicd-dataops/README.md).

## Segurança e governança

- **Autenticação/autorização** — registry privado; pull/push por identidade ([IAM](../../19-cloud/06-iam-secrets/README.md)),
  tokens de menor privilégio.
- **Vulnerability scanning** (ECR scanning, Trivy, Grype) — bloqueie imagens com CVEs críticos
  ([container security](../07-container-security/README.md)).
- **Assinatura de imagens** (Cosign/Sigstore) e **SBOM** para cadeia de suprimentos.
- **Imutabilidade de tags** (opção em ECR etc.) evita sobrescrever uma versão publicada.
- **Retenção/lifecycle** — apague imagens antigas (custo de storage).

## Cache e mirrors

Para evitar limites do Docker Hub e acelerar CI: use *pull-through cache*/mirror no registry do seu
provedor e **fixe** imagens base internas.

## Erros comuns

- Deploy com `latest` (não reprodutível; rollback impossível).
- Registry público com imagens internas/segredos embutidos.
- Sem scanning nem política de retenção.
- Credenciais fixas de registry no CI.
- Pulls de outra região/internet (lento e com egress).

## Boas práticas

- Registry privado na mesma região do compute; tags imutáveis (SemVer + SHA); digest em produção.
- Scanning + assinatura no pipeline; lifecycle policies.
- Autenticação via identidade federada/OIDC no CI.

## Relação com outros conceitos

- [Images](../02-images-containers/README.md), [multi-stage](../06-multi-stage-builds/README.md),
  [security](../07-container-security/README.md), [CI/CD](../../23-cicd-dataops/README.md),
  [Kubernetes](../../21-kubernetes/README.md).

## Exercícios

1. Publique uma imagem no ghcr.io com tags SemVer e SHA.
2. Explique tag vs digest e por que usar digest em produção.
3. Configure (conceitualmente) um job de CI que builda, escaneia e publica a imagem.

## Referências

- Docker/OCI Distribution Spec; docs de ECR, Artifact Registry, ACR, GHCR; Sigstore/Cosign.
