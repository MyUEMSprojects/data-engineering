# Volumes (persistência)

> 🟣 Cloud & Infra · Parte de [21 — Kubernetes](../README.md)

## O problema

Como nos [containers](../../20-containers/03-volumes-networks/README.md), o filesystem de um Pod é
**efêmero**. Pods são recriados em outros nós; o dado local some. Kubernetes abstrai armazenamento
persistente com **Volumes**, **PersistentVolumes (PV)**, **PersistentVolumeClaims (PVC)** e
**StorageClasses**.

## Tipos de volume (resumo)

| Tipo | Persistência | Uso |
| --- | --- | --- |
| **emptyDir** | vive enquanto o Pod existe | scratch/shuffle de Spark, cache, troca entre containers do Pod |
| **configMap / secret** | — | arquivos de [config/segredos](../05-configmaps-secrets/README.md) |
| **hostPath** | do nó | evite (acopla ao nó; risco de segurança) |
| **persistentVolumeClaim** | **sobrevive** ao Pod | bancos, estado, dados duráveis |

## PV, PVC e StorageClass

- **PersistentVolume (PV)** — um pedaço de armazenamento (disco EBS/PD/Azure Disk, NFS...).
- **PersistentVolumeClaim (PVC)** — **pedido** de armazenamento por um Pod ("quero 100Gi RWO").
- **StorageClass** — define **como provisionar dinamicamente** (tipo de disco, IOPS, replicação). Com
  provisionamento dinâmico, criar o PVC cria o PV automaticamente.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: kafka-data-0}
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: gp3
  resources: {requests: {storage: 200Gi}}
```

```yaml
# no Pod
volumes: [{name: data, persistentVolumeClaim: {claimName: kafka-data-0}}]
containers:
  - name: broker
    volumeMounts: [{name: data, mountPath: /var/lib/kafka}]
```

### Access modes

- **ReadWriteOnce (RWO)** — um nó monta leitura/escrita (discos de bloco — o mais comum).
- **ReadOnlyMany (ROX)** / **ReadWriteMany (RWX)** — vários nós (NFS/EFS/Filestore/CephFS).

### Reclaim policy

`Delete` (apaga o disco ao apagar o PVC) vs `Retain` (mantém). Para dados valiosos, use `Retain`/snapshots —
**cuidado com deleção acidental** ([backup/DR](../../06-databases/09-backup-recovery-dr/README.md)).

## StatefulSet (estado com identidade estável)

Para cargas que precisam de **identidade e armazenamento estáveis por réplica** (Kafka, Cassandra, bancos):

- Nomes estáveis (`kafka-0`, `kafka-1`), ordem de criação/atualização.
- **`volumeClaimTemplates`** — um PVC por réplica, que **segue** a réplica ao ser reagendada.
- Service **headless** para DNS por Pod ([services](../03-services-networking/README.md)).

> Operar bancos/Kafka em K8s é **difícil** (backup, upgrade, failover). Use **operators** maduros
> (Strimzi p/ Kafka, CloudNativePG p/ Postgres) ou, preferencialmente, serviços **gerenciados**
> ([managed DBs](../../19-cloud/04-managed-databases/README.md)).

## Em dados: o que persistir e onde

- **Estado de verdade e dados analíticos** → **object storage** ([S3/GCS](../../19-cloud/02-object-storage/README.md))
  e **bancos gerenciados**, não volumes do cluster. Pods de pipeline devem ser **stateless**/efêmeros.
- **Scratch** (shuffle/spill do Spark, arquivos temporários) → `emptyDir` (ou NVMe local) — rápido, descartável.
- **Estado de streaming** (checkpoints) → storage durável externo ([Flink/Spark checkpoints](../../17-streaming/05-stateful-processing/README.md)
  em S3).
- **Brokers/bancos self-hosted** → StatefulSet + PVC + operator (se realmente necessário).

## Snapshots e backup

CSI **VolumeSnapshots** permitem snapshot de PVCs; combine com backup externo (Velero) e **teste a
restauração**.

## Erros comuns

- Guardar dados importantes em `emptyDir`/disco do container (somem).
- Usar `hostPath` em produção.
- PVC RWO exigido em Pods espalhados por nós diferentes (não monta).
- Reclaim `Delete` em dados críticos sem backup.
- Rodar banco/Kafka em K8s sem operator nem plano de backup.
- Zona/AZ do disco ≠ AZ do Pod (volume não anexa) — atenção a topologia.

## Boas práticas

- Pipelines stateless; persistência em object storage/serviços gerenciados.
- `emptyDir` para scratch; PVC/StatefulSet só quando indispensável, com operator e backups testados.
- StorageClass adequada (IOPS), `Retain` + snapshots para dados valiosos.

## Relação com outros conceitos

- [Containers/volumes](../../20-containers/03-volumes-networks/README.md), [Pods](../02-pods-deployments/README.md),
  [object storage](../../19-cloud/02-object-storage/README.md), [backup/DR](../../06-databases/09-backup-recovery-dr/README.md),
  [stateful streaming](../../17-streaming/05-stateful-processing/README.md).

## Exercícios

1. Crie um PVC e monte-o num Pod; apague o Pod e prove que o dado persiste.
2. Explique `emptyDir` vs PVC e dê um uso de dados para cada.
3. Descreva por que Pipelines devem ser stateless e onde guardar o estado.
4. Quando um StatefulSet é necessário e que riscos operacionais traz?

## Referências

- Kubernetes Docs — Volumes, Persistent Volumes, StorageClass, StatefulSets, VolumeSnapshots.
- Strimzi, CloudNativePG (operators); Velero (backup).
