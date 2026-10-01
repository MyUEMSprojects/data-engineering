# Container security

> 🟣 Cloud & Infra · Parte de [20 — Containers](../README.md)

## Por que importa

Containers **compartilham o kernel** do host, então o isolamento é mais fraco que o de VMs. Imagens
vêm de bases/pacotes de terceiros (cadeia de suprimentos), e containers frequentemente carregam
**credenciais** de dados. Um container mal configurado pode virar porta de entrada para dados sensíveis
(ver [security](../../26-security/README.md)).

## Superfícies de risco

```text
Imagem (base, pacotes, segredos embutidos) → Build/Supply chain → Registry → Runtime (privilégios, rede) → Host/Orquestrador
```

## 1. Segurança da imagem (build)

- **Imagens base mínimas e confiáveis** — `slim`/distroless, oficiais, versão **fixa** (não `latest`).
- **[Multi-stage](../06-multi-stage-builds/README.md)** — remova compiladores/ferramentas do runtime.
- **Rodar como não-root** — `USER app`; evita que um comprometimento vire root no container.
- **Nenhum segredo na imagem** — nem em `ENV`, `ARG`, `COPY .env`, nem em camadas anteriores (ficam no
  histórico). Injete em runtime ([secrets](../../19-cloud/06-iam-secrets/README.md)); use
  `--mount=type=secret` no build.
- **`.dockerignore`** — não envie `.git`, `.env`, chaves ao contexto.
- **Atualize** bases/dependências regularmente (CVEs).

## 2. Vulnerabilidades e supply chain

- **Scanning** de imagens e dependências: **Trivy**, Grype, Docker Scout, ECR/Artifact Registry scanning —
  bloqueie CVEs críticos no [CI](../../23-cicd-dataops/README.md).
- **SBOM** (lista de componentes) e **assinatura** (Cosign/Sigstore) comprovam proveniência.
- **Pin por digest** em produção; registries privados com tags imutáveis
  ([registries](../05-registries/README.md)).
- Dependências Python: lockfile + auditoria (`pip-audit`).

## 3. Segurança em runtime

- **Menor privilégio**:
  - `--user` não-root; `--read-only` (filesystem somente leitura) + `tmpfs` onde precisa escrever.
  - **Dropar capabilities** (`--cap-drop ALL`, adicionar só o necessário); `--security-opt no-new-privileges`.
  - **Nunca `--privileged`** nem montar `/var/run/docker.sock` (equivale a root no host).
- **Limites de recursos** (CPU/memória/pids) contra DoS e *noisy neighbor*.
- **Perfis seccomp/AppArmor/SELinux** restringem syscalls.
- **Rootless** containers (Podman/Docker rootless) reduzem o impacto de escape.

## 4. Rede

- Publique **só as portas necessárias**; serviços internos (banco, Kafka) sem `-p` para o host.
- Redes separadas por função; criptografia em trânsito (TLS); [network policies](../../21-kubernetes/README.md) em
  Kubernetes (default-deny).
- Não exponha o daemon Docker (TCP 2375) sem TLS/autenticação.

## 5. Segredos e credenciais em dados

Containers de pipeline precisam de acesso a bancos/buckets: use **identidade do workload**
(IRSA/Workload Identity/Managed Identity) com **menor privilégio** em vez de chaves fixas
([IAM](../../19-cloud/06-iam-secrets/README.md)). Evite logar segredos/PII
([logging](../../04-python-for-data-engineering/04-errors-and-logging/README.md)).

## 6. Orquestrador (Kubernetes)

Pod Security Standards (restricted), RBAC mínimo, secrets criptografados, network policies, admission
control (OPA/Kyverno) — ver [Kubernetes](../../21-kubernetes/README.md).

## Checklist rápido

```text
[ ] Base mínima, versão/digest fixos, atualizada
[ ] USER não-root; sem segredos na imagem/ENV/ARG; .dockerignore
[ ] Multi-stage; só o necessário no runtime
[ ] Scan (Trivy) + SBOM + assinatura no CI
[ ] read-only fs, cap-drop ALL, no-new-privileges; nunca --privileged / docker.sock
[ ] Limites de CPU/mem; portas mínimas; TLS; redes isoladas
[ ] Identidade de workload em vez de chaves estáticas
```

## Erros comuns

- Rodar como root e com `--privileged`.
- Segredos em `ENV`/imagem/histórico.
- Imagens antigas/`latest` sem scan.
- Expor portas de banco à internet; montar o socket do Docker.
- Confiar em imagens públicas desconhecidas.

## Boas práticas

- Aplique o checklist; automatize scan/assinatura no CI.
- Menor privilégio em tudo (usuário, capabilities, rede, IAM).
- Atualize e reconstrua imagens regularmente; monitore runtime (Falco).

## Relação com outros conceitos

- [Security](../../26-security/README.md), [secrets/IAM](../../19-cloud/06-iam-secrets/README.md),
  [registries](../05-registries/README.md), [Kubernetes](../../21-kubernetes/README.md),
  [CI/CD](../../23-cicd-dataops/README.md).

## Exercícios

1. Endureça um Dockerfile: base slim fixa, usuário não-root, multi-stage, sem segredos.
2. Escaneie uma imagem com Trivy e interprete os achados.
3. Rode um container com `--read-only`, `--cap-drop ALL` e `no-new-privileges` e ajuste o que quebrar.
4. Explique por que montar `/var/run/docker.sock` é perigoso.

## Referências

- CIS Docker Benchmark; OWASP Docker Security Cheat Sheet; documentação do Trivy e Sigstore.
