# Branching, merge e rebase

> 🟢 Foundations · Parte de [03 — Git & SWE](../README.md)

## O que é

**Branches** (ramos) permitem desenvolver mudanças em isolamento, sem afetar a
linha principal (`main`). **Merge** e **rebase** são as duas formas de trazer o
trabalho de uma branch para outra. Dominar isso é o que viabiliza colaboração e
[pull requests](../03-pull-requests-code-review/README.md).

## Branches: o conceito

Uma branch é apenas um **ponteiro móvel** para um commit. Criar uma branch é
barato (não copia arquivos). `HEAD` indica em qual branch você está.

```bash
git branch                       # lista branches
git switch -c feature/ingest     # cria e muda para a branch (Git 2.23+)
git switch main                  # volta para main
git branch -d feature/ingest     # apaga (após merge)
```

```text
main:     A───B───C
                   \
feature:            D───E   (feature aponta para E; main para C)
```

## Merge

Integra o histórico de uma branch em outra.

```bash
git switch main
git merge feature/ingest
```

Dois casos:

- **Fast-forward** — se `main` não avançou, o ponteiro só "anda para frente". Sem
  commit extra, histórico linear.
- **Merge commit** — se ambas avançaram, cria um commit de merge com **dois pais**,
  preservando a história exata.

```text
antes:  main A─B─C      feature C─D─E
merge:  main A─B─C───────M   (M tem pais C e E)
                 \      /
          feature D────E
```

## Rebase

"Reaplica" seus commits a partir de uma nova base, **reescrevendo** o histórico
para deixá-lo linear.

```bash
git switch feature/ingest
git rebase main          # move D,E para depois de C, como D',E'
```

```text
antes:   main A─B─C       feature (base B) B─D─E
rebase:  main A─B─C       feature         C─D'─E'  (linear, sem merge commit)
```

### Merge vs rebase — o trade-off

| | Merge | Rebase |
| --- | --- | --- |
| Histórico | Preserva a realidade (ramificado) | Linear, limpo |
| Commit extra | Sim (merge commit) | Não |
| Reescreve commits | Não | **Sim** (novos hashes) |
| Seguro em branch compartilhada | Sim | **Não** (ver regra de ouro) |

**Regra de ouro do rebase:** *nunca* faça rebase de commits que **já foram
enviados e outras pessoas podem ter baseado trabalho neles**. Reescrever histórico
público quebra o de todos. Rebase é para **limpar seu trabalho local** antes de
compartilhar.

Padrão comum e seguro: `git pull --rebase` para integrar mudanças remotas sem
criar merge commits triviais na sua branch.

## Rebase interativo (limpar antes do PR)

```bash
git rebase -i main
```

Permite **squash** (juntar), reordenar, editar e reescrever mensagens de commits
locais — para apresentar um histórico limpo no PR. (Em sessões automatizadas o
modo interativo não está disponível, mas conheça o conceito.)

## Resolvendo conflitos

Ocorrem quando duas branches mudam as mesmas linhas.

```text
<<<<<<< HEAD
versão da branch atual
=======
versão da outra branch
>>>>>>> feature/ingest
```

Fluxo:

```bash
# edite os arquivos, escolhendo/combinando as versões e removendo os marcadores
git add arquivo_resolvido
git merge --continue     # ou  git rebase --continue
git merge --abort        # desiste e volta ao estado anterior (se precisar)
```

Dicas: resolva conflitos cedo (branches curtas conflitam menos); use uma
ferramenta de merge (`git mergetool`, VS Code).

## Estratégias de branching

- **GitHub Flow** (recomendado para a maioria/DE): `main` sempre deployável;
  cada mudança em uma branch curta → PR → merge. Simples, combina com CI/CD.
- **Git Flow**: branches `develop`, `release/*`, `hotfix/*`. Mais cerimônia; útil
  em releases versionadas, exagero para muitos times de dados.
- **Trunk-based**: commits frequentes direto na `main` (com *feature flags*).
  Exige forte automação de testes.

Para pipelines de dados, **GitHub Flow + ambientes (dev/staging/prod)** é o mais
comum. Ver [deployment strategies](../../23-cicd-dataops/06-deployment-strategies/README.md).

## Erros comuns

- Rebase de branch compartilhada → quebra o histórico dos colegas.
- Branches de vida longa → conflitos gigantes ("merge hell").
- Resolver conflito apagando o trabalho do outro sem entender.
- Commitar em `main` direto sem revisão em projeto colaborativo.

## Boas práticas

- Branches **curtas e focadas**; integre rápido.
- Nomeie com prefixo: `feature/`, `fix/`, `docs/`, `chore/`.
- Rebase local para limpar; merge (via PR) para integrar.
- `main` sempre verde (passa no [CI](../../23-cicd-dataops/README.md)).

## Relação com outros conceitos

- Base de [pull requests](../03-pull-requests-code-review/README.md).
- Conecta a [ambientes/deploy](../../23-cicd-dataops/06-deployment-strategies/README.md).

## Exercícios

1. Crie duas branches que editam a mesma linha, faça merge e resolva o conflito.
2. Repita com rebase em vez de merge e compare os históricos (`--graph`).
3. Explique, com um exemplo, por que rebase de uma branch já compartilhada é
   perigoso.
4. Use `git rebase -i` (conceitualmente) para descrever como juntaria 3 commits
   "wip" em 1.

## Referências

- Chacon, S.; Straub, B. *Pro Git* — cap. 3 (branching) e 3.6 (rebasing).
- GitHub Flow (docs.github.com). Atlassian Git tutorials.
