# 20 — Containers

> 🟣 Nível 6 — Cloud & Infra · Pré: [02 — Linux](../02-linux-shell-environment/README.md),
> [03 — Git/SWE](../03-git-software-engineering/README.md) · Próximo: [21 — Kubernetes](../21-kubernetes/README.md)

**Containers** empacotam uma aplicação com suas dependências num artefato isolado e reprodutível que roda
igual em qualquer lugar. Para Data Engineering, resolvem o clássico "funciona na minha máquina":
ambientes locais (Postgres, Kafka, Airflow, Spark via Compose), imagens de pipelines em produção e a base
de [Kubernetes](../21-kubernetes/README.md).

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Docker: conceitos](01-docker-concepts/README.md) | Containers vs VMs, arquitetura |
| 02 | [Images e containers](02-images-containers/README.md) | Dockerfile, camadas, ciclo de vida |
| 03 | [Volumes e networks](03-volumes-networks/README.md) | Persistência e comunicação |
| 04 | [Docker Compose](04-docker-compose/README.md) | Stacks multi-serviço locais |
| 05 | [Registries](05-registries/README.md) | Distribuição de imagens |
| 06 | [Multi-stage builds](06-multi-stage-builds/README.md) | Imagens pequenas e seguras |
| 07 | [Container security](07-container-security/README.md) | Segurança de imagens e runtime |

## Dependências internas

```text
Conceitos ─► Images/containers ─► Volumes/networks ─► Compose
                    │
                    ├─► Registries
                    └─► Multi-stage builds ─► Container security
```

## Checkpoint

- [ ] Explicar containers vs VMs e o que é uma imagem, camada e container.
- [ ] Escrever um Dockerfile eficiente para um pipeline Python.
- [ ] Persistir dados com volumes e conectar containers via networks.
- [ ] Montar um stack local (Postgres + app + Airflow/Kafka) com Compose.
- [ ] Publicar/consumir imagens em um registry com tags versionadas.
- [ ] Usar multi-stage builds para reduzir tamanho/superfície de ataque.
- [ ] Aplicar práticas básicas de segurança de containers.

## Referências do módulo

- Documentação oficial do Docker (docs.docker.com); *Docker Deep Dive*, Nigel Poulton.
- OCI Specs (opencontainers.org); CIS Docker Benchmark.
