# Pull requests e code review

> 🟢 Foundations · Parte de [03 — Git & SWE](../README.md)

## O que é

Um **Pull Request (PR)** (ou *Merge Request*) é uma proposta de integrar as
mudanças de uma branch na principal, acompanhada de discussão, **revisão de
código** e verificações automáticas ([CI](../../23-cicd-dataops/README.md)). É o
mecanismo central de colaboração e controle de qualidade em times modernos.

## Por que existe / que problema resolve

- **Qualidade:** outra pessoa (ou o CI) pega bugs antes de chegarem à `main`.
- **Compartilhamento de conhecimento:** o time aprende as mudanças.
- **Auditoria:** fica registrado o quê, por quê e quem aprovou — importante em
  dados (mudanças podem afetar relatórios e compliance).
- **Gate de automação:** testes, lint e checagem de links rodam antes do merge.

## O fluxo

```text
1. branch curta ──► 2. commits ──► 3. push ──► 4. abre PR
        ▲                                           │
        │                                           ▼
8. merge ◄── 7. CI verde ◄── 6. ajustes ◄── 5. review + comentários
```

```bash
git switch -c feature/scd2-clientes
# ... trabalho, commits ...
git push -u origin feature/scd2-clientes
# abra o PR na interface (ou: gh pr create)
```

## Como escrever um bom PR

- **Pequeno e focado.** PRs grandes recebem revisões rasas. Prefira <~400 linhas.
- **Título claro** (siga [conventional commits](../04-conventional-commits-versioning/README.md)):
  `feat(etl): adiciona SCD2 na dimensão de clientes`.
- **Descrição que responde:** o que muda, por quê, como testar, riscos/impacto.
  Para dados: *quais tabelas/relatórios são afetados?* É preciso *backfill*?
- **Contexto visual:** antes/depois, amostra de dados, plano de query, prints.
- **Checklist** (ver o [template de PR](../../.github/pull_request_template.md)).

## Como revisar código (bem)

Objetivo: melhorar o código e proteger o sistema — não "ganhar" a discussão.

Procure por:

1. **Correção** — faz o que diz? Casos de borda, nulos, fuso horário, duplicatas?
2. **Idempotência/efeitos em dados** — rerodar duplica? sobrescreve? precisa de
   *backfill*? (ver [ETL](../../09-etl-elt/07-idempotency-retries/README.md)).
3. **Testes** — há testes? cobrem o risco? ([testes](../05-testing/README.md)).
4. **Legibilidade e manutenção** — nomes, estrutura, complexidade.
5. **Performance/custo** — a query varre a tabela toda? faz *shuffle* desnecessário?
6. **Segurança** — segredos, PII, permissões (ver [security](../../26-security/README.md)).

### Etiqueta de revisão

- Comente o **código**, não a pessoa. "Essa função pode duplicar linhas se rodar
  2x" > "você errou".
- Distinga **bloqueante** de **sugestão/nit** ("nit:" para coisas menores).
- Explique o *porquê* e, quando possível, proponha a alternativa.
- Elogie boas soluções. Aprove quando estiver bom "o suficiente" — não busque a
  perfeição.

## Verificações automáticas (CI no PR)

Um PR deve rodar automaticamente: lint ([ruff/black](../06-linting-formatting/README.md)),
testes ([pytest](../05-testing/README.md)), checagem de links/Markdown e, em
projetos de dados, testes de dados (ex.: [dbt tests](../../28-dbt/README.md),
[Great Expectations](../../12-data-quality/05-great-expectations/README.md)). Só
mergeia com tudo verde. Ver [CI/CD](../../23-cicd-dataops/README.md).

## Proteção de branch

Configure a `main` para exigir: PR (sem push direto), ≥1 aprovação, CI passando e,
opcionalmente, *up-to-date* com a base. Isso codifica "a main sempre funciona".

## Opções de merge

- **Merge commit** — preserva todos os commits e a ramificação.
- **Squash and merge** — junta tudo em 1 commit (histórico de `main` limpo, 1
  commit por PR). **Popular e recomendado** para a maioria dos times.
- **Rebase and merge** — reaplica os commits linearmente, sem merge commit.

## O ângulo de Data Engineering

Revisar mudanças de dados exige cuidado extra: uma alteração "pequena" em uma
transformação pode mudar números em dashboards usados para decisões. Boas práticas:
revisar o **plano de execução**, exigir **testes de dados**, validar em
**staging** com dados reais/amostrados, e planejar **backfill** quando a lógica
histórica muda.

## Erros comuns

- PRs enormes e genéricos ("várias coisas").
- Descrição vazia ("fix stuff").
- Aprovar sem ler (*rubber stamp*).
- Ignorar o impacto em tabelas/relatórios a jusante.
- Discussões improdutivas sobre estilo (resolva com [formatador automático](../06-linting-formatting/README.md)).

## Boas práticas

- Um PR = uma mudança lógica.
- Autodescreva o PR; rode o CI antes de pedir review.
- Como revisor, responda rápido (PRs parados bloqueiam o time).
- Automatize o que for mecânico (estilo, lint) para o review focar em lógica.

## Relação com outros conceitos

- Usa [branching](../02-branching-merging-rebasing/README.md) e
  [conventional commits](../04-conventional-commits-versioning/README.md).
- É o gate de [CI/CD & DataOps](../../23-cicd-dataops/README.md).

## Exercícios

1. Abra um PR (pode ser num repo seu) com título convencional e descrição
   completa (o quê/por quê/como testar).
2. Faça uma autorrevisão: liste 3 problemas que você mesmo pegaria.
3. Dado um PR que altera uma transformação de faturamento, escreva 5 perguntas de
   revisão específicas de dados.
4. Configure proteção de branch exigindo CI + 1 aprovação (conceitual ou real).

## Referências

- GitHub Docs — About pull requests, branch protection.
- Google *Code Review Developer Guide* (eng-practices).
