# Projeto 09 — Pipeline em nuvem com IaC (Terraform), IAM de menor privilégio e policy-as-code

> 🟣 Nível: avançado · Módulos: [19 Cloud](../../19-cloud/README.md), [22 Infrastructure as Code](../../22-infrastructure-as-code/README.md),
> [26 Segurança](../../26-security/README.md), [23 CI/CD](../../23-cicd-dataops/README.md) ·
> Anterior: [Projeto 08](../08-streaming/README.md) · Próximo: [Projeto 10](../10-capstone/README.md)

## Objetivo

Provisionar com **Terraform** um pipeline *serverless* de ingestão — **S3 (raw) → SQS (+DLQ) → Lambda → S3 (curated)** —
com **segurança por padrão** e **testar a infraestrutura de verdade, sem conta AWS**, usando um emulador (Moto):

- infraestrutura **declarativa e verificável** (`validate` → `plan` → `apply` → *verificações como código*);
- **IAM de menor privilégio**, provado por um **simulador** (o papel *pode* ler `incoming/*`, *não pode* apagar nada);
- **policy-as-code**: um linter que reprova a infraestrutura *antes* de ela existir na nuvem;
- pipeline **idempotente** e tolerante a falhas (*at-least-once*, falha parcial de lote, DLQ);
- **custo e retenção** como decisão de projeto (lifecycle, *bucket key*, retenção de logs).

> ⚠️ **Honestidade sobre o que foi (e não foi) verificado**: tudo abaixo rodou contra o **Moto** (emulador), não contra a AWS.
> O emulador valida a *forma* dos recursos e várias regras (ele chegou a **aplicar** a bucket policy e negar HTTP), mas **não
> executa a Lambda** (precisa de acesso ao Docker) nem avalia IAM de verdade. O *código* da Lambda é testado em-processo e por um
> *poller* local que imita o *event source mapping*. Antes de produção, um `terraform plan` real é obrigatório.

## Arquitetura

```text
 produtor ──► s3://orders-ENV-raw-<conta>/incoming/*.csv ──(ObjectCreated, prefixo incoming/, sufixo .csv)──► SQS orders-ENV-ingest ──► Lambda orders-ENV-transform
              versionado · SSE-KMS · sem acesso público              │ visibilidade 6×timeout                    (event source mapping:
              TLS obrigatório · lifecycle (→ IA em 30 d)             │ maxReceiveCount=3 ──► SQS ...-ingest-dlq     batch 10, ReportBatchItemFailures)
                                                                     ▼                                                   │
                                                         alarme CloudWatch: DLQ não vazia                                ▼
                                          s3://orders-ENV-curated-<conta>/curated/orders/dt=AAAA-MM-DD/part-<hash>.jsonl   (válidas, por data)
                                                                          /rejected/orders/<hash>.jsonl                    (inválidas + motivo + origem)
 KMS (rotação anual) cifra os buckets · IAM role da Lambda: S3 GetObject incoming/* · PutObject curated/* e rejected/* · SQS consumo · KMS · logs próprios
```

## Requisitos

Docker + Compose (Terraform 1.10 e Moto rodam em contêineres) e Python ≥ 3.11 para os testes (`moto`, `boto3`).
Porta do emulador configurável: `MOTO_PORT` (padrão 5000).

## Estrutura

```text
09-cloud/
├── infra/                      # Terraform: versions · variables · main · outputs · .terraform.lock.hcl (VERSIONADO)
├── docker-compose.yml · tf.sh  # Moto + Terraform em contêiner (estado num volume, não no repositório)
├── src/cloudpipe/              # handler.py (a Lambda) · runner.py (poller que imita o event source mapping)
├── src/policylint/             # iam_sim.py (simulador IAM) · lint.py (regras sobre plano/estado do Terraform)
├── scripts/verify_and_e2e.py   # compliance da infra criada + e2e S3→SQS→handler→curated/DLQ
└── tests/                      # 25 testes (handler com Moto em-processo · simulador · linter)
```

## Execução

