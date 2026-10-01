# Exercícios — Módulo 03: Git e engenharia de software

Teoria em [03-git-software-engineering](../../03-git-software-engineering/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Implementação — Desfazer sem perder

Você fez `git commit` com a mensagem errada (ainda **não** enviou). E depois commitou um arquivo de senha por engano (também não enviou). Como corrigir cada caso?

<details><summary>Gabarito</summary>

Mensagem: `git commit --amend -m "mensagem correta"`. Arquivo indevido: `git reset --soft HEAD~1` → `git restore --staged senha.env` → recommitar o resto (e **adicionar ao `.gitignore`**).
Se **já tivesse enviado**, o segredo está comprometido: **rotacione a credencial** (reescrever histórico não basta).
</details>

## 2. 🟢 Conceitual — Merge × rebase

Quando usar `merge` e quando `rebase`? Qual a regra de ouro do rebase?

<details><summary>Gabarito</summary>

`merge` preserva o histórico real (commit de merge) — bom para integrar à `main`. `rebase` reescreve commits sobre outra base, deixando o histórico **linear** — bom para atualizar **sua** branch local.
**Regra de ouro:** nunca faça rebase de commits **já publicados/compartilhados**. Ver [branching](../../03-git-software-engineering/02-branching-merging-rebasing/README.md).
</details>

## 3. 🔵 Implementação — Conventional Commits e versão

Dadas as mensagens: `fix(api): trata timeout`, `feat(etl): adiciona carga incremental`, `feat!: remove coluna legacy_id`, `docs: atualiza README`. Qual será o próximo **bump semântico** a partir de `1.4.2` e por quê?

<details><summary>Gabarito</summary>

`feat!:` (ou `BREAKING CHANGE:`) é incompatível ⇒ **major**: `2.0.0`. Sem o breaking change, `feat` daria minor (`1.5.0`) e `fix` patch. `docs` não altera versão. Ver [commits convencionais](../../03-git-software-engineering/04-conventional-commits-versioning/README.md).
</details>

## 4. 🔵 Debugging — Conflito de merge

Ao dar `git merge feature/novo-schema` aparece:
```
<<<<<<< HEAD
amount NUMERIC(12,2) NOT NULL,
=======
amount NUMERIC(14,4) NOT NULL,
>>>>>>> feature/novo-schema
```
Como decidir a resolução e **garantir** que o resultado não quebra o pipeline?

<details><summary>Gabarito</summary>

Não escolha "no escuro": entenda a **intenção** de cada lado (`git log -p` nos dois), converse com o autor e decida o tipo correto (aqui, precisão monetária). Depois: remova os marcadores, `git add`, **rode os testes/migrações** e só então `git commit`.
Prevenção: PRs pequenos, integração frequente, e testes de schema no CI. Ver [pull requests](../../03-git-software-engineering/03-pull-requests-code-review/README.md).
</details>

## 5. 🟣 Arquitetura — Organizar um repositório de dados

Proponha a estrutura de pastas de um repositório com: pipelines Python, modelos dbt, DAGs do Airflow, IaC e testes. Justifique **mono-repo × multi-repo** para um time de 8 pessoas.

<details><summary>Gabarito (um caminho)</summary>

```text
repo/
├── pipelines/      # pacote Python (src/), testes ao lado
├── dbt/            # models/, tests/, macros/
├── dags/           # só orquestra; lógica fica em pipelines/
├── infra/          # Terraform
├── tests/          # integração
└── .github/workflows/
```
**Mono-repo** para 8 pessoas: mudanças atômicas (código + modelo + DAG no mesmo PR), CI único, menos coordenação de versões. Multi-repo vale com times autônomos, ciclos de release distintos ou requisitos de acesso diferentes. Ver [organização de projetos](../../03-git-software-engineering/07-project-organization/README.md).
</details>

## 6. 🟣 Implementação — Teste que protege a transformação

Escreva um teste `pytest` para `def dedupe(rows)` que mantém **a linha mais recente por `id`** (campo `updated_at`). Inclua o caso de empate e a **idempotência** (`dedupe(dedupe(x)) == dedupe(x)`).

<details><summary>Gabarito</summary>

```python
def dedupe(rows):
    best = {}
    for i, r in enumerate(rows):
        k = r["id"]
        if k not in best or (r["updated_at"], i) > (best[k][1]["updated_at"], best[k][0]):
            best[k] = (i, r)
    return [v[1] for v in sorted(best.values(), key=lambda x: x[0])]

def test_dedupe_keeps_latest_and_is_idempotent():
    rows = [
        {"id": 1, "updated_at": 1, "v": "a"},
        {"id": 1, "updated_at": 3, "v": "c"},
        {"id": 1, "updated_at": 2, "v": "b"},
        {"id": 2, "updated_at": 1, "v": "x"},
        {"id": 2, "updated_at": 1, "v": "y"},   # empate: vence o que chegou depois
    ]
    out = dedupe(rows)
    assert {r["id"]: r["v"] for r in out} == {1: "c", 2: "y"}
    assert dedupe(out) == out
```
Ver [testes](../../03-git-software-engineering/05-testing/README.md).
</details>
