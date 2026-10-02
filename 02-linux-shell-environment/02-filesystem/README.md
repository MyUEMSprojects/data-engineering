# Filesystem

> 🟢 Foundations · Parte de [02 — Linux & Shell](../README.md)

## O que é

O **filesystem** (sistema de arquivos) organiza como dados são armazenados e
acessados no disco. No Linux, tudo é uma árvore única começando na **raiz** (`/`)
— inclusive dispositivos e recursos do sistema são expostos como arquivos
("everything is a file").

## Por que o DE precisa disso

Pipelines leem e escrevem arquivos o tempo todo (CSV, [Parquet](../../08-data-formats/04-parquet/README.md),
logs). Entender caminhos, permissões de diretório, links e pontos de montagem
evita bugs do tipo "arquivo não encontrado", "disco cheio" e "permission denied",
e é essencial ao montar [volumes em containers](../../20-containers/03-volumes-networks/README.md).

## Hierarquia (FHS — Filesystem Hierarchy Standard)

```text
/            raiz de tudo
├── bin      executáveis essenciais (ls, cp...)
├── etc      arquivos de configuração do sistema
├── home     diretórios dos usuários (/home/felipe)
├── var      dados variáveis: /var/log (logs!), /var/lib
├── tmp      temporários (limpos ao reiniciar)
├── opt      softwares de terceiros
├── usr      programas e bibliotecas do usuário
├── mnt /media  pontos de montagem de discos externos
├── dev      dispositivos (discos, etc.)
└── proc /sys  interfaces do kernel (processos, hardware)
```

Para DE, os mais relevantes no dia a dia: `/var/log` (logs),
`/etc` (configs), `/tmp` e `/home`.

## Caminhos

- **Absoluto** — começa em `/`: `/home/felipe/data/raw.csv`.
- **Relativo** — a partir do diretório atual: `data/raw.csv`, `../outro`.
- Símbolos: `.` (atual), `..` (pai), `~` (home do usuário).

> Em scripts e pipelines, **prefira caminhos absolutos** ou derive-os
> explicitamente — caminhos relativos quebram quando o *working directory* muda
> (um erro clássico em cron e containers).

## Tipos de "arquivo"

```bash
ls -l
# -  arquivo comum
# d  diretório
# l  link simbólico
# c/b  dispositivos de caractere/bloco
```

## Links

```bash
ln -s /dados/2024/vendas.parquet latest.parquet   # link simbólico (atalho)
ln arquivo hardlink                                # hard link (mesmo inode)
```

- **Symlink** aponta para um *caminho*; quebra se o alvo some. Muito usado para
  apontar "latest" para a partição mais recente.
- **Hard link** aponta para os *mesmos dados* (inode); sobrevive à remoção do
  nome original.

## Inodes, espaço e "disco cheio"

Cada arquivo tem um **inode** (metadados + ponteiros para os blocos). Dois limites
podem estourar:

```bash
df -h          # espaço em disco (GB)
df -i          # inodes (nº de arquivos) — pode acabar antes do espaço!
du -sh *       # tamanho por item no diretório atual
```

O **small files problem** (muitos arquivos minúsculos) pode esgotar inodes e
degradar performance — relevante em [data lakes](../../14-data-lake/06-small-files-compaction/README.md).

## Montagem (mount)

Discos e sistemas remotos são "montados" em um diretório:

```bash
mount                      # o que está montado onde
lsblk                      # dispositivos de bloco e partições
```

Em containers, você **monta volumes** do host dentro do container para persistir
dados (ver [volumes](../../20-containers/03-volumes-networks/README.md)).

## Globbing (padrões de arquivo)

```bash
ls data/*.csv            # todos os .csv
ls data/2024-0[1-3]*     # jan a mar de 2024
ls data/**/*.parquet     # recursivo (com shopt -s globstar)
```

## Erros comuns

- Assumir *working directory* em scripts → use caminhos absolutos.
- Encher `/` ou `/tmp` sem perceber (monitore com `df -h`).
- Esgotar inodes com milhões de arquivos pequenos.
- Symlink apontando para alvo inexistente (link "quebrado").

## Boas práticas

- Padronize uma estrutura de diretórios para dados (`raw/`, `staging/`,
  `processed/`), particionada por data.
- Nunca grave dados importantes em `/tmp`.
- Monitore espaço/inodes em máquinas de pipeline.

## Relação com outros conceitos

- Permissões desses arquivos/diretórios: [processos e permissões](../03-processes-and-permissions/README.md).
- Padrões de pastas particionadas: [data lake / partitioning](../../14-data-lake/05-partitioning/README.md).

## Exercícios

1. Explique a diferença entre symlink e hard link e dê um caso de uso de cada no
   contexto de "apontar para o dataset mais recente".
2. Um pipeline falha com "No space left on device" mas `df -h` mostra espaço
   livre. O que mais pode ter acabado? Como verificar?
3. Crie uma estrutura `lake/{bronze,silver,gold}/dt=2024-01-01/` e liste-a com
   `tree`.

## Referências

- Filesystem Hierarchy Standard (FHS 3.0).
- `man hier`, `man mount`, `man ln`.
