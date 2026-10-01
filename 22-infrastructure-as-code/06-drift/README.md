# Drift

> 🟣 Cloud & Infra · Parte de [22 — IaC](../README.md)

## O que é

**Drift** (desvio) é a divergência entre o **estado declarado no código/state** e o **estado real** da
infraestrutura. Ocorre quando algo é alterado **fora** do fluxo de IaC (console, CLI, outro processo,
autoscaling, incidente), deixando o código "mentindo" sobre a realidade.

```text
código/state: bucket com versioning=Enabled, tag ambiente=prod
realidade:    alguém desligou o versioning no console  → DRIFT
```

## Por que importa

- **Segurança** — uma regra de firewall/IAM aberta "só pra testar" fica esquecida (vulnerabilidade).
- **Confiabilidade/reprodutibilidade** — recriar o ambiente do código **não** reproduz o que roda hoje.
- **Surpresas no `apply`** — o Terraform pode **reverter** mudanças manuais (inclusive correções
  emergenciais úteis) ou propor destruir/recriar recursos.
- **Auditoria/compliance** — a infra real não bate com o que foi aprovado ([governança](../../25-data-governance/README.md)).

## Causas comuns

- **Mudanças manuais** no console/CLI ("hotfix" em incidente).
- **Outros processos** modificando os mesmos recursos (scripts, outra ferramenta, autoscaling, o próprio
  provedor).
- **Atributos computados** que mudam sozinhos (ex.: tags/IDs adicionados pelo serviço).
- **Recursos criados fora** e nunca importados.
- **State desatualizado** ou perdido ([state](../03-state/README.md)).

## Detectando drift

- **`terraform plan`** — compara código, state e **realidade (refresh)**; diffs inesperados indicam drift.
- **`terraform plan -refresh-only`** — mostra **apenas** divergências entre state e realidade (sem
  propor mudar o código).
- **Detecção agendada** — job de CI/cron que roda `plan` periodicamente (ex.: toda noite) e **alerta** se
  houver diferença (`-detailed-exitcode`: código 2 = há mudanças).
- **Ferramentas**: Terraform Cloud drift detection, driftctl/Snyk IaC, AWS Config / GCP Asset Inventory /
  Azure Policy (detectam recursos fora do padrão), `cloudquery`.

```bash
terraform plan -detailed-exitcode   # 0 = sem mudanças; 2 = há diferenças (drift ou mudança de código)
terraform plan -refresh-only
```

## Corrigindo drift (duas direções)

1. **Reverter a realidade ao código** — `terraform apply` reaplica o estado declarado (o código vence).
   Use quando a mudança manual foi indevida.
2. **Atualizar o código à realidade** — se a mudança manual era legítima, **incorpore-a no código** (PR) e
   `apply -refresh-only` para sincronizar o state; assim a verdade volta a estar no repositório.
3. **Recursos criados fora** — `terraform import` + declarar no código.
4. **Atributos que mudam legitimamente** — `lifecycle { ignore_changes = [...] }` (com parcimônia).

> Decisão consciente: **qual é a fonte da verdade?** O padrão saudável é: **o código**. Mudanças
> emergenciais manuais devem ser **registradas no código logo depois**.

## Prevenindo drift

- **Cultura/processo**: toda mudança por PR; proibir/limitar acesso de escrita manual a produção.
- **Permissões**: IAM de **somente leitura** para humanos em prod; escrita só via pipeline/role de CI
  ([IAM](../../19-cloud/06-iam-secrets/README.md)).
- **Policy-as-code** (OPA, Sentinel, Checkov, AWS Config rules) bloqueia/alerta configurações fora do
  padrão.
- **GitOps** (Argo CD/Flux) reconcilia continuamente o cluster ao Git (auto-heal).
- **Break-glass** documentado para emergências (com reconciliação posterior).
- **Detecção agendada** + alertas; revisão dos diffs.

## Drift também em dados

O conceito se estende: **schema drift** (a fonte mudou o schema — [schema validation](../../12-data-quality/03-schema-validation/README.md),
[schema evolution](../../08-data-formats/10-schema-evolution/README.md)), **data drift/feature drift** em ML
([DE + ML](../../31-data-engineering-and-ml/README.md)), e tabelas/permissões do warehouse alteradas
manualmente fora do dbt/IaC. Mesma lição: **fonte da verdade declarada + detecção contínua**.

## Erros comuns

- Corrigir incidentes no console e nunca refletir no código.
- Ignorar `plan` com diffs "esquisitos" e aplicar cegamente (reverte correções ou destrói recursos).
- Humanos com escrita ampla em prod.
- Sem detecção periódica → drift acumulado descoberto só no desastre.
- Abusar de `ignore_changes` mascarando problemas.

## Boas práticas

- Código como fonte da verdade; mudanças só por PR/pipeline; acesso manual restrito.
- Detecção agendada de drift com alertas; policy-as-code.
- Após mudança emergencial: PR para sincronizar o código.
- Use `ignore_changes` apenas para atributos legitimamente gerenciados por terceiros.

## Relação com outros conceitos

- [State](../03-state/README.md), [Terraform](../02-terraform-basics/README.md),
  [CI/CD](../../23-cicd-dataops/README.md), [governança](../../25-data-governance/README.md),
  [schema drift](../../12-data-quality/03-schema-validation/README.md).

## Exercícios

1. Provoque drift (altere uma tag no console) e detecte-o com `plan -refresh-only`.
2. Configure (conceitualmente) um job noturno que roda `plan -detailed-exitcode` e alerta no código 2.
3. Decida, em 3 cenários, se reverte a realidade ao código ou atualiza o código à realidade.
4. Liste 4 controles que previnem drift em produção.

## Referências

- Terraform Docs — `plan -refresh-only`, `-detailed-exitcode`, lifecycle `ignore_changes`.
- Documentação de Argo CD/Flux (GitOps), AWS Config, driftctl; Morris, K. *Infrastructure as Code*.
