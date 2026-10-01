# Exercícios — Módulo 20: Contêineres

Teoria em [20-containers](../../20-containers/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Imagem × contêiner

Qual a diferença entre **imagem** e **contêiner**? O que acontece com os dados gravados dentro de um contêiner ao removê-lo?

<details><summary>Gabarito</summary>

Imagem: *template* imutável em camadas. Contêiner: instância em execução (camada gravável por cima). Dados na camada do contêiner **somem** ao removê-lo — use **volumes** para persistir. Ver [imagens e contêineres](../../20-containers/02-images-containers/README.md) e [volumes](../../20-containers/03-volumes-networks/README.md).
</details>

## 2. 🟢 Debugging — "Connection refused" entre contêineres

Num Compose, o app usa `localhost:5432` para falar com o Postgres e falha. Por quê?

<details><summary>Gabarito</summary>

Dentro do contêiner, `localhost` é **ele mesmo**. Use o **nome do serviço** (`postgres:5432`) na rede do Compose. `ports:` publica para o **host**, não é necessário para tráfego entre serviços. E `depends_on` com `condition: service_healthy` ordena o início. Ver [Compose](../../20-containers/04-docker-compose/README.md).
</details>

## 3. 🔵 Implementação — Dockerfile eficiente

Reescreva para melhor cache e imagem menor:
```dockerfile
FROM python:3.12
COPY . /app
RUN pip install -r /app/requirements.txt
CMD ["python", "/app/main.py"]
```

<details><summary>Gabarito</summary>

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt     # camada reaproveitada se as dependências não mudam
COPY src ./src
RUN useradd -m app && chown -R app /app
USER app                                               # não rode como root
CMD ["python", "-m", "main"]
```
Copiar `requirements.txt` **antes** do código preserva o cache; `slim` reduz a imagem; use `.dockerignore`. Ver [multi-stage builds](../../20-containers/06-multi-stage-builds/README.md).
</details>

## 4. 🔵 Implementação — Multi-stage

Quando um *multi-stage build* ajuda um projeto Python com dependências nativas (compiladores)? Esboce.

<details><summary>Gabarito</summary>

```dockerfile
FROM python:3.12 AS build
RUN pip wheel --wheel-dir /wheels -r requirements.txt    # compilar aqui (gcc etc.)

FROM python:3.12-slim
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt
```
A imagem final **não carrega** compiladores nem arquivos de build: menor e com superfície de ataque reduzida.
</details>

## 5. 🟣 Debugging — O contêiner que vaza segredo

`docker history` de uma imagem mostra `ARG DB_PASSWORD=...` e `COPY .env /app`. Qual o problema e como corrigir?

<details><summary>Gabarito</summary>

Segredos ficam **gravados nas camadas** da imagem (recuperáveis por quem puxar a imagem). Correção: nunca `COPY .env`/`ARG` com segredo; injete em **tempo de execução** (variáveis, *secrets* do orquestrador, cofre) ou use `RUN --mount=type=secret` no build. **Rotacione** a credencial vazada. Ver [segurança de contêineres](../../20-containers/07-container-security/README.md).
</details>

## 6. 🟣 Arquitetura — Dev ≡ Prod

Como usar contêineres para reduzir o "funciona na minha máquina" em um time de dados (jobs, dbt, testes)? Cite três práticas.

<details><summary>Gabarito</summary>

(1) **Mesma imagem** em dev, CI e produção (versões fixas de dependências). (2) `docker compose` para dependências (Postgres, Kafka) reproduzíveis — como nos [projetos](../../projects/README.md). (3) Testes de integração rodando em contêineres no CI. Extras: imagens com *digest*/tag imutável e varredura de vulnerabilidades. Ver [conceitos](../../20-containers/01-docker-concepts/README.md).
</details>
