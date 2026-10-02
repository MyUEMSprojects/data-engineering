# 03 — Git e Engenharia de Software

> 🟢 Nível 1 — Foundations · Pré: [02 — Linux & Shell](../02-linux-shell-environment/README.md) ·
> Próximo: [04 — Python para DE](../04-python-for-data-engineering/README.md)

Data Engineering **é** engenharia de software aplicada a dados. Pipelines são
código: precisam de versionamento, revisão, testes, lint e organização. Este
módulo cobre as práticas de SWE que tornam seu trabalho reprodutível,
colaborativo e seguro de mudar — a base do [DataOps](../23-cicd-dataops/README.md)
e do [CI/CD](../23-cicd-dataops/README.md).

## Por que isso é fundacional

- Todo código de pipeline, SQL, DAG e IaC vive em **Git**.
- Mudanças em dados são arriscadas; **revisão e testes** reduzem incidentes.
- **Reprodutibilidade** (versionar código + ambiente) é um princípio central de DE.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Git básico](01-git-basics/README.md) | Modelo do Git, staging, commits, remotos |
| 02 | [Branching, merge e rebase](02-branching-merging-rebasing/README.md) | Fluxos de trabalho e integração de mudanças |
| 03 | [Pull requests e code review](03-pull-requests-code-review/README.md) | Colaboração e revisão de código |
| 04 | [Conventional commits e versionamento](04-conventional-commits-versioning/README.md) | Mensagens padronizadas e SemVer |
| 05 | [Testes](05-testing/README.md) | Pirâmide de testes, pytest, testes de dados |
| 06 | [Lint e formatação](06-linting-formatting/README.md) | ruff, black, pre-commit |
| 07 | [Organização de projetos](07-project-organization/README.md) | Estrutura, dependências, documentação |

## Dependências internas

```text
Git básico ─► Branching/merge/rebase ─► Pull requests & code review
                                               │
Conventional commits ──────────────────────────┤
                                               ▼
Testes ─► Lint & formatação ─► Organização de projetos ─► (CI/CD, módulo 23)
```

## Checkpoint

- [ ] Explicar a área de *staging* e o fluxo working dir → index → commit → remoto.
- [ ] Criar branches, resolver conflitos e escolher entre `merge` e `rebase`.
- [ ] Abrir um PR claro e fazer uma revisão construtiva.
- [ ] Escrever mensagens no padrão Conventional Commits e versionar com SemVer.
- [ ] Escrever testes com `pytest` e entender a pirâmide de testes.
- [ ] Configurar `ruff`/`black` e um hook de `pre-commit`.
- [ ] Estruturar um projeto Python de DE com dependências e README.

## Referências do módulo

- *Pro Git*, Scott Chacon & Ben Straub (git-scm.com/book) — gratuito.
- Documentação oficial do Git, GitHub Docs.
- *The Pragmatic Programmer*, Hunt & Thomas.
