# 02 — Linux, Shell e Ambiente

> 🟢 Nível 1 — Foundations · Pré: [01 — Fundamentos](../01-foundations/README.md) ·
> Próximo: [03 — Git & SWE](../03-git-software-engineering/README.md)

Praticamente toda plataforma de dados roda em **Linux**: servidores, containers,
clusters Spark, nós Kafka, máquinas de orquestração. O terminal é a interface de
trabalho do Data Engineer. Este módulo dá a fluência mínima para navegar, manipular
arquivos de dados, automatizar tarefas e **investigar problemas em produção** — a
habilidade que mais separa quem resolve incidentes de quem fica travado.

## Por que isso é fundacional

- Containers e cloud assumem familiaridade com Linux.
- Grande parte de *troubleshooting* de pipelines é olhar **logs** e processos no
  shell.
- Ferramentas de texto (`grep`/`sed`/`awk`) resolvem em segundos tarefas de
  inspeção de dados que, de outra forma, exigiriam escrever código.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Linux básico](01-linux-basics/README.md) | Shell, navegação, comandos essenciais |
| 02 | [Filesystem](02-filesystem/README.md) | Hierarquia, caminhos, links, montagem |
| 03 | [Processos e permissões](03-processes-and-permissions/README.md) | Processos, sinais, usuários, permissões |
| 04 | [Processamento de texto](04-text-processing/README.md) | pipes, redirecionamento, grep, sed, awk, find, xargs |
| 05 | [Shell scripting](05-shell-scripting/README.md) | Scripts Bash robustos para automação |
| 06 | [Cron](06-cron/README.md) | Agendamento de tarefas |
| 07 | [SSH](07-ssh/README.md) | Acesso remoto, chaves, túneis, scp |
| 08 | [Logs e troubleshooting](08-logs-and-troubleshooting/README.md) | Investigar sistemas e pipelines |

## Dependências internas

```text
Linux básico ─► Filesystem ─► Processos & permissões
                    │
                    ▼
        Processamento de texto ─► Shell scripting ─► Cron
                                        │
                                        ▼
                               SSH ─► Logs & troubleshooting
```

## Checkpoint

- [ ] Navegar, inspecionar e manipular arquivos pelo terminal com confiança.
- [ ] Explicar permissões (`rwx`, octal) e corrigir um "Permission denied".
- [ ] Encadear `grep`/`sed`/`awk`/`sort`/`uniq` para inspecionar um CSV grande.
- [ ] Escrever um script Bash robusto (`set -euo pipefail`, argumentos, logging).
- [ ] Agendar uma tarefa no `cron` e saber onde caem os logs dela.
- [ ] Acessar um host por SSH com chave e copiar arquivos com `scp`/`rsync`.
- [ ] Diante de um job travado, usar `ps`/`top`/`df`/`journalctl` para investigar.

## Referências do módulo

- *The Linux Command Line*, William Shotts (gratuito em linuxcommand.org).
- *Linux Pocket Guide*, Daniel Barrett. O'Reilly.
- `man` pages (sempre a referência primária) e `tldr`/`explainshell.com`.
