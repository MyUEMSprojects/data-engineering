# Organização de projetos

> 🟢 Foundations · Parte de [03 — Git & SWE](../README.md)

## O que é

Como estruturar um projeto de Data Engineering: layout de diretórios, gestão de
dependências, configuração, documentação e separação de responsabilidades. Um
projeto bem organizado é fácil de entender, testar, executar e evoluir.

## Por que importa

- **Onboarding** — alguém novo entende e roda o projeto rápido.
- **Manutenção** — mudar algo não quebra o resto (baixo acoplamento).
- **Reprodutibilidade** — qualquer pessoa reconstrói o mesmo ambiente.
- **Reuso** — lógica compartilhada não é copiada e colada.

## Layout típico de um projeto de pipeline

```text
meu-pipeline/
├── README.md                 # o que é, como rodar, arquitetura
├── pyproject.toml            # metadados, deps, config de ferramentas
├── requirements.txt          # (ou gerado do pyproject) deps de runtime
├── .env.example              # variáveis necessárias (SEM valores reais)
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml        # serviços locais (DB, etc.)
├── Dockerfile
├── src/
│   └── meu_pipeline/
│       ├── __init__.py
│       ├── config.py         # configuração centralizada (lê env)
│       ├── extract.py        # ingestão (I/O)
│       ├── transform.py      # transformações (lógica PURA, testável)
│       ├── load.py           # carga (I/O)
│       └── pipeline.py       # orquestra extract→transform→load
├── tests/
│   ├── conftest.py           # fixtures compartilhadas
│   ├── test_transform.py
│   └── fixtures/             # amostras pequenas de dados
├── sql/                      # queries/DDL versionadas
├── dags/                     # DAGs de orquestração (se Airflow)
└── docs/                     # documentação adicional, ADRs
```

## Separation of concerns (o princípio central)

Separe **I/O** (ler/escrever de fontes e destinos) da **lógica de transformação**
(pura, sem efeitos colaterais). Isso torna a lógica testável sem banco/rede e
facilita trocar a fonte/destino.

```python
# transform.py — PURO: entra dado, sai dado. Fácil de testar.
import pandas as pd

def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.dropna(subset=["order_id"])
          .drop_duplicates(subset=["order_id"])
          .assign(email=lambda d: d["email"].str.strip().str.lower())
    )

# pipeline.py — orquestra o I/O com a lógica.
from .extract import read_orders
from .transform import clean_orders
from .load import write_orders

def run(date: str) -> None:
    raw = read_orders(date)          # I/O
    clean = clean_orders(raw)        # lógica pura (testável)
    write_orders(clean, date)        # I/O
```

## Gestão de dependências

- **`pyproject.toml`** é o padrão moderno (PEP 621) para metadados + dependências.
- **Fixe versões** (lockfile) para reprodutibilidade: `uv`, `pip-tools`
  (`requirements.lock`), `poetry` ou `pipenv`.
- **Ambiente isolado** por projeto (`venv`/`uv`) — nunca instale no Python global.
  Ver [environments & packaging](../../04-python-for-data-engineering/02-environments-and-packaging/README.md).

```toml
[project]
name = "meu-pipeline"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pandas>=2.2", "requests>=2.32", "psycopg[binary]>=3.2"]

[project.optional-dependencies]
dev = ["pytest", "ruff", "black", "mypy", "pre-commit"]
```

## Configuração (12-factor)

- Configuração vem do **ambiente**, não do código: URLs, credenciais, caminhos em
  variáveis de ambiente (`.env` local, secret manager em produção).
- Centralize a leitura em um `config.py` (ex.: com `pydantic-settings`).
- **Nunca** comite segredos; versione um `.env.example` documentando o que é
  necessário. Ver [security](../../26-security/04-secrets-management/README.md).

```python
# config.py
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    db_url: str = os.environ["DATABASE_URL"]
    raw_dir: str = os.environ.get("RAW_DIR", "/data/raw")

settings = Settings()
```

## Documentação

- **README** respondendo: o que é, por que existe, como instalar, como rodar, como
  testar, arquitetura, decisões.
- **Docstrings** nas funções públicas.
- **ADRs** (*Architecture Decision Records*) — registros curtos de decisões
  importantes e seus motivos (ótimo para dados: "por que escolhemos ELT", "por que
  particionamos por data").

## Princípios de engenharia aplicados

| Princípio | Como aparece aqui |
| --- | --- |
| **KISS** | estrutura simples; não abstrair cedo demais |
| **DRY** | lógica compartilhada em módulos, não copiada |
| **Separation of concerns** | I/O separado de transformação |
| **Reproducibility** | deps fixas, ambiente isolado, Docker |
| **Testability** | lógica pura, testável sem infra |
| **Maintainability** | nomes claros, módulos coesos, docs |

Evite o oposto: um único script gigante que lê, transforma e grava tudo misturado,
com dependências globais e segredos embutidos.

## Erros comuns

- "Script monstro" sem módulos nem testes.
- Dependências sem fixar versão → "funciona hoje, quebra amanhã".
- Segredos no código; configuração *hardcoded*.
- README ausente ou desatualizado.
- Copiar/colar a mesma transformação em vários lugares (viola DRY).

## Boas práticas

- Comece simples, mas com a separação I/O × lógica desde o início.
- Um ambiente isolado + lockfile + `pyproject.toml`.
- Documente decisões (ADRs) enquanto estão frescas.
- Containerize para reprodutibilidade ([Docker](../../20-containers/README.md)).

## Relação com outros conceitos

- Base para [testes](../05-testing/README.md) e
  [lint/format](../06-linting-formatting/README.md).
- Reprodutibilidade conecta a [containers](../../20-containers/README.md) e
  [IaC](../../22-infrastructure-as-code/README.md).
- Aplicado em todos os [projetos](../../projects/README.md).

## Exercícios

1. Reestruture um script único em `extract`/`transform`/`load` + `pipeline`,
   isolando a lógica pura.
2. Crie um `pyproject.toml` com dependências de runtime e de dev.
3. Mova configuração *hardcoded* para variáveis de ambiente lidas em `config.py` e
   documente-as em `.env.example`.
4. Escreva um ADR curto justificando uma decisão de arquitetura do seu projeto.

## Referências

- The Twelve-Factor App (12factor.net).
- PEP 621 / Python Packaging User Guide (packaging.python.org).
- Percival, H.; Gregory, B. *Architecture Patterns with Python*.
- ADR (adr.github.io).
