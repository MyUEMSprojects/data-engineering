# Exercícios — Módulo 19: Cloud

Teoria em [19-cloud](../../19-cloud/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Modelo de responsabilidade compartilhada

No S3, o que é responsabilidade **da AWS** e o que é **sua**? Dê exemplos.

<details><summary>Gabarito</summary>

AWS: infraestrutura física, durabilidade/disponibilidade do serviço, patching da plataforma. Você: **configuração** (bucket público ou não), **IAM**, criptografia, versionamento, classificação e **o que armazena**. A maioria dos vazamentos em nuvem vem de **má configuração do cliente**. Ver [IAM e segredos](../../19-cloud/06-iam-secrets/README.md).
</details>

## 2. 🟢 Conceitual — Classes de armazenamento

Associe: dados acessados diariamente; acessados 1×/mês; arquivo regulatório raramente lido. Cite o custo oculto das classes "frias".

<details><summary>Gabarito</summary>

Diário → **Standard**; mensal → **Standard-IA**/Nearline (preço de armazenamento menor, **taxa de recuperação** e mínimo de 30 dias); arquivo → **Glacier/Archive** (muito barato; recuperação em minutos/horas e custo por *retrieval*). Use *lifecycle policies* e **Intelligent-Tiering** quando o padrão é imprevisível. Ver [object storage](../../19-cloud/02-object-storage/README.md).
</details>

## 3. 🔵 Implementação — Lifecycle

Escreva (Terraform) uma regra de lifecycle: mover `incoming/` para Standard-IA após 30 dias e expirar versões antigas após 90.

<details><summary>Gabarito</summary>

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    id = "ia-and-expire"; status = "Enabled"
    filter { prefix = "incoming/" }
    transition { days = 30; storage_class = "STANDARD_IA" }
    noncurrent_version_expiration { noncurrent_days = 90 }
  }
}
```
Completo e aplicado num emulador no [Projeto 09](../../projects/09-cloud/README.md).
</details>

## 4. 🔵 Debugging — Conta surpresa

O custo mensal do BigQuery/Athena triplicou. Liste **quatro** causas e como investigar.

<details><summary>Gabarito</summary>

(1) Consultas **sem filtro de partição** / `SELECT *`. (2) Tabelas **sem partição/cluster** ou com **arquivos pequenos**. (3) *Dashboards* com refresh frequente sem cache. (4) *Joins* acidentais (produto cartesiano) ou jobs em loop. Investigue pelo **log de jobs** (bytes lidos por usuário/consulta), defina **cotas/orçamentos** e alertas. Ver [custos](../../19-cloud/08-cost-management/README.md).
</details>

## 5. 🟣 Arquitetura — Rede privada para dados

Um job no cluster acessa um banco gerenciado e o S3 **sem sair pela internet**. Que recursos de rede usar e por quê?

<details><summary>Gabarito</summary>

Recursos em **subnets privadas**; banco **sem IP público**; **VPC endpoints** (gateway para S3/DynamoDB, *interface/PrivateLink* para outros) para tráfego pela rede da AWS; **security groups** de menor privilégio; NAT apenas se precisar de saída. Reduz exposição e custo de saída. Ver [redes](../../19-cloud/05-networking/README.md) e [segurança de rede](../../26-security/05-network-security/README.md).
</details>

## 6. 🟣 Arquitetura — Multi-cloud?

Um executivo pede "multi-cloud para evitar lock-in". Dê **dois argumentos contra** e **uma abordagem** que reduz o lock-in a custo razoável.

<details><summary>Gabarito</summary>

Contra: (1) complexidade operacional e de segurança multiplicada; (2) perde-se o uso de serviços gerenciados diferenciados e há custo de **egress** entre nuvens. Alternativa: **formatos e protocolos abertos** (Parquet/Iceberg/Delta, SQL, Kafka API, Kubernetes, Terraform) — o dado e a lógica ficam portáveis mesmo com uma nuvem principal. Ver [serviços](../../19-cloud/01-service-models/README.md).
</details>
