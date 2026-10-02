# Processamento de texto (pipes, grep, sed, awk, find, xargs)

> 🟢 Foundations · Parte de [02 — Linux & Shell](../README.md)

## Por que isso é ouro para Data Engineering

A filosofia Unix é "programas pequenos que fazem uma coisa bem, combinados por
pipes". Para o DE, isso significa inspecionar, filtrar e transformar arquivos de
dados (CSV, logs, JSONL) **em segundos**, sem escrever um script Python. É a
ferramenta mais rápida para responder "esse arquivo de 10 GB tem o quê?".

## Fundamentos: streams, pipes e redirecionamento

Todo processo tem três *streams*: **stdin** (0), **stdout** (1), **stderr** (2).

```bash
cmd > out.txt            # redireciona stdout para arquivo (sobrescreve)
cmd >> out.txt           # anexa
cmd 2> err.txt           # redireciona stderr
cmd > all.txt 2>&1       # stdout e stderr para o mesmo arquivo
cmd < in.txt             # usa arquivo como stdin
cmd1 | cmd2              # pipe: stdout de cmd1 vira stdin de cmd2
cmd | tee arquivo        # mostra na tela E salva
```

Pipes são a essência: encadeie filtros e cada um faz uma coisa.

## grep — buscar padrões

```bash
grep "erro" app.log              # linhas com "erro"
grep -i "erro" app.log           # case-insensitive
grep -r "TODO" .                 # recursivo em diretórios
grep -c "404" access.log         # conta ocorrências
grep -n "panic" app.log          # com número da linha
grep -v "DEBUG" app.log          # inverte: linhas SEM "DEBUG"
grep -E "erro|falha|timeout" log # regex estendida (OR)
grep -A2 -B2 "exception" app.log # 2 linhas antes/depois do match
```

## Ferramentas de recorte e contagem

```bash
cut -d',' -f1,3 dados.csv        # colunas 1 e 3 (delimitador vírgula)
sort dados.txt                   # ordena
sort -t',' -k2 -n dados.csv      # ordena pela coluna 2, numérico
uniq -c                          # conta duplicatas consecutivas (use após sort)
tr 'a-z' 'A-Z'                   # troca caracteres
head/tail/wc                     # ver topo/fim/contar
```

Idioma clássico "top N mais frequentes":

```bash
cut -d',' -f3 vendas.csv | sort | uniq -c | sort -rn | head -10
```

## sed — edição de fluxo (stream editor)

```bash
sed 's/antigo/novo/' arquivo         # substitui a 1ª ocorrência por linha
sed 's/antigo/novo/g' arquivo        # substitui todas (global)
sed -n '10,20p' arquivo              # imprime só as linhas 10–20
sed '1d' dados.csv                   # remove a 1ª linha (cabeçalho)
sed -i 's/,/;/g' dados.csv           # edita o arquivo in-place (cuidado!)
```

## awk — processamento por colunas

`awk` lê linha a linha, divide em campos (`$1`, `$2`, ...) e executa ações. É uma
mini-linguagem ótima para dados tabulares.

```bash
awk -F',' '{print $1, $3}' dados.csv          # imprime colunas 1 e 3
awk -F',' '$3 > 100' vendas.csv               # linhas com coluna 3 > 100
awk -F',' '{soma += $3} END {print soma}' v.csv  # soma a coluna 3
awk -F',' 'NR>1 {c[$2]++} END{for(k in c) print k, c[k]}' v.csv  # contagem por grupo
awk 'NR==1 || $0 ~ /erro/' app.log            # cabeçalho + linhas com "erro"
```

Variáveis especiais: `NR` (nº da linha), `NF` (nº de campos), `FS`/`OFS`
(separador de entrada/saída).

## find — localizar arquivos

```bash
find . -name "*.parquet"                 # por nome
find . -type f -mtime -1                 # arquivos modificados nas últimas 24h
find . -type f -size +100M               # maiores que 100 MB
find /tmp -type f -mtime +7 -delete      # apaga temporários com +7 dias
find . -name "*.log" -exec gzip {} \;    # executa um comando por arquivo
```

## xargs — construir comandos a partir de uma lista

```bash
find . -name "*.csv" | xargs wc -l             # conta linhas de todos os CSVs
find . -name "*.tmp" | xargs rm                # remove (cuidado!)
find . -name "*.csv" -print0 | xargs -0 ...    # -print0/-0: seguro com espaços
cat urls.txt | xargs -P4 -I{} curl -O {}       # baixa 4 em paralelo
```

`-P` dá **paralelismo** — útil para processar muitos arquivos.

## jq — para JSON (bônus essencial)

Muitos dados vêm em JSON/JSONL. `jq` é o "awk do JSON":

```bash
cat resp.json | jq '.items[] | .id'         # extrai campo id de cada item
cat eventos.jsonl | jq -c 'select(.type=="click")'  # filtra por campo
```

## Exemplo real: inspecionar um CSV de 5 GB sem abrir no editor

```bash
head -1 vendas.csv                         # cabeçalho
wc -l vendas.csv                           # nº de linhas
cut -d',' -f4 vendas.csv | sort -u | head  # valores distintos da coluna 4
awk -F',' 'NR>1 {s+=$7} END{print s}' vendas.csv  # soma de faturamento
grep -c ',,' vendas.csv                    # linhas com campos vazios
```

## Erros comuns

- `sed -i` sem backup → edição destrutiva irreversível (use `sed -i.bak`).
- Esquecer `-F','` no `awk`/`cut` para CSV.
- `uniq` sem `sort` antes (só remove duplicatas **consecutivas**).
- Quebrar com espaços/nomes especiais → use `find -print0 | xargs -0`.
- CSVs com vírgulas *dentro* de aspas quebram `cut`/`awk` ingênuos — para esses,
  use uma ferramenta que entende CSV (`csvkit`, `mlr`/Miller, ou Python/pandas).

## Boas práticas

- Construa o pipe incrementalmente, adicionando um filtro por vez.
- Para CSV "de verdade" (com aspas/escapes), prefira `mlr`/`csvkit`/pandas.
- Guarde *one-liners* úteis; eles viram sua caixa de ferramentas.

## Relação com outros conceitos

- Usado em [shell scripting](../05-shell-scripting/README.md) e
  [troubleshooting](../08-logs-and-troubleshooting/README.md).
- Alternativa programática: [Python/pandas/polars](../../04-python-for-data-engineering/README.md).

## Exercícios

1. Dado um `access.log`, liste os 10 IPs com mais requisições (pipe
   `cut|sort|uniq -c|sort -rn|head`).
2. Some uma coluna numérica de um CSV com `awk`, ignorando o cabeçalho.
3. Encontre todos os `.log` modificados nas últimas 24h e compacte-os.
4. Em um JSONL de eventos, conte quantos têm `type == "purchase"` usando `jq`.

## Referências

- Dougherty, D.; Robbins, A. *sed & awk*. O'Reilly.
- `man grep`, `man sed`, `man awk`, `man find`, `man xargs`.
- `jq` manual (stedolan.github.io/jq).
