# Exercícios — Módulo 02: Linux, shell e ambiente

Teoria em [02-linux-shell-environment](../../02-linux-shell-environment/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Implementação — Contar erros por serviço

O arquivo `app.log` tem linhas como `2024-03-01T10:00:01Z ERROR payments timeout`. Com **uma linha de shell**, conte as linhas `ERROR` por serviço (3º campo), em ordem decrescente.

<details><summary>Gabarito</summary>

```bash
grep ' ERROR ' app.log | awk '{print $3}' | sort | uniq -c | sort -rn
```
`sort` antes de `uniq -c` é **obrigatório** (`uniq` só junta linhas adjacentes). Variante em um só `awk`: `awk '$2=="ERROR"{c[$3]++} END{for(k in c) print c[k], k}' app.log | sort -rn`.
</details>

## 2. 🟢 Conceitual — Permissões

O que significa `-rwxr-x---` num arquivo `etl.sh` de dono `ana` e grupo `data`? Como permitir que **só o grupo** o execute sem poder editá-lo?

<details><summary>Gabarito</summary>

Dono: ler/escrever/executar (`rwx`); grupo: ler/executar (`r-x`); outros: nada. O grupo **já** executa sem editar. Para tirar a escrita do dono também: `chmod 550 etl.sh` (ou `chmod u-w etl.sh`).
Octal: `750` = `rwxr-x---`. Ver [processos e permissões](../../02-linux-shell-environment/03-processes-and-permissions/README.md).
</details>

## 3. 🔵 Debugging — O script que "funciona na minha máquina"

```bash
#!/bin/bash
for f in $(ls /data/in/*.csv); do
  rows=$(wc -l < $f)
  echo "$f: $rows" >> /tmp/report.txt
done
```
Aponte **quatro** problemas e reescreva de forma robusta.

<details><summary>Gabarito</summary>

Problemas: (1) `for f in $(ls ...)` quebra com **espaços** nos nomes; (2) `$f` sem aspas; (3) sem `set -euo pipefail` — falhas silenciosas; (4) se não houver `.csv`, o glob literal vira o "arquivo"; (5) `>>` acumula em execuções repetidas (não idempotente).
```bash
#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob
out=/tmp/report.txt; : > "$out"
for f in /data/in/*.csv; do
  printf '%s: %s\n' "$f" "$(wc -l < "$f")" >> "$out"
done
```
Ver [shell scripting](../../02-linux-shell-environment/05-shell-scripting/README.md).
</details>

## 4. 🔵 Implementação — Agendamento com cron

Escreva as entradas de `crontab` para: (a) rodar `/opt/etl/run.sh` **todo dia às 02:30**; (b) **a cada 15 minutos** em dias úteis das 8h às 18h; (c) o 1º dia de cada mês às 03:00. Qual o risco de usar `cron` para pipelines com dependências?

<details><summary>Gabarito</summary>

```cron
30 2 * * *       /opt/etl/run.sh
*/15 8-18 * * 1-5 /opt/etl/run.sh
0 3 1 * *        /opt/etl/run.sh
```
Riscos: sem **dependências** entre jobs, sem **retry/alerta**, sem **backfill**, sobreposição de execuções (use `flock`), e fuso horário do servidor. Daí os orquestradores ([módulo 11](../../11-orchestration/README.md)). Ver [cron](../../02-linux-shell-environment/06-cron/README.md).
</details>

## 5. 🟣 Implementação — Diagnóstico de disco cheio

Um servidor de ingestão parou com `No space left on device`. Escreva a **sequência de comandos** para achar o que ocupa o espaço (incluindo o caso em que `df` diz 100% mas `du` não soma isso) e proponha uma correção durável.

<details><summary>Gabarito</summary>

```bash
df -h                        # qual filesystem?
df -i                        # inodes esgotados? (milhões de arquivos pequenos)
du -xh --max-depth=1 / | sort -rh | head
du -xh /var/log --max-depth=1 | sort -rh | head
lsof +L1                     # arquivos APAGADOS mas ainda abertos (df cheio, du vazio)
```
`lsof +L1` revela o clássico: log apagado com o processo ainda escrevendo — o espaço só volta ao reiniciar/ `truncate` o processo. **Correção durável:** `logrotate` com compressão e retenção, alerta de uso (>80%), e compactar/arquivar dados antigos. Ver [logs e troubleshooting](../../02-linux-shell-environment/08-logs-and-troubleshooting/README.md).
</details>

## 6. 🟣 Arquitetura — Acesso seguro por SSH

Projete o acesso de 10 engenheiros a servidores de produção: autenticação, auditoria e **o que fazer quando alguém sai da empresa**. Cite ao menos um padrão melhor que "chaves copiadas à mão".

<details><summary>Gabarito</summary>

Chaves por pessoa (nunca compartilhadas), `PasswordAuthentication no`, **bastion/jump host**, e idealmente **certificados SSH de curta duração** emitidos por uma CA (via SSO) — revogação é automática pelo prazo. Auditoria: log de sessões e comandos (`auditd`/gravação de sessão).
Offboarding: com certificados, basta desativar a conta no SSO; com chaves, é preciso remover de **todos** os `authorized_keys` (por isso gerenciar com IaC). Ver [SSH](../../02-linux-shell-environment/07-ssh/README.md) e [segurança](../../26-security/README.md).
</details>
