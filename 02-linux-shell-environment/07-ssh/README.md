# SSH

> 🟢 Foundations · Parte de [02 — Linux & Shell](../README.md)

## O que é

**SSH (Secure Shell)** é o protocolo padrão para acessar e operar máquinas remotas
de forma criptografada. O Data Engineer usa SSH para entrar em servidores, rodar
comandos, copiar arquivos e criar **túneis** para alcançar serviços internos
(bancos, UIs de ferramentas) com segurança.

## Como funciona

SSH usa **criptografia assimétrica** (par de chaves pública/privada) para
autenticar e criptografia simétrica para a sessão. Você guarda a **chave privada**
(secreta, nunca sai da sua máquina) e coloca a **chave pública** no servidor. O
servidor desafia; só quem tem a privada correspondente passa.

```text
  Sua máquina                         Servidor remoto
 ┌───────────┐   conexão TCP/22      ┌──────────────┐
 │ chave      │◄────────────────────►│ ~/.ssh/       │
 │ privada    │  prova de posse      │ authorized_keys (sua pública)
 └───────────┘                        └──────────────┘
```

## Chaves: criação e uso

```bash
ssh-keygen -t ed25519 -C "felipe@maquina"   # gera par (ed25519 é o recomendado)
# gera ~/.ssh/id_ed25519 (privada) e id_ed25519.pub (pública)

ssh-copy-id user@servidor                    # instala sua pública no servidor
# ou manualmente: anexe o conteúdo do .pub em ~/.ssh/authorized_keys no servidor
```

> Prefira autenticação por **chave** em vez de senha (mais seguro e automatizável).
> Proteja a chave privada com uma *passphrase* e use o `ssh-agent` para não
> redigitá-la.

### Permissões (causa nº 1 de "Permission denied")

O SSH **recusa** chaves com permissões abertas demais:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519        # privada: só o dono lê/escreve
chmod 644 ~/.ssh/id_ed25519.pub
chmod 600 ~/.ssh/authorized_keys
```

## Conectando e executando

```bash
ssh user@servidor                       # sessão interativa
ssh user@servidor "df -h"               # executa um comando e sai
ssh -p 2222 user@servidor               # porta customizada
ssh -i ~/.ssh/outra_chave user@host     # chave específica
```

## Arquivo de configuração (~/.ssh/config)

Em vez de decorar hosts e flags, declare-os:

```ssh-config
Host prod-etl
    HostName 10.0.3.14
    User felipe
    Port 22
    IdentityFile ~/.ssh/id_ed25519

Host bastion
    HostName bastion.exemplo.com
    User felipe

Host db-interno
    HostName 10.0.5.9
    User felipe
    ProxyJump bastion          # pula pelo bastion para alcançar a rede privada
```

Agora basta `ssh prod-etl`. `ProxyJump` é essencial para acessar hosts em redes
privadas via um **bastion host**.

## Copiando arquivos

```bash
scp arquivo.csv prod-etl:/data/raw/        # envia
scp prod-etl:/data/out/result.parquet .    # baixa
scp -r pasta/ prod-etl:/data/              # recursivo

# rsync: incremental, retomável, melhor para muitos/grandes arquivos
rsync -avz --progress pasta/ prod-etl:/data/pasta/
rsync -avz prod-etl:/data/ ./backup/       # baixa só o que mudou
```

Para transferências grandes e repetidas, **prefira `rsync`** (só copia diffs).

## Túneis (port forwarding)

Permitem alcançar um serviço remoto como se fosse local — útil para acessar um
banco ou uma UI (Airflow, Spark) que só escuta na rede interna.

```bash
# Local forwarding: localhost:5433 -> banco interno:5432 (via servidor)
ssh -L 5433:10.0.5.9:5432 prod-etl
# agora conecte seu cliente a localhost:5433

# acessar a UI do Airflow remota em http://localhost:8080
ssh -L 8080:localhost:8080 prod-etl
```

## Sessões persistentes

Comandos longos morrem se a conexão cair. Combine SSH com **`tmux`**:

```bash
ssh prod-etl
tmux new -s etl        # cria sessão; rode seu job aqui
# Ctrl+b d  -> "detach"; pode desconectar
tmux attach -t etl     # reconecta depois
```

## Segurança

- Chave privada **nunca** é compartilhada nem versionada.
- Desative login por senha e por root no servidor (`sshd_config`) quando possível.
- Use *bastion hosts* para isolar redes privadas (ver
  [network security](../../26-security/05-network-security/README.md)).
- Rotacione chaves; remova as de pessoas que saíram (`authorized_keys`).

## Erros comuns

- Permissões erradas em `~/.ssh` → "Permission denied (publickey)".
- Versionar chave privada por engano (adicione ao [.gitignore](../../.gitignore)).
- Esquecer `-r` no `scp` de diretórios.
- Transferir TBs com `scp` em vez de `rsync` (sem retomada).

## Relação com outros conceitos

- Base para operar [cloud](../../19-cloud/README.md) e servidores de pipeline.
- Permissões: [processos e permissões](../03-processes-and-permissions/README.md).
- Git sobre SSH: [03 — Git](../../03-git-software-engineering/README.md).

## Exercícios

1. Gere um par de chaves ed25519 e configure acesso por chave a uma VM (local ou
   cloud).
2. Escreva uma entrada em `~/.ssh/config` que alcança um host privado via bastion
   com `ProxyJump`.
3. Crie um túnel para acessar um PostgreSQL remoto em `localhost:5433` e conecte
   com `psql`.
4. Copie uma pasta grande com `rsync` e explique por que ele é melhor que `scp`
   aqui.

## Referências

- `man ssh`, `man ssh_config`, `man scp`, `man rsync`.
- OpenSSH documentation (openssh.com).
