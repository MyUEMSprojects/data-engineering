# Git básico

> 🟢 Foundations · Parte de [03 — Git & SWE](../README.md)

## O que é

**Git** é um sistema de controle de versão distribuído: registra o histórico de
mudanças do seu código, permite voltar no tempo, trabalhar em paralelo e colaborar.
"Distribuído" = cada clone tem o histórico completo, não depende de um servidor
central para a maioria das operações.

## Por que o DE precisa disso

Tudo que você produz — pipelines, SQL, DAGs, [IaC](../../22-infrastructure-as-code/README.md),
notebooks — é código e precisa de versionamento para ser reprodutível, auditável e
colaborativo. Git é também o gatilho do [CI/CD](../../23-cicd-dataops/README.md).

## O modelo mental do Git

Git tem **três áreas** e um repositório de objetos:

```text
 working directory      staging area (index)        repositório (.git)
 (seus arquivos)   ──►  (o que entrará no  )   ──►  (commits = snapshots
   git add             (próximo commit     )        imutáveis encadeados)
                                                git commit
```

- Um **commit** é um *snapshot* do projeto + metadados (autor, data, mensagem) +
  ponteiro para o commit pai. Tem um hash SHA único.
- **HEAD** aponta para o commit/branch atual.
- Git versiona **conteúdo**, não diffs; cada commit referencia a árvore completa
  (de forma eficiente, compartilhando objetos).

## Configuração inicial

```bash
git config --global user.name "Seu Nome"
git config --global user.email "voce@exemplo.com"
git config --global init.defaultBranch main
git config --global core.editor "code --wait"   # ou vim, nano
```

## Começando um repositório

```bash
git init                      # cria repositório no diretório atual
git clone <url>               # clona um repositório remoto
```

## O ciclo diário

```bash
git status                    # o que mudou, o que está staged
git diff                      # mudanças ainda não staged
git diff --staged            # mudanças já staged
git add arquivo.py           # move mudança para staging
git add -p                   # staging interativo (por trecho) — recomendado
git commit -m "feat: ..."    # cria commit com o que está staged
git log --oneline --graph    # histórico resumido
```

> `git add -p` deixa você revisar e escolher **o que** entra em cada commit →
> commits menores e coerentes.

## Trabalhando com remotos

```bash
git remote -v                     # remotos configurados
git remote add origin <url>       # adiciona o remoto "origin"
git push -u origin main           # envia e vincula a branch
git push                          # envia commits
git fetch                         # baixa mudanças remotas (sem aplicar)
git pull                          # fetch + merge (traz e integra)
```

`fetch` só baixa; `pull` baixa **e** integra na sua branch — por isso `fetch` +
inspeção é mais seguro quando há dúvida.

## Desfazendo coisas (com segurança)

```bash
git restore arquivo              # descarta mudanças não staged (Git 2.23+)
git restore --staged arquivo     # tira do staging (mantém a mudança)
git commit --amend               # corrige a mensagem/conteúdo do ÚLTIMO commit
git revert <hash>                # cria um commit que desfaz outro (seguro p/ histórico público)
git reset --soft HEAD~1          # desfaz commit, mantém mudanças staged
git reset --hard HEAD~1          # desfaz commit E descarta mudanças (PERIGO)
```

Regra de ouro: **`revert`** para desfazer em histórico já compartilhado;
`reset --hard` só em trabalho local não enviado (é destrutivo).

### A rede de segurança: reflog

```bash
git reflog                       # histórico de onde o HEAD esteve
```

Quase nada se perde de verdade no Git enquanto os commits existem — o `reflog`
costuma salvar você de um reset/rebase atrapalhado.

## .gitignore

Nunca versione segredos, dados pesados, artefatos e ambientes. Ver o
[.gitignore](../../.gitignore) deste repositório e
[security](../../26-security/04-secrets-management/README.md).

```gitignore
.env
*.parquet
.venv/
__pycache__/
```

## O especial do DE: dados e notebooks

- **Não versione dados** (grandes, mutáveis, possivelmente sensíveis). Para
  versionar *datasets*, use ferramentas específicas (ex.: DVC, lakeFS) ou controle
  por tabela/partição no lake/warehouse.
- **Notebooks** geram diffs ruins (JSON + saídas). Use `nbstripout` para limpar
  saídas antes do commit, ou prefira `.py` com *jupytext*.

## Erros comuns

- Comitar `.env`/credenciais (depois presentes **para sempre** no histórico —
  exige reescrita + rotação da credencial).
- `git add .` sem olhar → arquivos indesejados no commit.
- `reset --hard` sem entender que descarta trabalho.
- Commits gigantes misturando mudanças não relacionadas.

## Boas práticas

- Commits **pequenos e coerentes**, com mensagem clara (ver
  [conventional commits](../04-conventional-commits-versioning/README.md)).
- `git status`/`git diff` antes de todo commit.
- Puxe antes de empurrar (`git pull --rebase` mantém histórico linear).

## Relação com outros conceitos

- Habilita [branching](../02-branching-merging-rebasing/README.md) e
  [PRs](../03-pull-requests-code-review/README.md).
- Gatilho de [CI/CD](../../23-cicd-dataops/README.md).

## Exercícios

1. Inicialize um repositório, faça 3 commits usando `git add -p` e visualize o
   histórico com `--graph`.
2. "Acidentalmente" comite um arquivo `.env`; remova-o do staging antes do commit.
3. Faça um commit, perceba um erro na mensagem e corrija com `--amend`.
4. Simule um `reset --hard` indevido e recupere o commit usando `git reflog`.

## Referências

- Chacon, S.; Straub, B. *Pro Git* (git-scm.com/book) — caps. 1–3.
- Git Reference (git-scm.com/docs).
