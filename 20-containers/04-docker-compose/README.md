# Docker Compose

> 🟣 Cloud & Infra · Parte de [20 — Containers](../README.md)

## O que é

**Docker Compose** define e executa **aplicações multi-container** a partir de um arquivo YAML
(`docker-compose.yml` / `compose.yaml`). Em Data Engineering é a ferramenta que sobe **ambientes locais
completos** (Postgres + MinIO + Kafka + Airflow + Spark) com um comando — base de todos os
[projetos](../../projects/README.md) deste repositório.

## Por que usar

- **Reprodutibilidade** — o ambiente inteiro versionado em Git.
- **Um comando** — `docker compose up` sobe tudo, na ordem certa, na mesma rede.
- **Isolamento** — cada projeto com seu stack, sem poluir a máquina.
- Paridade dev/CI (rodar integração com serviços reais efêmeros).

> Compose é para **dev/teste/ambientes pequenos**. Produção em escala usa
> [Kubernetes](../../21-kubernetes/README.md) ou serviços gerenciados.

## Exemplo: Postgres + MinIO + app

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: de
      POSTGRES_PASSWORD: de
      POSTGRES_DB: warehouse
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U de -d warehouse"]
      interval: 5s
      retries: 10

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio12345
    volumes: ["minio:/data"]
    ports: ["9000:9000", "9001:9001"]

  pipeline:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://de:de@postgres:5432/warehouse
    volumes: ["./data:/app/data"]

volumes:
  pgdata:
  minio:
```

## Conceitos

| Elemento | Função |
| --- | --- |
| `services` | cada container/serviço |
| `image` / `build` | usar imagem pronta ou construir do Dockerfile |
| `environment` / `env_file` | variáveis (segredos via `.env` não versionado) |
| `volumes` | persistência / bind mounts |
| `ports` | publicação ao host |
| `depends_on` | ordem de start (com `condition: service_healthy`) |
| `healthcheck` | define "pronto" de verdade |
| `profiles` | grupos opcionais de serviços |
| rede default | Compose cria uma rede; serviços se resolvem **pelo nome** (`postgres`) |

## Comandos essenciais

```bash
docker compose up -d            # sobe em background
docker compose ps ; docker compose logs -f pipeline
docker compose exec postgres psql -U de warehouse
docker compose run --rm pipeline python -m src.pipeline --date 2024-01-15
docker compose down             # derruba (mantém volumes)
docker compose down -v          # derruba E apaga volumes
docker compose up --build       # reconstrói imagens
```

## `depends_on` e prontidão

`depends_on` sozinho só ordena o **start**, não garante que o serviço esteja **pronto** (o Postgres pode
levar segundos para aceitar conexões). Use **healthcheck** + `condition: service_healthy`, ou *retry* no
app ([retries](../../09-etl-elt/07-idempotency-retries/README.md)).

## Configuração e segredos

- Use `.env` (fora do Git — ver [.gitignore](../../.gitignore)) e `${VARIAVEL}` no YAML; versione um
  `.env.example`.
- Segredos reais **não** vão no `docker-compose.yml` versionado.
- `docker-compose.override.yml` para ajustes locais (também ignorado no Git).

## Padrões úteis para DE

- **Stack local de dados**: Postgres (warehouse) + MinIO (S3) + Airflow + dbt + Kafka/Redpanda + Spark.
- **Testes de integração** em CI com serviços efêmeros.
- **Perfis** para ligar/desligar componentes pesados (ex.: `--profile streaming`).

## Erros comuns

- Assumir que `depends_on` espera o serviço estar pronto.
- Segredos/credenciais comitados no YAML.
- Esquecer volumes → perder dados no `down -v`/recriação.
- Portas em conflito com serviços já rodando no host.
- Usar Compose como orquestrador de produção.

## Boas práticas

- Healthchecks, volumes nomeados, `.env.example`, versões de imagem fixas.
- Um Compose por projeto, documentado no README (`docker compose up`).
- `down -v` só quando quiser resetar o estado.

## Relação com outros conceitos

- [Volumes/networks](../03-volumes-networks/README.md), [images](../02-images-containers/README.md),
  [Kubernetes](../../21-kubernetes/README.md); usado em todos os [projetos](../../projects/README.md).
- [Ambiente local](../../README.md#ambiente-local).

## Exercícios

1. Crie um Compose com Postgres + um app que aguarda o banco ficar saudável.
2. Adicione MinIO e escreva um arquivo Parquet nele a partir do app.
3. Explique a diferença entre `depends_on` simples e com `service_healthy`.
4. Use `profiles` para tornar opcional um serviço de streaming.

## Referências

- Documentação do Docker Compose (docs.docker.com/compose); Compose Specification.