```bash
cd projects/09-cloud
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
export MOTO_PORT=5000                      # (ocupada? troque — e mantenha exportada)

pytest -q                                   # 25 testes, ~1 s, sem Docker (Moto em-processo)

docker compose up -d moto                   # emulador
./tf.sh init
./tf.sh validate
./tf.sh plan -out=tfplan
./tf.sh apply -auto-approve tfplan          # 23 recursos

# 1) policy-as-code sobre o ESTADO criado (veja "Limite do plano" abaixo)
docker compose --profile tools run --rm terraform "terraform show -json" | python -m policylint /dev/stdin   # (ou salve em arquivo)

# 2) compliance da infra + prova de que o bucket nega HTTP
export AWS_ENDPOINT_URL=http://localhost:${MOTO_PORT} AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 PYTHONPATH=src
EXPECT_TLS_DENY=1 python scripts/verify_and_e2e.py

# 3) e2e: o emulador só fala HTTP, então desligue o Deny não-TLS para este passo (em produção: SEMPRE ligado)
./tf.sh apply -auto-approve -var enforce_tls_only=false
python scripts/verify_and_e2e.py            # 26/26 verificações

docker compose --profile tools down -v      # limpa (estado do Terraform incluso)
```

Saída verificada (resumo):

```text
Apply complete! Resources: 23 added, 0 changed, 0 destroyed.
✔ nenhuma violação                                  ← policylint sobre o estado
   ✔ bucket policy nega escrita via HTTP (sem TLS)  ← o Moto APLICA a policy: PutObject sem TLS → 403
== 2. o papel da Lambda tem MENOR privilégio (simulador IAM) ==
   ✔ s3:GetObject    raw/incoming/a.csv           → PERMITIDO     ✔ s3:DeleteObject raw/incoming/a.csv → NEGADO
   ✔ s3:PutObject    curated/curated/orders/...   → PERMITIDO     ✔ s3:GetObject    curated/...        → NEGADO
   ✔ s3:PutObject    raw/incoming/a.csv           → NEGADO        ✔ s3:ListBucket   raw                → NEGADO     ✔ iam:PassRole * → NEGADO
== 3. e2e ==  bom → 2 partições dt=, 6 linhas válidas, 2 rejeitadas com motivo {bad_amount, missing_field:customer_id}
              veneno (cabeçalho errado) → DLQ após 3 tentativas · arquivo fora de incoming/ → sem mensagem
== 4. idempotência ==  chave URL-encoded decodificada · reentrega do mesmo evento ⇒ mesmos bytes e mesmas chaves
26/26 verificações OK
```

## Os recursos e o porquê de cada decisão

| Recurso | Decisão | Por quê / trade-off |
| --- | --- | --- |
| **KMS key** | `enable_key_rotation`, alias | rotação anual automática; custo fixo/mês + por chamada |
| **S3** (`for_each` raw/curated) | **versionamento**, **SSE-KMS** com **bucket key**, **Public Access Block** total, **bucket policy** negando não-TLS | defesa em profundidade. *Bucket key* corta ~99% das chamadas ao KMS (custo); versionamento custa armazenamento (mitigado por lifecycle) |
| **Lifecycle** | versões antigas expiram em 90 d; multipart abortado em 7 d; `raw/incoming/` → **Standard-IA** em 30 d | custo de armazenamento ([custos](../../19-cloud/08-cost-management/README.md)); IA cobra *retrieval* e tem mínimo de 30 d — não use em dado quente |
| **SQS + DLQ** | `maxReceiveCount=3`, retenção 14 d na DLQ, visibilidade = **6 × timeout** da Lambda, SSE gerenciado | regra da AWS para Lambda+SQS (senão a mensagem reaparece *durante* o processamento); DLQ preserva o que falhou |
| **Queue policy** | só o `s3.amazonaws.com` envia, com `aws:SourceArn` **e** `aws:SourceAccount` | evita o *confused deputy*: outro bucket/conta não injeta mensagens |
| **Notificação S3** | prefixo `incoming/`, sufixo `.csv` | não dispara para qualquer objeto (custo e ruído) |
| **IAM role da Lambda** | 5 statements, **cada um com ARN específico** (nenhum `*` em ação ou recurso) | menor privilégio ([IAM](../../26-security/02-iam/README.md), [least privilege](../../26-security/06-least-privilege/README.md)) |
| **Lambda** | `python3.12`, 256 MB, timeout 60 s, `source_code_hash` | o hash faz o Terraform reimplantar **só** quando o código muda |
| **Event source mapping** | batch 10 + janela de 5 s, `ReportBatchItemFailures` | reentrega **só** o item que falhou — sem isso um item ruim reprocessa o lote inteiro |
| **Log group** | retenção 14 d, criado pelo Terraform | sem retenção os logs custam para sempre; a role só pode escrever **nele** |
| **Alarme** | DLQ visível > 0 | a DLQ cheia **precisa** acordar alguém ([alertas](../../24-observability/04-alerting/README.md)) |
| **Provider** | credenciais falsas só quando `emulator_endpoint != ""`; senão cadeia padrão | **nenhuma chave no código**; `default_tags` em tudo ([segredos](../../22-infrastructure-as-code/05-environments-secrets/README.md)) |
| **`.terraform.lock.hcl` versionado** | `~> 5.80` | builds reprodutíveis do provider |

