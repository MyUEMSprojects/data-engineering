# Shell scripting

> 🟢 Foundations · Parte de [02 — Linux & Shell](../README.md)

## O que é

Um **shell script** é um arquivo com comandos de shell (Bash) executados em
sequência. Serve para **automatizar** tarefas repetitivas: orquestrar passos de um
pipeline simples, preparar ambientes, mover arquivos, acionar ferramentas.

## Quando usar Bash vs Python

- **Bash:** colar comandos existentes, manipular arquivos/processos, *glue code*
  curto, entrypoints de container.
- **Python:** lógica de dados, parsing complexo, qualquer coisa com >~50 linhas de
  lógica ou estruturas de dados. Ver
  [Python para DE](../../04-python-for-data-engineering/README.md).

Regra prática: se você está criando funções, arrays e lógica complexa em Bash,
provavelmente já deveria estar em Python.

## Anatomia de um script robusto

```bash
#!/usr/bin/env bash
# ingest_vendas.sh — baixa e valida o CSV diário de vendas.
set -euo pipefail          # falha cedo e alto (ver abaixo)
IFS=$'\n\t'                # separador seguro

# --- configuração ---
readonly DATA_DIR="${DATA_DIR:-/data/raw}"   # usa env var ou default
readonly DATE="${1:?uso: $0 <YYYY-MM-DD>}"   # arg obrigatório

log() { printf '%s [%s] %s\n' "$(date -Is)" "$1" "${*:2}" >&2; }

main() {
  log INFO "Iniciando ingestão para ${DATE}"
  local url="https://exemplo.com/vendas/${DATE}.csv"
  local out="${DATA_DIR}/vendas_${DATE}.csv"

  curl -fsSL "$url" -o "$out"            # -f falha em HTTP >=400
  local linhas
  linhas=$(wc -l < "$out")
  if (( linhas < 2 )); then
    log ERROR "Arquivo vazio: ${out}"
    exit 1
  fi
  log INFO "OK: ${linhas} linhas em ${out}"
}

main "$@"
```

### `set -euo pipefail` (o mais importante)

- `-e` — aborta se qualquer comando falhar (sai com status ≠ 0).
- `-u` — erro ao usar variável não definida (pega *typos*).
- `-o pipefail` — um pipe falha se **qualquer** parte falhar (sem isso, só o
  último comando conta).

Sem isso, scripts "continuam" após erros e corrompem dados silenciosamente — um
pecado em pipelines. **Sempre comece com essa linha.**

## Variáveis, argumentos e expansão

```bash
nome="vendas"             # sem espaços ao redor do =
echo "${nome}_2024"       # sempre entre aspas: "${var}"
$0  $1  $2  "$@"  "$#"    # script, 1º arg, 2º arg, todos os args, nº de args
"${VAR:-default}"         # usa default se VAR vazia/indefinida
"${VAR:?mensagem}"        # erro com mensagem se VAR indefinida
$(comando)                # substituição por comando
$(( 2 + 3 ))              # aritmética
```

> **Sempre** use aspas em `"$var"` — sem elas, espaços e globbing causam bugs
> sérios (o problema de segurança/robustez nº 1 em Bash).

## Controle de fluxo

```bash
if [[ -f "$arquivo" ]]; then ...; elif ...; else ...; fi
for f in /data/*.csv; do echo "$f"; done
while read -r linha; do echo "$linha"; done < arquivo
case "$x" in
  start) ... ;;
  stop)  ... ;;
  *)     echo "comando inválido" ;;
esac
```

Testes úteis em `[[ ]]`: `-f` (arquivo existe), `-d` (dir), `-z` (string vazia),
`-n` (não vazia), `==`, `-eq`/`-lt`/`-gt` (numéricos).

## Funções, status e tratamento de erro

- Todo comando retorna um **exit status** (`0` = sucesso). Verifique com `$?` ou
  deixe o `set -e` cuidar.
- `trap` executa limpeza ao sair/erro:

```bash
cleanup() { rm -f "$tmpfile"; }
trap cleanup EXIT            # roda ao terminar (sucesso ou falha)
tmpfile=$(mktemp)           # arquivo temporário seguro
```

## Idempotência e segurança em pipelines

- Torne o script **idempotente**: rodar duas vezes não duplica dados (escreva em
  arquivo temporário e mova atômico; cheque se a saída já existe). Ver
  [idempotência](../../09-etl-elt/07-idempotency-retries/README.md).
- Escrita atômica: escreva em `arquivo.tmp` e `mv` para o nome final (o `mv` no
  mesmo filesystem é atômico).
- Nunca coloque segredos no script; leia de variáveis de ambiente/secret manager
  ([security](../../26-security/04-secrets-management/README.md)).

## Qualidade: ShellCheck

[`shellcheck`](https://www.shellcheck.net/) analisa scripts e aponta bugs comuns
(aspas faltando, variáveis indefinidas). Rode-o sempre — é o "lint" do Bash.

```bash
shellcheck ingest_vendas.sh
```

## Erros comuns

- Esquecer `set -euo pipefail` → erros silenciosos.
- Não usar aspas em variáveis.
- Lógica complexa em Bash que deveria ser Python.
- Caminhos relativos (quebram sob cron/container) — use absolutos.
- Comparar números com `==` em vez de `-eq`.

## Boas práticas

- Shebang `#!/usr/bin/env bash`.
- `main "$@"` no fim; lógica em funções.
- Logue com timestamp em `stderr`; deixe `stdout` para dados.
- `shellcheck` no [CI](../../23-cicd-dataops/README.md).

## Relação com outros conceitos

- Agendado por [cron](../06-cron/README.md).
- Usa [processamento de texto](../04-text-processing/README.md).
- Entrypoints de [containers](../../20-containers/README.md) costumam ser scripts.

## Exercícios

1. Escreva um script que recebe uma data como argumento, baixa um arquivo e falha
   com mensagem clara se o download retornar erro HTTP.
2. Torne-o idempotente: se o arquivo do dia já existe e é válido, pular.
3. Rode `shellcheck` no seu script e corrija todos os avisos.
4. Adicione um `trap` que remove arquivos temporários mesmo se o script falhar.

## Referências

- Google Shell Style Guide.
- `man bash`, ShellCheck wiki.
- *The Linux Command Line* (parte de scripting).
