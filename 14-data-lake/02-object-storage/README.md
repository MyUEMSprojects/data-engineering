# Object storage

> 🔵 Analytics Platforms · Parte de [14 — Data Lake](../README.md)

## O que é

**Object storage** (armazenamento de objetos) é o tipo de armazenamento que sustenta data lakes e
a nuvem moderna: guarda dados como **objetos** (arquivo + metadados + identificador único) em um
espaço plano de nomes (*buckets*), acessível via **API HTTP**. Exemplos: **Amazon S3**,
**Google Cloud Storage (GCS)**, **Azure Blob/ADLS**, e o **MinIO** (compatível com S3, para rodar
local). (Este tópico é o fundamento de storage do lake; a visão cloud mais ampla está em
[19 — Cloud/object storage](../../19-cloud/02-object-storage/README.md).)

## Por que importa

Praticamente todo data lake/lakehouse vive sobre object storage. Entender suas propriedades
(e limitações!) explica como lakes funcionam, por que [Parquet](../../08-data-formats/04-parquet/README.md)
e particionamento importam, e por que o [small files problem](../06-small-files-compaction/README.md)
existe.

## Características (e por que são ideais para lakes)

- **Barato** — centavos por GB/mês; classes "frias" ainda mais baratas para arquivamento.
- **Escala "infinita"** — sem gerenciar discos/capacidade.
- **Durável e disponível** — redundância embutida (ex.: S3 projeta 11 noves de durabilidade);
  replicação cross-region para DR.
- **Desacoplado do compute** — qualquer engine lê os mesmos objetos (base da separação
  storage/compute dos [warehouses](../../13-data-warehouse/01-concepts-architecture/README.md)).
- **API HTTP** — acesso de qualquer lugar/ferramenta.

## Object storage ≠ filesystem (diferenças cruciais)

Parece um sistema de arquivos, mas **não é** — e confundir causa bugs/custos:

- **Namespace plano** — não há diretórios de verdade; "pastas" são só prefixos no nome do objeto
  (`lake/vendas/dt=2024-01-01/part-0.parquet` é um nome, não uma hierarquia real).
- **Objetos são imutáveis** — você **não edita** um objeto; **substitui** o objeto inteiro. Não há
  "append" eficiente nem edição parcial. (Por isso updates em lakes crus exigem reescrever
  arquivos — e por isso o [lakehouse](../../15-lakehouse/README.md) existe.)
- **Operações de "listar/renomear" são caras/lentas** — listar um prefixo com milhões de objetos é
  lento; "renomear" é copiar+apagar. Isso penaliza muitos arquivos pequenos.
- **Consistência** — hoje S3 oferece *strong read-after-write* para novos objetos (antes era
  eventual — um histórico que explica muitas armadilhas antigas).

## Conceitos

| Conceito | O que é |
| --- | --- |
| **Bucket** | container de nível superior (nome global/único) |
| **Object** | o dado + metadados + chave (nome) |
| **Key/prefix** | o "caminho" do objeto (prefixos simulam pastas) |
| **Storage class** | nível de custo/latência (standard, infrequent, archive/Glacier) |
| **Versioning** | manter versões de objetos (proteção/DR) |
| **Lifecycle policy** | mover/expirar objetos automaticamente (custo) |

## Acesso programático

```python
import boto3                                  # S3 (ou gcsfs/adlfs para GCS/Azure)
s3 = boto3.client("s3")
s3.upload_file("local.parquet", "meu-bucket", "lake/vendas/dt=2024-01-01/part-0.parquet")

# ferramentas de dados lêem direto:
import polars as pl
pl.scan_parquet("s3://meu-bucket/lake/vendas/*.parquet")   # via fsspec/pyarrow
```

Bibliotecas como **fsspec**/**s3fs**/**gcsfs** e o [PyArrow](../../04-python-for-data-engineering/13-pyarrow/README.md)
`filesystem` deixam ler/escrever no object storage como se fosse arquivo.

## Custo (o que vigiar)

- **Storage** por GB (barato), com classes mais baratas para dados frios.
- **Requests** — `GET`/`PUT`/`LIST` têm custo por milhar; **muitos arquivos pequenos = muitas
  requests** (outro motivo contra small files).
- **Egress** — transferir dados **para fora** da nuvem/região custa (às vezes caro) — processe perto
  dos dados.
- **Lifecycle policies** para mover/expirar dados e cortar custo (ver
  [cost](../../19-cloud/08-cost-management/README.md)).

## Segurança

- **IAM/políticas de bucket** — controle de acesso fino (ver [security/IAM](../../26-security/02-iam/README.md)).
- **Criptografia** em repouso (SSE) e em trânsito (TLS) — ver
  [encryption](../../26-security/03-encryption/README.md).
- **Buckets públicos por engano** são um vazamento clássico — bloqueie acesso público por padrão.
- **Versioning + object lock (WORM)** protegem contra exclusão/ransomware (ver
  [backup/DR](../../06-databases/09-backup-recovery-dr/README.md)).

## Erros comuns

- Tratar como filesystem (esperar append/edição parcial eficientes).
- Milhões de arquivos pequenos → listas lentas, muitas requests, custo
  ([small files](../06-small-files-compaction/README.md)).
- Bucket público por descuido (vazamento).
- Ignorar custo de egress (processar em outra região/nuvem).
- Não usar lifecycle/classes frias para dados antigos.

## Boas práticas

- [Parquet](../../08-data-formats/04-parquet/README.md) + [partição](../05-partitioning/README.md)
  + arquivos de tamanho saudável (evite small files).
- IAM mínimo, criptografia, bloquear acesso público, versioning para dados críticos.
- Lifecycle policies para custo; processe perto dos dados (evite egress).

## Relação com outros conceitos

- Sustenta [data lake](../01-concepts/README.md),
  [lakehouse](../../15-lakehouse/README.md) e [warehouses](../../13-data-warehouse/README.md).
- [Cloud/object storage](../../19-cloud/02-object-storage/README.md),
  [security](../../26-security/README.md), [cost](../../19-cloud/08-cost-management/README.md).

## Exercícios

1. Explique por que object storage não é um filesystem e 2 consequências práticas disso.
2. Suba um MinIO local (Docker) e grave/leia um Parquet via `boto3`/`s3fs`.
3. Projete uma lifecycle policy que move dados > 90 dias para classe fria e expira > 2 anos.
4. Liste 3 configurações de segurança essenciais para um bucket de lake.

## Referências

- Documentação de Amazon S3, Google Cloud Storage, Azure Blob/ADLS; MinIO.
- fsspec / s3fs / PyArrow filesystem docs.
