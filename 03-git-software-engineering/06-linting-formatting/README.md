# Lint e formatação

> 🟢 Foundations · Parte de [03 — Git & SWE](../README.md)

## O que é

- **Formatação** — padroniza a *aparência* do código (indentação, aspas, quebras)
  automaticamente. Ferramenta: **`black`** (ou o formatador do `ruff`).
- **Lint** — analisa o código em busca de **problemas** (bugs potenciais, imports
  não usados, variáveis indefinidas, antipadrões). Ferramenta: **`ruff`**.
- **Type checking** — verifica consistência de tipos. Ferramenta: **`mypy`**.

## Por que existe

- **Elimina debates de estilo** no code review — a máquina decide, o humano revisa
  lógica.
- **Pega bugs cedo**, antes de rodar (variável não usada, comparação suspeita).
- **Consistência** facilita ler código de qualquer pessoa do time.
- Diffs menores: sem mudanças de formatação ruidosas.

## black — formatação

`black` é "opinativo": quase sem configuração, reformata para um estilo único.

```bash
black .              # formata tudo
black --check .      # só verifica (usado no CI; falha se desformatado)
black --diff arquivo.py
```

## ruff — lint (e formatação) rápido

`ruff` é um linter extremamente rápido (escrito em Rust) que substitui vários
linters clássicos (flake8, isort, pyupgrade...). Também formata.

```bash
ruff check .             # lint
ruff check . --fix       # corrige o que for automático
ruff format .            # formata (alternativa ao black)
```

Configuração em `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]  # erros, pyflakes, imports, pyupgrade, bugbear
ignore = []

[tool.black]
line-length = 88
target-version = ["py312"]
```

> Escolha **um** formatador (black *ou* `ruff format`) para o time não brigar.

## mypy — checagem de tipos

Com [type hints](../../04-python-for-data-engineering/03-typing/README.md), o
`mypy` encontra incompatibilidades sem rodar o código:

```bash
mypy .
```

```python
def soma(valores: list[int]) -> int:
    return sum(valores)

soma(["a", "b"])  # mypy aponta: esperado list[int]
```

Tipos ajudam especialmente em DE, onde dados têm *shapes* e tipos que é fácil
confundir.

## pre-commit — rodar tudo automaticamente antes do commit

[`pre-commit`](https://pre-commit.com) instala *git hooks* que rodam os checadores
no `git commit`, impedindo que código problemático seja comitado.

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-added-large-files   # evita comitar dados grandes!
      - id: detect-private-key        # evita vazar chaves
```

```bash
pip install pre-commit
pre-commit install          # ativa os hooks
pre-commit run --all-files  # roda em todo o repositório
```

Note os hooks `check-added-large-files` e `detect-private-key` — defesas valiosas
em DE contra comitar datasets e segredos.

## Onde isso roda

1. **No editor** — feedback instantâneo (extensões de ruff/black).
2. **No `pre-commit`** — barreira local antes do commit.
3. **No [CI](../../23-cicd-dataops/README.md)** — barreira final no PR (`--check`
   falha o build se algo estiver fora do padrão).

Essa tripla defesa é o padrão profissional.

## Além de Python

- **SQL** — `sqlfluff` (lint/format de SQL), essencial com [dbt](../../28-dbt/README.md).
- **Shell** — `shellcheck` (ver [shell scripting](../../02-linux-shell-environment/05-shell-scripting/README.md)).
- **Markdown** — `markdownlint` (usado no [CI deste repo](../../.github/workflows/ci.yml)).
- **Terraform** — `terraform fmt`, `tflint` (ver [IaC](../../22-infrastructure-as-code/README.md)).

## Erros comuns

- Formatação manual (perda de tempo e diffs ruidosos).
- Discutir estilo no review em vez de automatizar.
- Ligar o lint num projeto legado e ser soterrado por avisos — ligue
  incrementalmente (selecione regras aos poucos).
- `# noqa`/`# type: ignore` em excesso, mascarando problemas reais.

## Boas práticas

- Formatador + linter + pre-commit desde o início do projeto.
- Mesma configuração em editor, pre-commit e CI (uma fonte da verdade:
  `pyproject.toml`).
- Trate avisos do linter com seriedade; suprima com justificativa pontual.

## Relação com outros conceitos

- Automatizado no [CI/CD](../../23-cicd-dataops/README.md).
- Depende de [typing](../../04-python-for-data-engineering/03-typing/README.md).
- Reduz atrito em [code review](../03-pull-requests-code-review/README.md).

## Exercícios

1. Configure `ruff` + `black` num projeto Python e corrija os apontamentos.
2. Adicione `pre-commit` com hooks de lint, format, `check-added-large-files` e
   `detect-private-key`; teste comitando um arquivo grande (deve bloquear).
3. Anote tipos numa função e rode `mypy`, corrigindo o que acusar.
4. Rode `sqlfluff` num arquivo `.sql` e observe as correções.

## Referências

- Documentação de `ruff` (docs.astral.sh/ruff), `black`, `mypy`.
- pre-commit.com. sqlfluff.com.
