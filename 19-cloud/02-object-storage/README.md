# Object storage (visão cloud)

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)
>
> Os **fundamentos** (objetos imutáveis, namespace plano, relação com lakes) estão em
> [Data Lake / object storage](../../14-data-lake/02-object-storage/README.md). Aqui: a visão de
> **serviço cloud** — classes, custo, controle de acesso e operação.

## O que é

Armazenamento de **objetos** (dado + metadados + chave) em *buckets*, via API HTTP, praticamente
ilimitado, durável e barato: **Amazon S3**, **Google Cloud Storage (GCS)**, **Azure Blob/ADLS Gen2**. É a
base de [data lakes](../../14-data-lake/README.md), [lakehouses](../../15-lakehouse/README.md), backups e
da separação storage/compute dos [warehouses](../../13-data-warehouse/01-concepts-architecture/README.md).

## Classes de armazenamento (custo × acesso)

| Camada | Uso | Custo storage | Custo acesso/latência |
| --- | --- | --- | --- |
| **Standard / hot** | dados quentes, lidos com frequência | maior | baixo |
| **Infrequent access / cool** | acesso ocasional | médio | cobrança por leitura, mín. de dias |
| **Archive / cold (Glacier, Archive)** | retenção longa/compliance | muito baixo | recuperação em minutos–horas, cobrança por restore |
| **Intelligent tiering** | padrão incerto | auto | move automaticamente entre camadas |

**Lifecycle policies** transitam/expiram objetos automaticamente (ex.: 30d → IA, 365d → archive, 7a →
delete) — a principal alavanca de custo.

## O que gera custo

- **Storage** (GB/mês, por classe).
- **Requests** (`PUT/GET/LIST` por mil) → muitos arquivos pequenos custam caro
  ([small files](../../14-data-lake/06-small-files-compaction/README.md)).
- **Egress** (saída de dados para internet/outra região/outra nuvem) — frequentemente o custo
  surpresa; processar **na mesma região** do dado.
- **Retrieval/early deletion** em camadas frias.
- **Versionamento** acumula versões (limpe com lifecycle).

## Durabilidade e disponibilidade

- Durabilidade projetada de ~11 noves (S3): dados replicados em múltiplas zonas.
- **Versioning** (proteção contra delete/overwrite), **replicação** cross-region (DR — ver
  [backup/DR](../../06-databases/09-backup-recovery-dr/README.md)), **Object Lock/WORM** (imutabilidade,
  ransomware/compliance).
- Consistência: S3 e GCS oferecem leitura *strongly consistent* após escrita.

## Controle de acesso e segurança

- **IAM/políticas de bucket**, ACLs (legado), **pre-signed URLs** (acesso temporário), VPC endpoints
  (acesso privado sem internet) — ver [IAM](../06-iam-secrets/README.md).
- **Bloquear acesso público** por padrão (a causa nº 1 de vazamentos).
- **Criptografia** em repouso (SSE-S3/KMS/CMEK) e em trânsito (TLS) — ver
  [encryption](../../26-security/03-encryption/README.md).
- **Logs de acesso** e auditoria (CloudTrail/Audit Logs).

## Organização do lake no bucket

```text
s3://empresa-dados-prod/
├── bronze/  fonte=pedidos/dt=2024-01-15/part-0.parquet
├── silver/  ...
└── gold/    ...
```

Buckets separados por ambiente/camada/sensibilidade facilitam IAM e custo. Prefixos particionados por
data ([partitioning](../../14-data-lake/05-partitioning/README.md)).

## Acesso a partir de ferramentas

Spark/Trino/Athena/BigQuery (external tables)/polars/DuckDB leem direto do bucket. Conectores: `s3a://`
(Hadoop/Spark), `gs://`, `abfss://`. `fsspec/s3fs/gcsfs` em Python.

## Erros comuns

- Bucket público por engano.
- Dados em outra região/nuvem da engine (egress alto + latência).
- Sem lifecycle (storage e versões crescendo para sempre).
- Milhões de arquivos minúsculos (custo de requests + lentidão).
- Credenciais estáticas no código em vez de roles/identidade federada.

## Boas práticas

- Lifecycle + classes corretas; mesma região; Parquet particionado e arquivos de tamanho saudável.
- Block Public Access, criptografia, versioning/replicação para dados críticos.
- Acesso via roles/identidades (sem chaves de longa duração); VPC endpoints.
- Buckets/prefixos separados por ambiente e sensibilidade.

## Relação com outros conceitos

- [Data lake/object storage](../../14-data-lake/02-object-storage/README.md),
  [lakehouse](../../15-lakehouse/README.md), [IAM](../06-iam-secrets/README.md),
  [cost](../08-cost-management/README.md).
- Equivalentes: [AWS S3](../09-aws/README.md) · [GCS](../10-gcp/README.md) · [Azure Blob/ADLS](../11-azure/README.md).

## Exercícios

1. Desenhe uma lifecycle policy para dados de log (30d quente, 1a frio, 7a delete).
2. Liste 4 fontes de custo de object storage além do GB armazenado.
3. Configure acesso de um job Spark a um bucket via role (sem chaves estáticas) — descreva o fluxo.
4. Explique por que egress inter-região pode dominar a fatura.

## Referências

- Documentação do Amazon S3, Google Cloud Storage e Azure Blob/ADLS (pricing e segurança).
