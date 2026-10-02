# Conventional Commits e versionamento

> 🟢 Foundations · Parte de [03 — Git & SWE](../README.md)

## O que é

**Conventional Commits** é uma convenção para escrever mensagens de commit
padronizadas e legíveis por máquina. **Versionamento semântico (SemVer)** é um
esquema para numerar releases de forma significativa. Juntos, permitem histórico
limpo, *changelogs* automáticos e releases previsíveis.

## Por que existe

Mensagens de commit vagas ("fix", "update", "wip") tornam o histórico inútil.
Padronizá-las deixa claro **o que** mudou e **com que impacto**, viabiliza
automação (gerar changelog, decidir a próxima versão) e melhora a colaboração.

## Conventional Commits — formato

```text
<tipo>(<escopo opcional>): <descrição curta no imperativo>

<corpo opcional: o quê e por quê>

<rodapé opcional: BREAKING CHANGE, refs de issues>
```

Exemplos:

```text
feat(etl): adiciona carga incremental na tabela de pedidos
fix(airflow): corrige fuso horário do schedule do DAG de vendas
docs(sql): revisa seção de window functions
refactor(spark): extrai lógica de dedupe para função reutilizável
test(quality): adiciona testes de unicidade na dimensão cliente
chore(deps): atualiza pandas para 2.2
ci: adiciona verificação de links em Markdown
```

### Tipos comuns

| Tipo | Uso |
| --- | --- |
| `feat` | nova funcionalidade |
| `fix` | correção de bug |
| `docs` | documentação |
| `refactor` | mudança sem alterar comportamento |
| `test` | testes |
| `perf` | melhoria de performance |
| `chore` | manutenção (deps, configs) |
| `ci` | pipeline de CI/CD |
| `build` | build/empacotamento |

### Breaking changes

Sinalize mudanças incompatíveis com `!` ou com rodapé `BREAKING CHANGE:` — elas
disparam uma major no SemVer:

```text
feat(api)!: muda formato do payload de eventos

BREAKING CHANGE: o campo `ts` agora é epoch em ms, não ISO-8601.
```

Em dados, uma *breaking change* típica é **mudar o schema de uma tabela/contrato**
que consumidores dependem — ver [data contracts](../../29-data-contracts/README.md).

## Boas mensagens: regras práticas

- Assunto no **imperativo** ("adiciona", não "adicionado"/"adicionando").
- ≤ ~50 caracteres no assunto; corpo explicando o **porquê** (o *o quê* o diff já
  mostra).
- Um commit = uma mudança lógica.

## SemVer (Semantic Versioning)

Formato `MAJOR.MINOR.PATCH` (ex.: `2.4.1`):

- **MAJOR** — mudanças incompatíveis (quebra quem usa).
- **MINOR** — nova funcionalidade retrocompatível.
- **PATCH** — correção retrocompatível.

Pré-releases e metadados: `2.5.0-rc.1`, `1.0.0+build.5`.

Mapeamento com Conventional Commits (base de *semantic-release*):

| Commit | Incremento |
| --- | --- |
| `fix:` | PATCH |
| `feat:` | MINOR |
| `BREAKING CHANGE` / `!` | MAJOR |

## Tags e releases no Git

```bash
git tag -a v1.2.0 -m "release 1.2.0"   # tag anotada
git push origin v1.2.0                  # envia a tag
git tag                                 # lista
```

Tags marcam pontos de release no histórico; *releases* (GitHub) agregam tag +
changelog + artefatos.

## Versionando o que é de dados

Além do código, pense em versionar:

- **Schemas/contratos** — versionados e com política de compatibilidade (ver
  [schema evolution](../../08-data-formats/10-schema-evolution/README.md) e
  [data contracts](../../29-data-contracts/README.md)).
- **Modelos dbt** — versionados em Git como qualquer código.
- **Dados/*datasets*** — por ferramentas próprias (DVC, lakeFS) ou por
  tabela/partição em [lakehouse](../../15-lakehouse/README.md) (time travel).
- **Pipelines/infra** — Git + [IaC](../../22-infrastructure-as-code/README.md).

## Automação

- **commitlint** — valida mensagens no CI/pre-commit.
- **semantic-release / release-please** — decidem a versão, geram changelog e a
  tag a partir dos commits.
- **pre-commit** — hook que checa o formato antes do commit (ver
  [lint & formatação](../06-linting-formatting/README.md)).

## Erros comuns

- Mensagens vagas ("update", "fix bug").
- Misturar várias mudanças em um commit.
- Bumpar major por engano (ou nunca sinalizar breaking changes).
- Esquecer que mudar um schema de tabela **é** uma breaking change para quem
  consome.

## Boas práticas

- Padronize o time em Conventional Commits desde o início.
- Automatize versionamento e changelog.
- Trate contratos de dados com disciplina de SemVer.

## Relação com outros conceitos

- Melhora [PRs](../03-pull-requests-code-review/README.md) e habilita
  [CI/CD](../../23-cicd-dataops/README.md).
- Conecta a [data contracts](../../29-data-contracts/README.md) e
  [schema evolution](../../08-data-formats/10-schema-evolution/README.md).

## Exercícios

1. Reescreva estas mensagens no padrão: "fixed stuff", "update dag", "new table".
2. Classifique como MAJOR/MINOR/PATCH: (a) adicionar coluna opcional a uma tabela;
   (b) renomear uma coluna existente; (c) corrigir um cálculo sem mudar o schema.
3. Escreva um commit com `BREAKING CHANGE` para a remoção de uma coluna.
4. Descreva como *semantic-release* decidiria a próxima versão a partir dos commits
   desde a última tag.

## Referências

- Conventional Commits 1.0.0 (conventionalcommits.org).
- Semantic Versioning 2.0.0 (semver.org).
- semantic-release / release-please (docs oficiais).
