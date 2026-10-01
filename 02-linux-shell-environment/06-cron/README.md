# Cron

> 🟢 Foundations · Parte de [02 — Linux & Shell](../README.md)

## O que é

`cron` é o agendador de tarefas do Linux. Ele executa comandos em horários
recorrentes definidos em uma tabela (**crontab**). É a forma mais simples de
**agendar** um pipeline batch (ex.: "rodar a ingestão todo dia às 2h").

## Por que importa (e seus limites)

Cron é o "avô" dos [orquestradores](../../11-orchestration/README.md). Entendê-lo
mostra o problema que Airflow/Dagster resolvem: cron **agenda**, mas não gerencia
**dependências entre tarefas**, **retries**, **backfill**, **observabilidade** ou
**estado**. Para pipelines reais com várias etapas, use um orquestrador; cron
serve para tarefas simples e isoladas.

## Sintaxe do crontab

```text
┌───────── minuto (0–59)
│ ┌─────── hora (0–23)
│ │ ┌───── dia do mês (1–31)
│ │ │ ┌─── mês (1–12)
│ │ │ │ ┌─ dia da semana (0–7; 0 e 7 = domingo)
│ │ │ │ │
* * * * *  comando a executar
```

Exemplos:

```cron
0 2 * * *      /opt/pipelines/ingest.sh          # todo dia às 02:00
*/15 * * * *   /opt/pipelines/check.sh           # a cada 15 min
0 */4 * * *    /opt/pipelines/sync.sh            # a cada 4 horas
0 9 * * 1-5    /opt/reports/daily.sh             # 09:00 em dias úteis
0 0 1 * *      /opt/pipelines/monthly.sh         # 1º dia do mês à meia-noite
@reboot        /opt/start_services.sh            # ao iniciar a máquina
```

Use [crontab.guru](https://crontab.guru) para ler/escrever expressões.

## Gerenciando o crontab

```bash
crontab -e           # editar o crontab do usuário atual
crontab -l           # listar
crontab -r           # remover (cuidado!)
sudo crontab -u user -e   # editar o de outro usuário
```

Também há `/etc/crontab` e `/etc/cron.d/` (nível de sistema, com campo de usuário)
e diretórios `/etc/cron.{daily,hourly,...}`.

## Os erros clássicos de cron (e como evitá-los)

Cron roda em um ambiente **mínimo**: `PATH` curto, sem suas variáveis de ambiente,
*working directory* = home. Quase todo "funciona no terminal mas não no cron" vem
disso.

1. **PATH diferente** → use caminhos absolutos para tudo (`/usr/bin/python3`, não
   `python3`).
2. **Variáveis de ambiente ausentes** → defina-as no topo do crontab ou carregue
   um arquivo de ambiente no início do script.
3. **Working directory errado** → `cd` explícito ou caminhos absolutos.
4. **Saída perdida** → cron **manda stdout/stderr por e-mail local**, que você
   quase nunca lê. **Sempre redirecione para um log.**

Template seguro de linha de crontab:

```cron
PATH=/usr/local/bin:/usr/bin:/bin
0 2 * * * /opt/pipelines/ingest.sh >> /var/log/ingest.log 2>&1
```

E dentro do script, mantenha `set -euo pipefail` e caminhos absolutos (ver
[shell scripting](../05-shell-scripting/README.md)).

## Logs e monitoramento

```bash
grep CRON /var/log/syslog         # Debian/Ubuntu: execuções do cron
journalctl -u cron                # systemd
tail -f /var/log/ingest.log       # o log do SEU job (o que importa)
```

Como cron não alerta em falhas, adicione você mesmo: envie o status a um canal, um
*healthcheck* (ex.: "dead man's switch" tipo Healthchecks.io), ou grave um
arquivo de "última execução bem-sucedida" que outra verificação monitore.

## Concorrência: evitar sobreposição

Se um job pode demorar mais que o intervalo, duas execuções podem se sobrepor. Use
`flock` para garantir exclusão mútua:

```cron
*/5 * * * * /usr/bin/flock -n /tmp/sync.lock /opt/pipelines/sync.sh
```

`-n` faz desistir se já houver uma execução rodando.

## Alternativas ao cron

- **systemd timers** — mais poderosos (dependências, logging via journald,
  `OnCalendar`), padrão em distros modernas.
- **[Orquestradores](../../11-orchestration/README.md)** (Airflow, Dagster,
  Prefect) — para pipelines com dependências, retries e observabilidade.
- **CronJobs do [Kubernetes](../../21-kubernetes/04-jobs-cronjobs/README.md)** —
  cron em cluster.

## Quando usar / quando NÃO usar

- **Use** para tarefas simples, isoladas, em uma máquina (um backup, um script de
  limpeza, um sync pequeno).
- **NÃO use** para pipelines multi-etapa com dependências, SLAs, retries e
  necessidade de *backfill* — isso é trabalho de orquestrador.

## Erros comuns

- Supor o mesmo ambiente do terminal interativo.
- Não redirecionar a saída → falhas invisíveis.
- Jobs se sobrepondo sem `flock`.
- Usar cron para o que deveria ser um orquestrador.

## Relação com outros conceitos

- Evolui para [orquestração](../../11-orchestration/README.md) e
  [scheduling de pipelines](../../10-data-pipelines/03-scheduling/README.md).
- Depende de [shell scripting](../05-shell-scripting/README.md) robusto.

## Exercícios

1. Escreva a expressão cron para "a cada 10 minutos, de segunda a sexta, das 8h
   às 18h".
2. Um job "funciona no terminal mas não no cron". Liste 3 causas prováveis e como
   corrigir cada uma.
3. Adicione `flock` e redirecionamento de log a uma linha de crontab.
4. Explique por que você migraria um pipeline de 4 etapas de cron para Airflow.

## Referências

- `man 5 crontab`, `man cron`, `man flock`.
- crontab.guru. Documentação de systemd timers.
