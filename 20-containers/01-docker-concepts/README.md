# Docker: conceitos

> 🟣 Cloud & Infra · Parte de [20 — Containers](../README.md)

## O que é

Um **container** é um processo (ou grupo) isolado do restante do sistema, com seu próprio filesystem,
rede e espaço de processos, mas **compartilhando o kernel** do host. **Docker** é a plataforma que
popularizou containers: empacota, distribui e executa aplicações de forma padronizada.

## Problema que resolve

- **"Funciona na minha máquina"** — versões de Python/libs/SO diferentes quebram pipelines. A imagem
  carrega o ambiente inteiro → **reprodutibilidade** (princípio central de DE).
- **Dependências conflitantes** entre projetos na mesma máquina.
- **Onboarding/dev local** — subir Postgres+Kafka+Airflow com um comando.
- **Deploy uniforme** — o artefato testado no CI é o mesmo que roda em produção
  ([CI/CD](../../23-cicd-dataops/README.md)).

## Containers vs VMs

```text
VM:        [App][Libs][SO convidado completo] sobre [Hypervisor] sobre [Hardware]   (pesado, GBs, boot em minutos)
Container: [App][Libs] sobre [Container runtime] sobre [Kernel do host]              (leve, MBs, inicia em segundos)
```

| | VM | Container |
| --- | --- | --- |
| Isolamento | forte (kernel próprio) | processo isolado (kernel compartilhado) |
| Tamanho/boot | GBs / minutos | MBs / segundos |
| Densidade | baixa | alta |
| Segurança | maior isolamento | menor (requer hardening — ver [security](../07-container-security/README.md)) |

Complementares: containers costumam rodar **dentro** de VMs na nuvem.

## Como funciona (primitivas do Linux)

- **Namespaces** — isolam visões do sistema (PID, rede, mount, usuário, hostname).
- **cgroups** — limitam/medem recursos (CPU, memória, I/O).
- **Union/overlay filesystem** — camadas de imagem empilhadas, só-leitura, com camada gravável no topo.

Docker é a interface amigável sobre isso (ver [processos](../../02-linux-shell-environment/03-processes-and-permissions/README.md)).

## Arquitetura do Docker

```text
docker CLI ──► Docker daemon (dockerd) ──► containerd ──► runc (cria o container)
                    │
                    └─► imagens locais / registries ([registry](../05-registries/README.md))
```

O padrão **OCI** (Open Container Initiative) padroniza imagens e runtime — imagens rodam em Docker,
containerd, Podman, Kubernetes etc.

## Conceitos-chave

| Conceito | Significado |
| --- | --- |
| **Image** | template imutável, em camadas (ver [images](../02-images-containers/README.md)) |
| **Container** | instância em execução (ou parada) de uma imagem |
| **Dockerfile** | receita para construir a imagem |
| **Registry** | repositório de imagens ([registries](../05-registries/README.md)) |
| **Volume** | dados persistentes fora do ciclo de vida do container ([volumes](../03-volumes-networks/README.md)) |
| **Network** | comunicação entre containers |

## Primeiros comandos

```bash
docker run -d --name pg -e POSTGRES_PASSWORD=de -p 5432:5432 postgres:16   # sobe um Postgres
docker ps                    # containers rodando
docker logs -f pg            # logs
docker exec -it pg psql -U postgres   # shell/comando dentro
docker stop pg && docker rm pg
```

## Containers são efêmeros

Princípio: containers devem ser **descartáveis** — pode parar/recriar a qualquer momento sem perder nada
importante. Estado **não** vai dentro do container (use volumes/serviços externos) — ver
[12-factor](../../03-git-software-engineering/07-project-organization/README.md).

## Podman e alternativas

**Podman** (daemonless, rootless), **containerd/nerdctl**, **Buildah** seguem OCI e são compatíveis com
a maior parte dos fluxos Docker. Conceitos aqui valem para todos.

## Erros comuns

- Tratar container como VM (instalar/atualizar "dentro" à mão, guardar estado nele).
- Imagens gigantes e sem versão fixa (`latest`).
- Rodar como root sem necessidade.
- Esquecer limites de recursos (um container consome todo o host).

## Boas práticas

- Um processo principal por container; imagem imutável; configuração por variáveis de ambiente.
- Tags versionadas e fixas; limites de CPU/memória.
- Estado fora do container.

## Relação com outros conceitos

- [Images/containers](../02-images-containers/README.md), [Compose](../04-docker-compose/README.md),
  [Kubernetes](../../21-kubernetes/README.md), [CI/CD](../../23-cicd-dataops/README.md).
- [Reprodutibilidade/ambientes Python](../../04-python-for-data-engineering/02-environments-and-packaging/README.md).

## Exercícios

1. Rode um Postgres em container e conecte com `psql`; apague o container e veja o que se perde.
2. Explique namespaces e cgroups com um exemplo cada.
3. Compare VM e container para rodar um job de ETL em CI.

## Referências

- Documentação do Docker; OCI Runtime/Image specs; Poulton, N. *Docker Deep Dive*.
