# Contribuindo

Obrigado pelo interesse em contribuir! Este repositório é uma trilha de estudos
aberta de Engenharia de Dados. Contribuições que melhorem a precisão técnica, a
clareza ou a profundidade do conteúdo são muito bem-vindas.

## Como contribuir

1. Abra uma *issue* descrevendo o que pretende mudar (correção, melhoria de
   conteúdo, novo tópico, novo exercício/projeto).
2. Faça um *fork* e crie uma branch descritiva:
   `git checkout -b docs/melhora-readme-spark`.
3. Siga as [convenções do repositório](CONVENTIONS.md).
4. Garanta que o CI passa (lint de Markdown, verificação de links, lint/testes
   de Python quando houver código).
5. Abra um *Pull Request* usando o template.

## Padrões de qualidade

- **Precisão acima de tudo.** Não invente APIs, comandos ou comportamentos. Ao
  escrever sobre uma ferramenta, confira a documentação oficial e, quando o
  comportamento depender de versão, cite a versão.
- **Profundidade com densidade.** Evite tanto definições de uma linha quanto
  textos infláveis. O alvo é "apostila técnica bem organizada".
- **Todo diretório novo precisa de um `README.md`** próprio e específico.
- **Links internos relativos** e verificados.
- **Referências de qualidade**: documentação oficial, livros reconhecidos,
  papers, RFCs. Evite blogs de baixa qualidade só para preencher.

## Rodando as verificações localmente

```bash
# Lint de Markdown (requer Node)
npx markdownlint-cli2 "**/*.md"

# Verificação de links internos
npx markdown-link-check README.md

# Python (dentro de um projeto que tenha código)
pip install -r requirements-dev.txt
ruff check .
black --check .
pytest
```

## Checklist antes do PR

- [ ] Todo diretório novo tem `README.md`.
- [ ] Links internos funcionam.
- [ ] Conteúdo revisado tecnicamente e ortograficamente.
- [ ] Referências incluídas.
- [ ] Código (se houver) formatado, com lint e testes passando.
- [ ] Commits no padrão Conventional Commits.
