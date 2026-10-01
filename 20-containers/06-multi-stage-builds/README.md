# Multi-stage builds

> 🟣 Cloud & Infra · Parte de [20 — Containers](../README.md)

## O que é

**Multi-stage build** usa **vários `FROM`** num mesmo Dockerfile: um estágio de **build** (com compiladores,
ferramentas, caches) e um estágio **final** que copia **apenas o necessário** do anterior. O resultado é uma
imagem de runtime **pequena, rápida de baixar e com menor superfície de ataque**.

## Problema que resolve

Para instalar dependências com extensões nativas (pandas, pyarrow, psycopg, numpy) ou compilar código,
você precisa de **gcc, headers, git, caches pip**. Se tudo isso fica na imagem final:

- Imagem **gigante** (centenas de MB/GB) → deploy e pull lentos, mais custo.
- **Mais vulnerabilidades** (ferramentas de build desnecessárias em produção).
- Possível vazamento de segredos usados no build.

## Exemplo (Python com dependências compiladas)

```dockerfile
# --- Estágio 1: builder (pesado, descartável) ---
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Estágio 2: runtime (enxuto) ---
FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local            # só as libs instaladas
WORKDIR /app
COPY src/ ./src/
RUN useradd -m app && chown -R app /app
USER app
ENTRYPOINT ["python", "-m", "src.pipeline"]
```

O estágio `builder` (com gcc etc.) **não** vai para a imagem final: só o que foi copiado com
`COPY --from=builder`.

## Variações úteis

- **Estágio de testes/lint**: `FROM builder AS test` roda `pytest`/`ruff` no CI sem contaminar o runtime
  (`docker build --target test .`).
- **`--target`** — construir até um estágio específico (dev vs prod).
- **Imagem final mínima** — `slim` ou **distroless**; para binários estáticos (Go), `scratch`.
- **Cache de dependências** — BuildKit cache mounts: `RUN --mount=type=cache,target=/root/.cache/pip pip install ...`.
- **Virtualenv copiável**: criar `/opt/venv` no builder e copiá-lo ao runtime.

## Benefícios medidos

| Aspecto | Single-stage | Multi-stage |
| --- | --- | --- |
| Tamanho | grande | **bem menor** |
| Superfície de ataque | ampla (compiladores etc.) | **reduzida** |
| Segredos de build | risco de ficar na imagem | descartados com o estágio |
| Pull/deploy | lento | **rápido** |

## Cuidados

- Bibliotecas **nativas de runtime** (ex.: `libpq5`) precisam estar na imagem final (só as de **build**
  `-dev` ficam no builder).
- Mantenha **mesma versão/base** entre builder e runtime (ABI/glibc compatíveis; cuidado com Alpine/musl).
- Não copie segredos para o estágio final; use `--mount=type=secret` do BuildKit para segredos de build.

## Erros comuns

- Copiar o builder inteiro (`COPY --from=builder / /`) — perde o benefício.
- Faltar lib de runtime na imagem final ("ImportError: libpq.so").
- Misturar Alpine runtime com wheels compiladas para glibc.
- Colocar tokens/credenciais no estágio final ou em `ARG` (ficam no histórico).

## Boas práticas

- Builder para compilar; runtime só com o necessário, `USER` não-root.
- Aproveite cache de camadas e cache mounts; estágio de teste separado.
- Verifique o tamanho (`docker images`, `dive`) e escaneie a imagem final
  ([security](../07-container-security/README.md)).

## Relação com outros conceitos

- [Images/Dockerfile](../02-images-containers/README.md), [security](../07-container-security/README.md),
  [registries](../05-registries/README.md), [CI/CD](../../23-cicd-dataops/README.md).

## Exercícios

1. Converta um Dockerfile single-stage de um pipeline pandas+psycopg em multi-stage e compare tamanhos.
2. Adicione um estágio `test` que roda `pytest` e use `--target test` no CI.
3. Explique por que `libpq-dev` fica no builder e `libpq5` no runtime.

## Referências

- Docker — Multi-stage builds; BuildKit (cache/secret mounts); projeto `dive`.
