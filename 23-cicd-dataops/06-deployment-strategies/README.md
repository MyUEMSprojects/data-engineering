# Estratégias de deploy

> 🟣 Production · Parte de [23 — CI/CD & DataOps](../README.md)

## O que é

Formas de **substituir uma versão em produção por outra** minimizando risco e downtime. A escolha
equilibra **velocidade, custo, segurança e facilidade de rollback** — e, em dados, precisa considerar que
**estado/dados persistem** além do código.

## As estratégias

### Recreate (parar e subir)

Para a versão antiga, depois sobe a nova. **Simples, com downtime.** Aceitável para jobs batch fora de
horário ou ambientes não críticos.

### Rolling update (gradual)

Substitui instâncias **aos poucos** (ex.: 1 de cada vez) mantendo parte do serviço no ar. Padrão do
[Kubernetes Deployment](../../21-kubernetes/02-pods-deployments/README.md) (`maxUnavailable`/`maxSurge`).
**Sem downtime**, baixo custo extra; durante a transição, **duas versões coexistem** (exige compatibilidade
entre versões). Rollback = rolling para a versão anterior.

### Blue/green

Dois ambientes completos: **blue** (atual) e **green** (nova). Valida-se o green e **troca-se o tráfego** de
uma vez (LB/DNS/alias). **Rollback instantâneo** (voltar ao blue). Custo: **dobro de infraestrutura**
durante a troca. Ótimo para mudanças arriscadas; atenção a **estado compartilhado** (banco) e migrações.

### Canary

Libera a nova versão para uma **pequena fração** do tráfego (1–5%), **monitora** métricas e vai aumentando
(25% → 50% → 100%) ou aborta. **Reduz o raio de explosão**; exige boa **observabilidade** e roteamento de
tráfego (service mesh/ingress/feature flags). Ideal para serving de modelos/APIs.

### Shadow / dark launch

A nova versão recebe **cópia do tráfego real** mas suas respostas **são descartadas**; compara-se com a
atual. Excelente para validar **modelos de ML** e **novos pipelines** sem impacto (ver [DE + ML](../../31-data-engineering-and-ml/README.md)).

### Feature flags

Desacoplam **deploy** de **release**: o código vai à produção desligado e é ativado gradualmente (por
usuário/percentual), com *kill switch* instantâneo.

## Comparação

| Estratégia | Downtime | Rollback | Custo extra | Risco | Bom para |
| --- | --- | --- | --- | --- | --- |
| Recreate | sim | redeploy | nenhum | alto | batch, dev |
| Rolling | não | rolling reverso | baixo | médio | serviços stateless |
| Blue/green | não | **instantâneo** | **2×** infra | baixo | mudanças arriscadas |
| Canary | não | rápido (reduz %) | baixo/médio | **muito baixo** | serving, APIs, ML |
| Shadow | não | n/a | médio | mínimo | validar sem impacto |

## Especificidades de **dados**

### Pipelines batch

Não há "tráfego" a dividir; as estratégias traduzem-se em:

- **Blue/green de tabelas/schemas**: construir a nova versão numa tabela/schema paralelo, **validar**
  (testes de dados, comparação com a versão atual) e **trocar atomicamente** (swap de view/alias/`ALTER
  TABLE RENAME`/pointer) — consumidores nunca veem estado parcial ([loading](../../09-etl-elt/04-loading/README.md),
  [dbt deploy](../../28-dbt/09-deployment/README.md)).
- **Execução em paralelo/shadow**: rodar a nova lógica ao lado da antiga e **reconciliar resultados**
  antes de cortar.
- **Rollout por partição/domínio**: aplicar a nova lógica a um subconjunto (ex.: um país/cliente) antes de
  generalizar.

### Mudanças de schema (expand/contract)

Para não quebrar consumidores ([schema evolution](../../08-data-formats/10-schema-evolution/README.md),
[contracts](../../29-data-contracts/README.md)):

```text
1. EXPAND:   adicionar nova coluna/tabela (compatível); escrever nos dois formatos
2. MIGRATE:  consumidores migram para o novo campo; backfill de histórico
3. CONTRACT: remover o campo antigo só quando ninguém mais o usa
```

### Dados não revertem sozinhos

Código tem rollback; **dados escritos, não**. Mitigue com **idempotência**, **time travel**/snapshots
([lakehouse](../../15-lakehouse/README.md)), **backups** ([DR](../../06-databases/09-backup-recovery-dr/README.md)),
**overwrite por partição** e [backfill](../../09-etl-elt/08-backfill/README.md) para corrigir. Frequentemente
**roll-forward** (corrigir e reprocessar) é mais seguro que "desfazer".

### Streaming

Atualizar jobs com estado exige **savepoints/checkpoints compatíveis** ([stateful](../../17-streaming/05-stateful-processing/README.md));
estratégia comum: subir a nova versão em paralelo (novo consumer group/checkpoint), validar e **cortar**
(blue/green de consumidores), com replay do log se necessário ([replay](../../18-message-brokers/05-ordering-retention-replay/README.md)).

### Infraestrutura

`terraform plan` revisado + aplicação gradual por ambiente/componente; `prevent_destroy` em recursos com
dados ([Terraform](../../22-infrastructure-as-code/02-terraform-basics/README.md)).

## Rollback: planeje antes de implantar

- Defina **critério de sucesso/falha** (métricas, testes de dados) e **gatilho de rollback** (manual/automático).
- Mantenha o **artefato anterior** disponível ([artefatos](../04-environments-artifacts/README.md)).
- Para mudanças de dados/schema, o rollback do código **não basta** — tenha plano de dados.
- Pratique rollback (game days); documente no runbook.

## Como escolher

```text
Job batch simples, janela livre           → recreate / deploy direto com testes
Serviço stateless (API, consumidor)       → rolling (+ canary se crítico)
Mudança de alto risco / precisa rollback instantâneo → blue/green
Serving de modelo / endpoint crítico      → canary (+ shadow antes)
Mudança de tabela/schema consumido por vários → blue/green de tabela + expand/contract
```

## Erros comuns

- Recreate em serviço crítico (downtime).
- Rolling sem compatibilidade entre versões coexistentes.
- Blue/green sem lidar com migrações/estado compartilhado.
- Canary sem observabilidade (não sabe se está ruim).
- Mudança de schema "big bang" quebrando consumidores.
- Plano de rollback que ignora os dados já escritos.

## Boas práticas

- Estratégia pelo risco/estado; deploys pequenos; critérios objetivos de sucesso/rollback.
- Swap atômico de tabelas; expand/contract; shadow para validar.
- Observabilidade e verificação pós-deploy; rollback/roll-forward ensaiados.

## Relação com outros conceitos

- [CD](../02-continuous-delivery/README.md), [Kubernetes deployments](../../21-kubernetes/02-pods-deployments/README.md),
  [dbt deployment](../../28-dbt/09-deployment/README.md), [schema evolution](../../08-data-formats/10-schema-evolution/README.md),
  [observability](../../24-observability/README.md).

## Exercícios

1. Escolha e justifique a estratégia para: API de serving de features; mudança numa tabela fato usada por 20
   dashboards; job batch noturno.
2. Descreva um blue/green de tabela com swap atômico e validação prévia.
3. Planeje um expand/contract para renomear uma coluna sem quebrar consumidores.
4. Defina critérios de sucesso e gatilho de rollback automático para um canary.

## Referências

- Humble & Farley, *Continuous Delivery*; Kubernetes Docs — Deployment strategies; Argo Rollouts/Flagger.
- Fowler, M. — BlueGreenDeployment, CanaryRelease, FeatureToggle.
