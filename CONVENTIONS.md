# Convenções do Repositório

Este documento define as regras de consistência do repositório. Elas existem
para que o conteúdo pareça um material único e profissional, e não uma colagem
de estilos diferentes.

## 1. Idioma

| Elemento | Idioma |
| --- | --- |
| Nomes de diretórios | Inglês, `kebab-case` |
| Nomes de arquivos | Inglês, `kebab-case` (exceto convenções externas, ex.: `Dockerfile`) |
| Código (variáveis, funções, classes) | Inglês |
| Identificadores de dados (tabelas, colunas) | Inglês, `snake_case` |
| Conteúdo dos READMEs | Português (pt-BR) |
| Termos técnicos consagrados | Mantidos em inglês (ex.: *shuffle*, *watermark*, *backfill*) em itálico |

Motivo: o mercado de Data Engineering é internacional. Código e estrutura em
inglês tornam o material transferível para qualquer contexto; o conteúdo em
português otimiza o estudo.

## 2. Estrutura de diretórios

- Todo diretório de módulo/tópico/subtópico é prefixado com um número de dois
  dígitos que define a ordem pedagógica: `05-sql/`, `03-joins/`.
- **Regra inviolável:** todo diretório tem um `README.md` próprio que explica
  especificamente aquele conceito. Nenhum README de nível superior "explica
  tudo" dos filhos.
- Profundidade: `módulo/tópico/subtópico/` e, quando necessário,
  `sub-subtópico/`.

## 3. Estrutura de um README de conceito

Cada README de tópico técnico segue, quando aplicável, esta ordem (seções são
omitidas quando não fizerem sentido — não force):

1. O que é / Por que existe / Que problema resolve
2. Conceitos fundamentais
3. Como funciona (arquitetura, componentes, fluxo)
4. Exemplos práticos (código ou diagramas)
5. Casos de uso
6. Vantagens, limitações e *trade-offs*
7. Quando usar / Quando NÃO usar
8. Relação com outros conceitos (com links relativos)
9. Erros comuns
10. Boas práticas
11. Performance / escalabilidade / segurança / observabilidade (quando relevante)
12. Exercícios (quando fizer sentido)
13. Referências

O README de nível **módulo** é um índice + visão geral: explica o tema do
módulo, lista os tópicos com links, mostra dependências e termina com um
**Checkpoint** (critérios de domínio).

## 4. Markdown

- Títulos em *sentence case*: `## Como funciona`, não `## Como Funciona`.
- Um `#` (H1) por arquivo.
- Blocos de código sempre com linguagem: ` ```python `, ` ```sql `, ` ```bash `.
- Tabelas para comparações e *trade-offs*.
- Diagramas em ASCII ou [Mermaid](https://mermaid.js.org/) quando ajudarem.
- Links internos são **relativos** (`../03-sql/README.md`), nunca absolutos.
- Linha de no máximo ~100 colunas no texto-fonte, quando viável.

## 5. Código Python

- Formatação: [`black`](https://black.readthedocs.io/) (padrão).
- Lint: [`ruff`](https://docs.astral.sh/ruff/).
- Tipagem: anotações de tipo em funções públicas; `mypy` nos projetos.
- Docstrings no estilo Google.
- Testes com `pytest`; nomes `test_*.py`.
- Estrutura de pacote por projeto; dependências em `requirements.txt` ou
  `pyproject.toml`.

## 6. SQL

- Palavras-chave em MAIÚSCULAS (`SELECT`, `JOIN`), identificadores em
  `snake_case`.
- CTEs preferidas a subqueries aninhadas quando melhoram a leitura.
- Um campo por linha em `SELECT` longos.

## 7. Datasets e exemplos

- Dados reais **nunca** são versionados (ver `.gitignore`).
- Amostras pequenas e sintéticas vão em `sample_data/` ou `fixtures/`.
- Exemplos devem ser tecnicamente coerentes e, nos projetos, executáveis.

## 8. Commits

[Conventional Commits](https://www.conventionalcommits.org/):

```text
feat(sql): adiciona módulo de window functions
docs(foundations): revisa README de CAP theorem
fix(project-01): corrige conexão com PostgreSQL
```

Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.

## 9. Níveis de dificuldade

Cada módulo indica seu nível no README raiz:

- 🟢 **Foundations** — conceitual, pré-requisito de tudo.
- 🔵 **Core** — habilidades diárias do Data Engineer.
- 🟣 **Advanced** — especialização / arquitetura.
