# Linux básico

> 🟢 Foundations · Parte de [02 — Linux & Shell](../README.md)

## O que é

Linux é um sistema operacional de código aberto que domina servidores, cloud e
containers. Você interage com ele pelo **shell** (geralmente **Bash**), um
interpretador de comandos que lê linhas de texto e executa programas.

## Por que o DE precisa disso

Seus pipelines rodam em Linux (dentro de [containers](../../20-containers/README.md),
em [clusters](../../21-kubernetes/README.md), em VMs cloud). Saber operar o shell
é o que permite inspecionar dados, rodar ferramentas e depurar sem depender de
interface gráfica.

## Anatomia de um comando

```bash
comando [opções] [argumentos]
ls      -la      /var/log       # lista, formato longo + ocultos, no diretório
```

- **Opções curtas** (`-l`) e **longas** (`--all`); combináveis (`-la`).
- `--help` e `man comando` mostram a documentação.
- O **prompt** (`$` para usuário comum, `#` para root) indica que o shell espera
  um comando.

## Comandos essenciais

### Navegação

```bash
pwd                 # diretório atual
ls -lah             # listar (longo, legível, ocultos)
cd /caminho         # mudar de diretório; cd -  volta ao anterior; cd ~ = home
tree -L 2           # árvore de diretórios (se instalado)
```

### Arquivos e diretórios

```bash
mkdir -p a/b/c      # cria diretórios aninhados
touch arquivo.txt   # cria arquivo vazio / atualiza timestamp
cp -r origem destino
mv antigo novo      # mover/renomear
rm arquivo          # remover (rm -r dir; CUIDADO: não há lixeira)
ln -s alvo link     # link simbólico
```

### Ver conteúdo

```bash
cat arquivo              # imprime tudo
less arquivo             # paginador (q sai, / busca)
head -n 20 arquivo       # primeiras linhas
tail -n 20 arquivo       # últimas linhas
tail -f app.log          # acompanha o arquivo crescendo (logs!)
wc -l arquivo.csv        # conta linhas (útil p/ datasets)
```

### Informação do sistema

```bash
whoami; id               # usuário atual e grupos
df -h                    # espaço em disco por partição
du -sh pasta/            # tamanho de uma pasta
free -h                  # memória
uname -a                 # versão do kernel
history                  # comandos anteriores
```

## Ajuda e descoberta

- `man comando` — manual completo.
- `comando --help` — resumo rápido.
- `type comando` / `which comando` — onde está o executável, ou se é alias.
- `tldr comando` — exemplos práticos (pacote externo).
- [explainshell.com](https://explainshell.com) — explica cada parte de um comando.

## Atalhos de terminal importantes

| Atalho | Ação |
| --- | --- |
| `Ctrl+C` | Interrompe o comando atual |
| `Ctrl+D` | Fim de entrada (EOF) / sai do shell |
| `Ctrl+R` | Busca reversa no histórico |
| `Tab` | Autocompleta |
| `Ctrl+A` / `Ctrl+E` | Início / fim da linha |
| `Ctrl+L` | Limpa a tela (`clear`) |

## Variáveis de ambiente (introdução)

```bash
echo $HOME               # valor de uma variável
export API_URL=https://... # define para o processo e filhos
env                      # lista todas
```

Variáveis de ambiente configuram ferramentas e **guardam segredos/credenciais**
(nunca comite segredos — ver [12-factor](../05-shell-scripting/README.md) e
[security](../../26-security/04-secrets-management/README.md)). O `PATH` define
onde o shell procura executáveis.

## Erros comuns

- `rm -rf` no diretório errado — **não há desfazer**. Confira o caminho antes.
- Esquecer aspas em caminhos com espaços: `cd "Minha Pasta"`.
- Confundir caminho **relativo** (`./dados`) com **absoluto** (`/home/...`).
- Editar como `root` sem necessidade.

## Boas práticas

- Use `less` em vez de `cat` para arquivos grandes.
- Prefira `cp -i`/`mv -i`/`rm -i` (pergunta antes de sobrescrever) quando em
  dúvida.
- Aprenda `Ctrl+R` — economiza muito tempo.

## Relação com outros conceitos

- Base para [filesystem](../02-filesystem/README.md),
  [processos](../03-processes-and-permissions/README.md) e
  [processamento de texto](../04-text-processing/README.md).

## Exercícios

1. Crie a estrutura `projeto/{raw,processed,scripts}` com um comando só.
2. Descubra quantas linhas tem um arquivo `.csv` e veja suas 5 primeiras linhas.
3. Use `Ctrl+R` para reencontrar e reexecutar um comando que você digitou antes.
4. Descubra qual diretório está ocupando mais espaço no seu home (`du -sh *`).

## Referências

- Shotts, W. *The Linux Command Line*. No Starch Press (linuxcommand.org).
- `man bash`, `man ls`, `man less`.
