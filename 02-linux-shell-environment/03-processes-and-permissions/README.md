# Processos e permissões

> 🟢 Foundations · Parte de [02 — Linux & Shell](../README.md)

Dois assuntos que juntos explicam **o que está rodando** na máquina e **quem pode
fazer o quê** — base de *troubleshooting* e de segurança operacional.

## Parte 1 — Processos

### O que é

Um **processo** é um programa em execução, com seu próprio PID (identificador),
memória e estado. Seu pipeline, um worker do Airflow, um executor do Spark — todos
são processos.

### Observando processos

```bash
ps aux                   # todos os processos (snapshot)
ps aux | grep python     # filtra os de python
top                      # monitor interativo (CPU/mem em tempo real)
htop                     # versão melhor (se instalada)
pgrep -fl airflow        # PIDs cujo comando casa com "airflow"
```

Colunas úteis em `ps aux`: `%CPU`, `%MEM`, `STAT` (estado), `START`, `COMMAND`.

### Estados de processo

- **R** running/runnable, **S** sleeping (esperando), **D** uninterruptible
  sleep (geralmente I/O — se travar aqui, suspeite de disco/rede), **Z** zombie
  (terminou mas o pai não "colheu"), **T** parado.

### Sinais e término

```bash
kill PID                 # envia SIGTERM (pedido educado de encerrar)
kill -9 PID              # SIGKILL (forçado; último recurso)
kill -HUP PID            # SIGHUP (muitos serviços recarregam config)
```

- **SIGTERM (15)** permite ao processo limpar/encerrar graciosamente — prefira-o.
- **SIGKILL (9)** mata imediatamente, sem limpeza → pode deixar estado corrompido.

### Foreground, background e jobs

```bash
long_job.sh &            # roda em background
jobs                     # lista jobs do shell
fg %1                    # traz job 1 para foreground
Ctrl+Z                   # suspende o processo em foreground
bg %1                    # retoma em background
nohup cmd &              # continua rodando após fechar o terminal
```

Para jobs longos em servidores, prefira **`tmux`**/`screen` (sessões persistentes)
a `nohup`.

### Recursos e limites

```bash
free -h                  # memória
uptime                   # carga média (load average)
nice -n 10 cmd           # roda com menor prioridade
ulimit -a                # limites do shell (nº de arquivos abertos etc.)
```

O **OOM killer** do kernel mata processos quando a memória acaba — causa comum de
"meu job Spark/pandas morreu sem erro claro". Verifique com `dmesg` /
`journalctl -k`.

## Parte 2 — Usuários e permissões

### Modelo de permissões

Cada arquivo tem **dono (user)**, **grupo (group)** e **outros (others)**, cada um
com permissões de **leitura (r)**, **escrita (w)** e **execução (x)**.

```bash
ls -l script.sh
# -rwxr-xr--  1 felipe data 1200 ...
#  │└┬┘└┬┘└┬┘
#  │ u  g  o
#  tipo
```

Leitura: dono `rwx`, grupo `r-x`, outros `r--`.

### Notação octal

| Símbolo | Octal | Significado |
| --- | --- | --- |
| `r` | 4 | ler |
| `w` | 2 | escrever |
| `x` | 1 | executar (em diretório: entrar/listar) |

Soma por classe: `rwx`=7, `rw-`=6, `r-x`=5, `r--`=4.
`chmod 750 arquivo` → dono `rwx`, grupo `r-x`, outros nada.

### Mudando permissões e dono

```bash
chmod +x script.sh            # torna executável
chmod 644 dados.csv           # rw-r--r--
chmod -R 750 pasta/           # recursivo
chown felipe:data arquivo     # muda dono e grupo (requer privilégio)
```

Em **diretórios**, `x` significa "poder entrar/atravessar". Um erro comum é dar
`r` sem `x` num diretório e não conseguir acessá-lo.

### root, sudo e least privilege

- **root** (UID 0) pode tudo. Evite trabalhar como root.
- `sudo comando` executa como root pontualmente.
- Princípio do **menor privilégio**: processos/pipelines devem rodar com o mínimo
  de permissão necessário (ver [security](../../26-security/06-least-privilege/README.md)).

### Por que isso causa bugs em pipelines

- Container roda como um usuário sem permissão de escrever no volume montado →
  "Permission denied".
- Arquivo gerado por um job (`root`) não pode ser lido por outro (usuário comum).
- Chave SSH com permissão aberta demais → o SSH **recusa** usá-la (ver
  [SSH](../07-ssh/README.md)).

## Erros comuns

- `kill -9` como primeira opção (use SIGTERM primeiro).
- Rodar tudo como root "para evitar erros de permissão" — mascara o problema real.
- Esquecer o `x` em diretórios.
- Ignorar o OOM killer ao investigar jobs que "somem".

## Relação com outros conceitos

- Troubleshooting usa estes comandos: [logs & troubleshooting](../08-logs-and-troubleshooting/README.md).
- Permissões em containers: [20 — Containers](../../20-containers/README.md).
- Least privilege e IAM: [26 — Security](../../26-security/README.md).

## Exercícios

1. Encontre o processo que mais consome memória agora e explique como o
   descobriu.
2. Traduza `chmod 640` para `rwx` por classe e diga para que tipo de arquivo isso
   faria sentido.
3. Um job em background morreu quando você fechou o SSH. Como evitar isso da
   próxima vez (duas soluções)?
4. Um container não consegue escrever num volume montado. Liste 2 causas de
   permissão possíveis.

## Referências

- `man ps`, `man kill`, `man chmod`, `man chown`.
- Kerrisk, M. *The Linux Programming Interface* (referência avançada).
