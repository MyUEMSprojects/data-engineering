# Volumes e networks

> 🟣 Cloud & Infra · Parte de [20 — Containers](../README.md)

## Volumes (persistência)

O filesystem de um container é **efêmero**: ao removê-lo, o que foi escrito some. Para dados que devem
sobreviver (banco, arquivos de saída, caches), use armazenamento externo ao container.

### Tipos

| Tipo | Sintaxe | Uso |
| --- | --- | --- |
| **Named volume** | `-v pgdata:/var/lib/postgresql/data` | gerenciado pelo Docker; **preferido** p/ dados (bancos) |
| **Bind mount** | `-v $(pwd)/data:/data` | monta um diretório do host; bom p/ dev (código, configs, dados locais) |
| **tmpfs** | `--tmpfs /tmp` | em memória; dados temporários/sensíveis |

```bash
docker volume create pgdata
docker run -d -v pgdata:/var/lib/postgresql/data -e POSTGRES_PASSWORD=de postgres:16
docker volume ls ; docker volume inspect pgdata
```

### Quando usar

- **Named volumes** — estado de bancos/serviços; independem do layout do host; backup via
  `docker run --rm -v pgdata:/d -v $(pwd):/b alpine tar czf /b/pg.tgz /d`.
- **Bind mounts** — desenvolvimento (hot reload do código), fornecer arquivos de entrada/saída.

### Permissões (causa clássica de erro)

O usuário **dentro** do container precisa ter permissão no volume/bind mount ("Permission denied"). UIDs
não coincidem entre host e container — ajuste `--user`, `chown` ou use named volumes (ver
[permissões](../../02-linux-shell-environment/03-processes-and-permissions/README.md)).

### Em produção

Dados duráveis geralmente ficam em **serviços gerenciados** ([bancos](../../19-cloud/04-managed-databases/README.md),
[object storage](../../19-cloud/02-object-storage/README.md)) em vez de volumes locais; em Kubernetes usa-se
PersistentVolumes ([K8s volumes](../../21-kubernetes/06-volumes/README.md)).

## Networks (comunicação)

Containers conversam por **redes virtuais** do Docker.

### Drivers principais

- **bridge** (padrão) — rede privada no host; containers na **mesma** rede se enxergam.
- **host** — usa a rede do host (sem isolamento; Linux).
- **none** — sem rede.
- **overlay** — multi-host (Swarm/orquestradores).

### DNS por nome de serviço (o mais útil)

Numa **rede definida pelo usuário** (e no Compose), containers se resolvem **pelo nome**:

```bash
docker network create dados
docker run -d --network dados --name pg postgres:16 ...
docker run --rm --network dados meu-pipeline   # conecta em  postgresql://pg:5432/...
```

O host `pg` resolve para o IP do container — não use IPs fixos. (A rede `bridge` **default** não tem DNS
por nome; crie uma rede própria — o Compose já faz isso.)

### Publicação de portas

`-p HOSTPORT:CONTAINERPORT` expõe um serviço **ao host**:

```bash
docker run -p 5432:5432 postgres:16     # acessível em localhost:5432
```

Dentro da rede Docker, containers acessam pela **porta do container** (5432), sem precisar publicar.
**Publique só o necessário** (segurança): um banco usado apenas por outros containers não precisa de
`-p`.

## Armadilha: `localhost` dentro do container

`localhost` dentro de um container é **ele mesmo**, não o host nem outro container. Para falar com outro
serviço, use o **nome do serviço/container** na rede; para o host, `host.docker.internal` (Docker
Desktop) ou o gateway.

## Erros comuns

- Dados importantes dentro do container (somem ao recriar).
- Bind mount com permissões erradas.
- Usar `localhost` para alcançar outro container.
- Publicar portas de banco/Kafka à internet sem necessidade.
- Confiar na rede bridge default esperando DNS por nome.

## Boas práticas

- Named volumes para estado; bind mounts para dev; backup de volumes.
- Redes definidas pelo usuário/Compose; resolver por nome.
- Exponha o mínimo de portas; credenciais por env/secrets.

## Relação com outros conceitos

- [Compose](../04-docker-compose/README.md), [Kubernetes volumes/services](../../21-kubernetes/README.md),
  [networking cloud](../../19-cloud/05-networking/README.md).
- [Filesystem](../../02-linux-shell-environment/02-filesystem/README.md).

## Exercícios

1. Suba um Postgres com named volume, grave dados, remova o container e suba outro com o mesmo volume.
2. Crie uma rede, rode Postgres e um cliente nela e conecte por nome.
3. Explique por que `localhost:5432` falha dentro de um container para alcançar outro container.
4. Faça um backup de um named volume para um tar.

## Referências

- Docker — Volumes, Bind mounts, Networking overview.
