# Images e containers

> 🟣 Cloud & Infra · Parte de [20 — Containers](../README.md)

## Imagem vs container

- **Imagem** — artefato **imutável** em camadas (SO base + dependências + seu código). É o "molde".
- **Container** — **instância** em execução da imagem, com uma camada gravável efêmera por cima.

```text
imagem (camadas read-only):  [código] [deps pip] [python] [debian-slim]
container = imagem + camada de escrita (some ao remover o container)
```

## Dockerfile

Receita declarativa; cada instrução gera uma **camada** (cacheada).

```dockerfile
FROM python:3.12-slim
WORKDIR /app

# 1) dependências primeiro (cache: só reinstala se requirements mudar)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) código depois (muda mais)
COPY src/ ./src/

# usuário não-root
RUN useradd -m app && chown -R app /app
USER app

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "src.pipeline"]
CMD ["--date", "2024-01-15"]
```

| Instrução | Função |
| --- | --- |
| `FROM` | imagem base |
| `WORKDIR` | diretório de trabalho |
| `COPY` / `ADD` | copia arquivos (prefira `COPY`) |
| `RUN` | executa comando no build (cria camada) |
| `ENV` | variável de ambiente |
| `USER` | usuário de execução |
| `ENTRYPOINT` / `CMD` | o que roda; `CMD` fornece argumentos default sobrescrevíveis |
| `EXPOSE` | documenta porta |
| `HEALTHCHECK` | verifica saúde |

## Cache de camadas (otimização principal)

O Docker reutiliza camadas inalteradas. **Ordene do que muda menos para o que muda mais**: base → deps →
código. Mudar uma linha invalida **ela e as seguintes**. Por isso `COPY requirements.txt` + `pip install`
vêm **antes** de `COPY src/`.

## `.dockerignore`

Exclua do contexto de build o que não deve entrar (`.git`, `.venv`, dados, `__pycache__`, segredos):

```text
.git
.venv
__pycache__/
data/
.env
```

Reduz o tamanho/tempo de build e evita vazar segredos na imagem.

## Build e execução

```bash
docker build -t meu-pipeline:1.2.0 .
docker run --rm -e DATABASE_URL=... meu-pipeline:1.2.0 --date 2024-01-15
docker images ; docker rmi <id>
docker history meu-pipeline:1.2.0        # camadas e tamanhos
```

## Ciclo de vida do container

`created → running → paused/stopped → removed`. Comandos: `run`, `start`, `stop`, `restart`, `rm`,
`logs`, `exec`, `inspect`. Use `--rm` para jobs one-shot.

## Escolhendo a imagem base

| Base | Prós | Contras |
| --- | --- | --- |
| `python:3.12` | completa | grande |
| `python:3.12-slim` | **bom equilíbrio** | menos libs de sistema |
| `alpine` | minúscula | musl pode quebrar wheels/pandas (cuidado) |
| `distroless` | mínima, segura | sem shell (debug difícil) |

Fixe versões (`python:3.12.4-slim`) e, em produção, considere *digest* (`@sha256:...`) para
reprodutibilidade.

## Configuração: variáveis de ambiente

Configuração e segredos entram em **runtime** (`-e`, `--env-file`, secrets do orquestrador), **nunca**
embutidos na imagem ([IAM/secrets](../../19-cloud/06-iam-secrets/README.md)).

## Erros comuns

- `COPY . .` antes de instalar deps (quebra o cache a cada mudança de código).
- Sem `.dockerignore` (imagem inchada, segredos vazados).
- Tag `latest` (não reprodutível).
- Rodar como root; segredos no `ENV`/`RUN`.
- Muitos `RUN` separados deixando lixo (combine e limpe no mesmo layer).

## Boas práticas

- Ordene camadas por frequência de mudança; `slim` + `.dockerignore`.
- `USER` não-root; tags fixas; uma responsabilidade por imagem.
- `--no-cache-dir` no pip; limpe caches no mesmo `RUN`.
- Use [multi-stage](../06-multi-stage-builds/README.md) para builds com compilação.

## Relação com outros conceitos

- [Docker concepts](../01-docker-concepts/README.md), [registries](../05-registries/README.md),
  [multi-stage](../06-multi-stage-builds/README.md), [segurança](../07-container-security/README.md).
- [Ambientes Python/lockfile](../../04-python-for-data-engineering/02-environments-and-packaging/README.md).

## Exercícios

1. Escreva um Dockerfile para um pipeline Python com cache eficiente e usuário não-root.
2. Meça o efeito de ordenar mal `COPY` no tempo de rebuild.
3. Compare o tamanho de `python:3.12` vs `-slim` com `docker images`.
4. Explique `ENTRYPOINT` vs `CMD`.

## Referências

- Docker — Dockerfile reference e best practices for building images.