## O pipeline (Lambda) — tolerância a falhas

- **Idempotência por construção**: a chave de saída é `part-<sha256(chave_origem + ETag)>`. SQS é *at-least-once* — a mesma mensagem
  chega 2×; a segunda sobrescreve **os mesmos bytes**. Arquivo *regravado* (outro ETag) gera **nova** saída ([idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Chaves do S3 chegam URL-encoded** no evento (`espaço → +`, `+ → %2B`, acentos em %XX): `unquote_plus` — o bug clássico "funciona
  em teste, falha com arquivo `ordens de março.csv`". Está testado.
- **Falha permanente × transitória**: cabeçalho errado, não-UTF-8 ou arquivo > 50 MB ⇒ `PermanentError`; objeto inexistente/exceção
  ⇒ falha do item. Ambos voltam via `batchItemFailures` e, após 3 tentativas, vão para a **DLQ**. (Refinamento possível: enviar
  falhas permanentes direto à DLQ para não gastar tentativas.)
- **Quarentena**: linhas inválidas vão para `rejected/` com **motivo, número da linha e origem** — nada some.
- **Evento `s3:TestEvent`** (enviado ao configurar a notificação) é ignorado — sem isso, a 1.ª mensagem da fila falharia.

## Policy-as-code (`policylint`)

Um linter de ~100 linhas sobre o JSON do Terraform (o mesmo papel de Checkov/tfsec/OPA, com o mecanismo à vista):

| Regra | Pega |
| --- | --- |
| IAM-001 / IAM-002 | `Action` com curinga (`*`, `s3:*`) / `Resource: "*"` em *Allow* |
| IAM-003 | *Allow* para `Principal: "*"` **sem** `Condition` |
| S3-001…004 | bucket sem SSE-KMS / sem versionamento / com Public Access Block incompleto / sem *Deny* de não-TLS |
| SQS-001 / SQS-002 | fila sem criptografia / fila (não-DLQ) sem *redrive* |
| KMS-001 / LOG-001 | chave sem rotação / log group sem retenção |

**Limite do plano (aprendido na prática)**: no JSON de um **plano**, tudo que depende de atributo computado (o ARN do bucket dentro de uma policy,
por exemplo) é "conhecido só após o apply" e **desaparece** — meu 1.º linter, rodando sobre o plano, acusou 3 falsos positivos
(S3-004 e SQS-002). Solução: o linter aceita **plano e estado**, casa buckets pelo índice do `for_each`, e o fluxo recomendado é
*apply no emulador → lint do **estado** → só então apply na nuvem*. Ferramentas de produção resolvem o mesmo problema avaliando a
*configuração* (HCL) além do plano.

O **simulador IAM** (`iam_sim.py`) responde "este papel pode X em Y?" com *Deny explícito > Allow > negação implícita*, curingas e
case-insensitive para ações. **Limites declarados**: ignora `Condition`, `NotAction`, *permission boundaries* e SCPs (e **recusa**
`NotAction` em vez de adivinhar). Não substitui o *IAM Policy Simulator* da AWS.

## Testes

```bash
pytest -q        # 25 testes, ~1 s
```

| Grupo | O que garante |
| --- | --- |
| **Handler (Moto em-processo)** | 6 razões de validação; caminho feliz **particionado por data** + quarentena; **chave com espaço, `+` e acento**; reprocessar = mesmas chaves/bytes, ETag novo = saída nova; **falha parcial** (só o item ruim volta); objeto inexistente e não-UTF-8 não derrubam o lote; `TestEvent` e corpo inválido; objeto grande demais |
| **Simulador IAM** | negação implícita × *Allow*; *Deny* explícito vence; ação case-insensitive e recurso case-sensitive; aceita JSON em string; **recusa** `NotAction` |
| **Linter** | pilha conforme = 0 achados; **cada regra** pega a sua violação (parametrizado); ausência de TLS-deny/criptografia; `Principal "*"` com `Condition` é aceito; entende **estado** e ignora recursos em remoção |
| **Infra real (emulador)** | `verify_and_e2e.py`: criptografia/versionamento/PAB/lifecycle em **ambos** os buckets, DLQ com `maxReceiveCount=3`, filtro da notificação, 8 casos de IAM, e2e completo, DLQ do arquivo-veneno, idempotência |

> 🐞 **O que o emulador ensinou**: (1) o Moto **aplicou** o `Deny` não-TLS e devolveu `403` ao meu `PutObject` por HTTP — o e2e só passou
> depois de eu criar a variável `enforce_tls_only` (a política funciona; o emulador é que não fala HTTPS). (2) `terraform destroy`
> falhou com `BucketNotEmpty`: buckets **versionados e com dados não são apagados por acidente** — comportamento desejado; para
> laboratório use `force_destroy`, **nunca** em produção. (3) Os tempos de `apply` mostraram valores negativos/enormes por causa do
> relógio instável do meu WSL2 (ver [Projeto 07](../07-kafka/README.md#troubleshooting)) — cosmético aqui.

## Do emulador para a AWS real

```bash
cd infra
terraform init
terraform plan  -var environment=dev -out=tfplan        # SEM emulator_endpoint; credenciais via SSO/role (aws sso login)
terraform apply tfplan
# estado remoto + travamento: backend "s3" (+ DynamoDB/lockfile) — NÃO versione tfstate (contém segredos)
```

Antes de produção: **backend remoto** com *state locking* ([estado](../../22-infrastructure-as-code/03-state/README.md)), `environment=prod` com
workspaces/contas separados ([ambientes](../../22-infrastructure-as-code/05-environments-secrets/README.md)), `enable_event_source_mapping=true`
(padrão), *deployment* por CI com `terraform plan` comentado no PR e *apply* com aprovação ([CI/CD](../../23-cicd-dataops/README.md)),
detecção de **drift** agendada ([drift](../../22-infrastructure-as-code/06-drift/README.md)), CMK com *key policy* revisada,
alarmes com destino (SNS → e-mail/Slack) e orçamento (*AWS Budgets*).

## Possíveis melhorias (exercícios)

1. **Módulo Terraform**: extraia o par bucket+criptografia+PAB+lifecycle em `modules/secure-bucket` e reutilize para raw/curated/logs
   ([módulos](../../22-infrastructure-as-code/04-modules-variables/README.md)).
2. **Conformidade no CI**: rode `fmt -check`, `validate`, `policylint` e `pytest` no GitHub Actions (ver [workflow do repositório](../../.github/workflows/ci.yml)).
3. **Falhas permanentes direto para a DLQ** (sem gastar 3 tentativas) — como o handler sinaliza isso sem perder o item?
4. **Saída em Parquet** com Lambda Layer (`pyarrow`) ou **Glue/Athena**: particione e consulte; compare custo com JSONL ([Projeto 05](../05-data-lake/README.md)).
5. **Condition no simulador**: implemente `StringEquals`/`ArnEquals` e teste a *queue policy* (`aws:SourceArn`).
6. **Threat model**: o que um atacante com `s3:PutObject` em `incoming/` consegue? (CSV gigante, *zip bomb*, injeção de fórmula, custo) — adicione limites.
7. **Observabilidade**: métricas customizadas (linhas aceitas/rejeitadas por arquivo) via EMF e um *dashboard*; alarme de **idade** da mensagem mais antiga.
8. **Multi-conta**: separe raw/curated em contas distintas com *cross-account role* e `aws:PrincipalOrgID`.
9. **Cost**: estime com `infracost` e compare Standard × IA × Intelligent-Tiering para a camada raw.

## Referências

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) ·
  [Lambda + SQS: partial batch response](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html) ·
  [S3 event notifications (chaves URL-encoded)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html) ·
  [Moto](https://docs.getmoto.org/) · [IAM: lógica de avaliação de políticas](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html).
- AWS *Well-Architected* (pilares Segurança, Confiabilidade e Otimização de custos); módulos [19](../../19-cloud/README.md), [22](../../22-infrastructure-as-code/README.md) e [26](../../26-security/README.md).
