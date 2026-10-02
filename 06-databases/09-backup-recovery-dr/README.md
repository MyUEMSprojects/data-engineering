# Backup, recovery e disaster recovery

> 🔵 Core · Parte de [06 — Databases](../README.md)

## O que é

- **Backup** — cópia dos dados que permite restaurá-los após perda/corrupção.
- **Recovery** — o processo de restaurar a partir de um backup (ou do log).
- **Disaster Recovery (DR)** — o plano e a infraestrutura para voltar a operar após uma
  falha grave (perda de um datacenter/região, ataque, erro humano catastrófico).

## Por que importa (muito) em DE

Dados são o ativo. Perdê-los — por falha de hardware, bug, `DROP TABLE` acidental,
ransomware — pode ser fatal para o negócio. O Data Engineer frequentemente é responsável
por pipelines e armazenamentos cujo backup/DR precisa ser confiável **e testado**. Um
backup que nunca foi restaurado não é um backup — é uma esperança.

## RPO e RTO (os dois números que guiam tudo)

```text
            incidente
   ──────────────┼──────────────────────►
      RPO ◄──────┤                        tempo
   (quanto dado  │       ├──── RTO ───►
    posso perder)│       (quanto tempo até voltar a operar)
```

- **RPO (Recovery Point Objective)** — quanto de dado você tolera perder (ex.: "no
  máximo 15 min"). Define a **frequência** de backup/replicação.
- **RTO (Recovery Time Objective)** — quanto tempo você tolera ficar fora (ex.: "no
  máximo 1 h"). Define a **estratégia** de recuperação (standby quente vs restaurar do
  zero).

Esses alvos vêm do negócio e determinam o custo da solução (RPO/RTO baixos custam mais).

## Tipos de backup

- **Lógico** (`pg_dump`/`mysqldump`) — exporta SQL/dados; portável, mais lento, bom para
  bases pequenas/médias e migrações.
- **Físico** (ex.: `pg_basebackup`, snapshots de volume) — cópia dos arquivos; rápido de
  restaurar, específico da versão/engine.
- **Completo vs incremental/diferencial** — completo copia tudo; incremental só o que
  mudou desde o último (economiza espaço/tempo).
- **Snapshot** — cópia point-in-time do volume/armazenamento (cloud facilita muito).

## Point-in-Time Recovery (PITR) — o padrão robusto

Combina um **backup base** + o **log de transações** ([WAL](../01-relational-concepts/README.md)/
binlog) arquivado. Permite restaurar para **qualquer instante** (ex.: "às 14:59, 1 min
antes do DROP acidental").

```text
backup base (domingo) ─► + WAL arquivado continuamente ─► restaura até 14:59 de quarta
```

É o que entrega RPO baixo sem fazer *full backup* o tempo todo.

## Backup ≠ replicação ≠ versionamento

| Mecanismo | Protege contra | Não protege contra |
| --- | --- | --- |
| [Replicação](../07-replication/README.md) | falha de hardware/nó | erro lógico (um `DELETE` errado replica para todos!) |
| Backup/PITR | erro lógico, corrupção, perda | — (é a rede de segurança) |
| Snapshot de lake/time travel | mudanças indevidas em tabelas | perda total do storage (precisa cross-region) |

> Ponto crítico: **replicação não é backup**. Um comando destrutivo ou uma corrupção se
> propaga para as réplicas. Você precisa de backups independentes e imutáveis.

## Disaster Recovery: estratégias (por custo/RTO)

```text
Backup & restore   → mais barato, RTO alto (restaurar do zero)
Pilot light        → núcleo mínimo pronto, escala no desastre
Warm standby       → ambiente reduzido rodando, promove rápido
Hot standby / multi-site active-active → RTO ~0, mais caro
```

Escolha pelo RTO/RPO exigido e pelo orçamento.

## Testar a restauração (a regra de ouro)

- **Restaure de verdade**, periodicamente, em ambiente separado. Muitos descobrem que o
  backup estava corrompido/incompleto **só no desastre**.
- Meça o tempo real de restauração (ele é o seu RTO efetivo).
- Automatize e documente o *runbook* de recuperação.

## O ângulo do Data Engineering (lake/warehouse)

- **Object storage** ([S3/GCS](../../19-cloud/02-object-storage/README.md)) já é durável e
  replicado; para DR, habilite **versionamento** e **cross-region replication**.
- **Lakehouse** ([Delta/Iceberg/Hudi](../../15-lakehouse/README.md)) oferece **time
  travel** — "restaurar" uma tabela a uma versão anterior após um pipeline errado.
- **Reprodutibilidade como DR**: se pipelines e dados brutos (camada *bronze*) estão
  preservados e o código versionado, você pode **reprocessar** as camadas derivadas — uma
  forma poderosa de recuperação específica de dados.
- **Imutabilidade/WORM** e cópias *offline/air-gapped* protegem contra ransomware.

## Erros comuns

- Confundir replicação com backup.
- Nunca testar a restauração.
- Backups na mesma região/conta que o primário (um comprometimento leva os dois).
- RPO/RTO não definidos → solução sub ou superdimensionada.
- Esquecer de versionar/proteger a camada *raw* do lake (impossível reprocessar).

## Boas práticas

- Defina RPO/RTO com o negócio; dimensione a solução por eles.
- PITR (backup base + log) para bancos; versionamento + cross-region para lakes.
- Backups imutáveis, em local/conta separados; retenção por política.
- **Teste restaurações** regularmente; documente o runbook.
- Preserve a camada *raw* para reprocessar derivados.

## Relação com outros conceitos

- [Replicação](../07-replication/README.md) (complementar, não substituto).
- [Object storage](../../19-cloud/02-object-storage/README.md),
  [lakehouse/time travel](../../15-lakehouse/README.md),
  [medallion/bronze](../../14-data-lake/03-medallion-architecture/README.md).
- Governança/retenção: [governance](../../25-data-governance/06-retention-auditing/README.md).

## Exercícios

1. Para um sistema fictício, defina RPO e RTO e justifique a estratégia de backup/DR
   escolhida.
2. Explique por que replicação não substitui backup, com um exemplo de `DELETE`
   acidental.
3. Descreva um fluxo de PITR (backup base + WAL) para restaurar a 1 min antes de um erro.
4. Para um data lake, liste as medidas de DR (versionamento, cross-region, raw
   preservado) e como reprocessar as camadas derivadas.

## Referências

- Documentação do PostgreSQL — "Backup and Restore", "Continuous Archiving and PITR".
- AWS/GCP — guias de Disaster Recovery (padrões backup/pilot light/warm/hot).
- Google SRE Book — capítulos sobre confiabilidade e recuperação.
