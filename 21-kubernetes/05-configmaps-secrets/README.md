# ConfigMaps e Secrets

> 🟣 Cloud & Infra · Parte de [21 — Kubernetes](../README.md)

## Por que separar configuração do código

Segue o princípio **12-factor**: a imagem é **imutável e igual em todos os ambientes**; o que muda
(URLs, flags, credenciais) é **injetado em runtime** ([organização de projetos](../../03-git-software-engineering/07-project-organization/README.md),
[images](../../20-containers/02-images-containers/README.md)). Em K8s: **ConfigMap** (config não sensível) e
**Secret** (sensível).

## ConfigMap

Guarda configuração **não sensível** como pares chave/valor ou arquivos.

```yaml
apiVersion: v1
kind: ConfigMap
metadata: {name: pipeline-config}
data:
  ENV: "prod"
  RAW_BUCKET: "s3://dados-prod/bronze"
  config.yaml: |
    batch_size: 5000
    sources: [pedidos, clientes]
```

### Como consumir

```yaml
containers:
  - name: etl
    image: ghcr.io/org/pipeline:1.4.2
    envFrom: [{configMapRef: {name: pipeline-config}}]    # todas as chaves viram env vars
    env:
      - name: BATCH_SIZE
        valueFrom: {configMapKeyRef: {name: pipeline-config, key: batch_size}}
    volumeMounts: [{name: cfg, mountPath: /etc/pipeline}]  # ou como arquivo
volumes: [{name: cfg, configMap: {name: pipeline-config}}]
```

Alterar um ConfigMap **não** reinicia Pods automaticamente (env vars só no start; arquivos montados
atualizam com atraso) — planeje o *rollout*.

## Secret

Guarda dados **sensíveis** (senhas, tokens, certificados). Usado igual ao ConfigMap.

```yaml
apiVersion: v1
kind: Secret
metadata: {name: db-credentials}
type: Opaque
stringData:                       # stringData: texto; o K8s armazena em base64
  DATABASE_URL: "postgresql://user:***@host:5432/dw"
```

```yaml
env:
  - name: DATABASE_URL
    valueFrom: {secretKeyRef: {name: db-credentials, key: DATABASE_URL}}
```

### ⚠️ Secret ≠ criptografado por padrão

Por padrão, Secrets são apenas **base64** (codificação, **não** criptografia) no etcd. Quem lê o objeto vê
o valor. Para segurança real:

- Habilitar **criptografia at-rest** do etcd (KMS provider).
- **RBAC mínimo** — restringir quem lê Secrets.
- **Não versionar** Secrets no Git em texto claro.
- Preferir **gestores externos** + sincronização:
  - **External Secrets Operator** / **Secrets Store CSI Driver** buscam de AWS Secrets Manager, GCP Secret
    Manager, Azure Key Vault, Vault ([IAM/secrets](../../19-cloud/06-iam-secrets/README.md)).
  - **Sealed Secrets / SOPS** para versionar segredos **cifrados** no Git (GitOps).
- Melhor ainda: **identidade do workload** (IRSA/Workload Identity) → sem segredo algum para acessar
  bucket/banco.

## Em dados

- Config de pipeline (buckets, tabelas, flags) em ConfigMap; **credenciais** de banco/API em Secret
  (ou, melhor, identidade federada).
- Airflow: conexões/variáveis via backend de secrets; imagens sem credenciais.
- Evite logar valores de env sensíveis ([logging](../../04-python-for-data-engineering/04-errors-and-logging/README.md)).

## Erros comuns

- Achar que Secret é criptografado (é só base64).
- Segredos em ConfigMap, imagem ou manifestos no Git.
- RBAC aberto (qualquer um lê Secrets do namespace).
- Esperar que mudar ConfigMap atualize Pods em execução.
- Secrets expostos em logs/`describe`/env dump.

## Boas práticas

- ConfigMap p/ config, Secret p/ sensível; imagem única para todos os ambientes.
- Criptografia at-rest + RBAC mínimo + gestor externo (External Secrets/CSI) ou SOPS/Sealed Secrets.
- Prefira identidade de workload a chaves estáticas; rotacione credenciais.
- Reinicie/rollout ao mudar config (ou use *checksum annotations* no Helm).

## Relação com outros conceitos

- [IAM/secrets](../../19-cloud/06-iam-secrets/README.md), [container security](../../20-containers/07-container-security/README.md),
  [Pods/Deployments](../02-pods-deployments/README.md), [secrets management](../../26-security/04-secrets-management/README.md).

## Exercícios

1. Injete config via ConfigMap (env e arquivo) num Pod e verifique dentro do container.
2. Demonstre que um Secret é só base64 (`kubectl get secret -o yaml | base64 -d`).
3. Descreva o fluxo External Secrets: gestor externo → Secret no cluster → Pod.
4. Explique por que identidade de workload é melhor que um Secret com chave estática.

## Referências

- Kubernetes Docs — ConfigMaps, Secrets, Encrypting Secret Data at Rest; External Secrets Operator.
