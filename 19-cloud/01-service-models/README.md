# Modelos de serviço (IaaS, PaaS, SaaS, serverless)

> 🟣 Cloud & Infra · Parte de [19 — Cloud](../README.md)

## O que é

Os modelos de serviço descrevem **quanto da pilha tecnológica o provedor gerencia** versus **o que você
gerencia**. Quanto mais alto o nível de abstração, menos operação para você — e menos controle.

```text
            Você gerencia ───────────────────────────────►  Provedor gerencia
On-prem:   [app][dados][runtime][SO][virtualização][hardware][rede]  (tudo seu)
IaaS:      [app][dados][runtime][SO] | virtualização, hardware, rede
PaaS:      [app][dados]              | runtime, SO, infraestrutura
SaaS:      (só usa)                  | tudo
Serverless:[código/consultas]        | tudo, cobrança por uso
```

## Os modelos

### IaaS (Infrastructure as a Service)

Você aluga **infraestrutura** (VMs, discos, redes) e gerencia SO, runtime e aplicação. Ex.: EC2, Compute
Engine, Azure VMs. **Controle máximo**, operação máxima (patches, scaling, HA). Em dados: rodar Kafka/
Spark/Airflow numa VM própria.

### PaaS (Platform as a Service)

O provedor gerencia SO/runtime/escala; você entrega **código e dados**. Ex.: RDS/Cloud SQL (banco
gerenciado), EMR/Dataproc (Spark gerenciado), MSK/Confluent Cloud (Kafka gerenciado), Cloud Composer/MWAA
(Airflow). Equilíbrio entre controle e esforço — **o ponto doce para muita engenharia de dados**.

### SaaS (Software as a Service)

Produto pronto; você só usa e configura. Ex.: Snowflake, Fivetran, dbt Cloud, Looker. Menos controle,
tempo mínimo até valor; custo recorrente e dependência (*lock-in*).

### Serverless

Você não provisiona servidores; paga **por uso** (execução/dados processados) e o provedor escala de zero
a muito. Ex.: BigQuery, AWS Lambda/Athena/Glue, Cloud Functions/Run, Redshift Serverless. Ótimo p/ cargas
variáveis/esporádicas; atenção a *cold start*, limites e custo em uso intenso e constante.

## Responsabilidade compartilhada (shared responsibility)

O provedor é responsável pela segurança **da** nuvem (hardware, datacenter, hypervisor); **você** é
responsável pela segurança **na** nuvem (dados, IAM, configuração, rede, criptografia). Quanto mais alto o
nível (SaaS), mais o provedor cobre — mas **dados e acesso são sempre seus** (ver
[security](../../26-security/README.md), [IAM](../06-iam-secrets/README.md)).

## Trade-offs: controle × esforço × custo

| | IaaS | PaaS | SaaS | Serverless |
| --- | --- | --- | --- | --- |
| Controle | alto | médio | baixo | baixo/médio |
| Esforço operacional | alto | médio | baixo | muito baixo |
| Time-to-value | lento | médio | rápido | rápido |
| Custo em escala | menor/unit. (se bem operado) | médio | maior | variável (ótimo p/ esporádico) |
| Lock-in | baixo | médio | alto | médio/alto |

## Em dados: como escolher

- Time pequeno / prazo curto → **SaaS/serverless/PaaS gerenciado**.
- Escala enorme, requisitos específicos, time de plataforma maduro → **IaaS/Kubernetes self-managed**
  (ver [Kubernetes](../../21-kubernetes/README.md)).
- Regra: **gerenciado por padrão**; assuma operação só onde agrega vantagem real (custo, controle,
  portabilidade).

## Erros comuns

- Operar self-hosted (IaaS) algo que existe gerenciado, sem ganho real.
- Achar que "gerenciado" elimina a responsabilidade por IAM/dados/custos.
- Serverless para carga constante pesada sem comparar custo.
- Ignorar lock-in ao adotar SaaS proprietário (mitigue com formatos abertos).

## Boas práticas

- Escolha o nível de abstração pelo custo total (operação + licença), não só pelo preço da fatura.
- Formatos abertos ([Parquet](../../08-data-formats/04-parquet/README.md), Iceberg) reduzem lock-in.
- Entenda a responsabilidade compartilhada de cada serviço.

## Relação com outros conceitos

- [Compute](../03-compute/README.md), [databases gerenciados](../04-managed-databases/README.md),
  [cost](../08-cost-management/README.md), [IaC](../../22-infrastructure-as-code/README.md).
- [Modern data stack](../../01-foundations/04-data-systems/README.md).

## Exercícios

1. Classifique em IaaS/PaaS/SaaS/serverless: EC2, RDS, Snowflake, Lambda, BigQuery, MSK, Fivetran.
2. Dê um caso em que IaaS faz sentido e outro em que PaaS é melhor para Airflow.
3. Liste o que é responsabilidade sua num banco gerenciado (RDS).

## Referências

- NIST SP 800-145 (definição de cloud computing); AWS Shared Responsibility Model.
