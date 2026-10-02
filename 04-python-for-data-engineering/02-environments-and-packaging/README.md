# Ambientes e packaging

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

## O que é

Isolar as dependências de cada projeto (ambientes virtuais) e declará-las de forma
reprodutível (packaging) para que qualquer pessoa — ou qualquer máquina/CI/
container — reconstrua **o mesmo** ambiente.

## Por que importa (reprodutibilidade)

"Funciona na minha máquina" é inaceitável em dados: um pipeline deve rodar igual no
laptop, no CI e em produção. Versões diferentes de pandas/pyarrow mudam resultados
e quebram jobs. Ambientes isolados + versões fixas (*lockfile*) são a base da
reprodutibilidade — um princípio central de DE.

## Ambientes virtuais

Cada projeto tem seu próprio ambiente, isolado do Python do sistema.

```bash
python3 -m venv .venv            # cria o ambiente
source .venv/bin/activate        # ativa (Linux/macOS)
# .venv\Scripts\activate         # Windows
pip install pandas               # instala só neste ambiente
deactivate                       # sai
```

Nunca instale pacotes no Python global — vira um emaranhado de versões
conflitantes.

## Ferramentas (panorama atual)

| Ferramenta | Papel | Notas |
| --- | --- | --- |
| `venv` + `pip` | padrão, embutido | simples; combine com lockfile |
| **`uv`** | gerenciador rápido (Rust) | cria venv, instala e resolve muito rápido; moderno |
| `pip-tools` | gera lockfile (`pip-compile`) | sobre pip |
| `poetry` | deps + build + lock | tudo-em-um, popular |
| `conda`/`mamba` | ambientes + libs nativas | útil quando há dependências de sistema (geo, ML) |

> Recomendação atual para projetos novos: **`uv`** (rápido e simples) ou
> `venv`+`pip-tools`. Escolha uma e padronize.

Exemplo com `uv`:

```bash
uv venv                    # cria .venv
uv pip install pandas requests
uv pip compile pyproject.toml -o requirements.lock   # lockfile
uv pip sync requirements.lock                         # instala exatamente o lock
```

## Declarando dependências

### pyproject.toml (padrão moderno, PEP 621)

```toml
[project]
name = "meu-pipeline"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pandas>=2.2,<3",
    "requests>=2.32",
    "psycopg[binary]>=3.2",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "black", "mypy"]
```

### requirements.txt vs lockfile

- `requirements.txt` com faixas (`pandas>=2.2`) diz o que você *quer*.
- **lockfile** (`requirements.lock`) fixa versões *exatas* de tudo (inclusive
  dependências transitivas) → reprodutível. **Use lockfile em produção/CI.**

## Versionamento do Python em si

Além das libs, fixe a versão do **Python** (ex.: 3.12). Ferramentas: `pyenv`
(instala múltiplas versões), `uv python`, ou a imagem base do
[Docker](../../20-containers/README.md) (`python:3.12-slim`). O container é a
forma mais forte de reprodutibilidade.

## Empacotando seu código

Para reutilizar código entre DAGs/jobs, transforme-o em um pacote instalável:

```bash
pip install -e .        # instala seu projeto em modo editável (dev)
```

Com `src/` layout e `pyproject.toml`, `import meu_pipeline` passa a funcionar em
qualquer lugar do ambiente — evita hacks de `sys.path`.

## Reprodutibilidade de ponta a ponta

```text
pyproject.toml (o que quero)
      │  resolve
      ▼
lockfile (versões exatas)  ──► venv local  ──► CI  ──► imagem Docker ──► produção
                               (mesma coisa em todos os ambientes)
```

## Erros comuns

- Instalar no Python global → conflitos.
- Sem lockfile → "build quebrou do nada" quando uma transitiva lançou versão nova.
- Comitar a pasta `.venv/` (adicione ao [.gitignore](../../.gitignore)).
- Misturar `conda` e `pip` sem cuidado.
- Não fixar a versão do Python.

## Boas práticas

- Um ambiente isolado por projeto; `pyproject.toml` + lockfile.
- Mesmas versões em local, CI e container.
- Separe deps de runtime das de dev (`[dev]`).
- Atualize dependências com intenção (e rode os testes depois).

## Relação com outros conceitos

- Base de [organização de projetos](../../03-git-software-engineering/07-project-organization/README.md).
- Reprodutibilidade conecta a [containers](../../20-containers/README.md) e
  [CI/CD](../../23-cicd-dataops/README.md).

## Exercícios

1. Crie um ambiente com `uv` (ou venv), instale pandas e gere um lockfile.
2. Em outra máquina/pasta, reconstrua o ambiente a partir do lockfile e confirme as
   mesmas versões.
3. Empacote um módulo com `pyproject.toml` e instale-o em modo editável; importe-o
   de outro diretório.
4. Explique a diferença entre `requirements.txt` com faixas e um lockfile.

## Referências

- Python Packaging User Guide (packaging.python.org).
- Documentação do `uv` (docs.astral.sh/uv), `pip-tools`, `poetry`.
- PEP 621, PEP 517/518.
