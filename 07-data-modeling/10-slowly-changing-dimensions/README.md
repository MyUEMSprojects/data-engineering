# Slowly Changing Dimensions (SCD)

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

**Slowly Changing Dimensions (SCD)** são técnicas para lidar com **mudanças nos atributos
de uma [dimensão](../08-dimension-tables/README.md) ao longo do tempo** — e, crucialmente,
decidir se você **preserva o histórico** dessas mudanças. Exemplo clássico: um cliente
muda de endereço/região; uma venda antiga deve aparecer com a região **da época** ou com
a **atual**?

## Por que importa

Dimensões mudam devagar (clientes mudam de cidade, produtos mudam de categoria). Como você
trata isso define a **correção da análise histórica**. Escolher o tipo errado de SCD leva
a relatórios que "reescrevem o passado" ou que explodem de tamanho sem necessidade.

## O problema, concretamente

```text
Venda de jan/2020: cliente C-7 morava na região Sul.
Em 2023, C-7 muda para Sudeste.
Pergunta: "receita por região em 2020" deve contar C-7 em Sul (correto historicamente)
          ou em Sudeste (como ele é hoje)?
```

A resposta depende do **tipo de SCD** escolhido para aquele atributo.

## Os tipos principais

### SCD Tipo 0 — fixo (retain original)

O atributo **nunca muda** após a carga inicial (ex.: data de nascimento, data de
cadastro). Mudanças na origem são ignoradas.

### SCD Tipo 1 — sobrescreve (overwrite)

Atualiza o valor, **descartando** o histórico. Simples; a dimensão sempre reflete o
estado **atual**. A análise histórica passa a usar o valor novo ("reescreve o passado").

```sql
UPDATE dim_cliente SET regiao = 'Sudeste' WHERE cliente_id = 'C-7';
```

Use quando o histórico do atributo **não importa** ou era uma correção de erro.

### SCD Tipo 2 — nova versão (add new row) — o mais importante

Preserva o histórico criando uma **nova linha** a cada mudança, com
[surrogate keys](../09-surrogate-natural-keys/README.md) e colunas de validade. É o
padrão ouro para histórico.

```text
cliente_sk | cliente_id | regiao  | valido_de  | valido_ate | is_current
   100      |   C-7      | Sul     | 2020-01-01 | 2023-06-30 | false
   250      |   C-7      | Sudeste | 2023-07-01 | 9999-12-31 | true
```

- Fatos antigos apontam para `cliente_sk=100` (Sul); novos, para `250` (Sudeste).
- Consultas "como era na época" ficam corretas automaticamente (o fato guarda a sk vigente
  no evento).
- Colunas de apoio: `valido_de`/`valido_ate`, `is_current`, às vezes `versao`.

### SCD Tipo 3 — coluna anterior (add new attribute)

Guarda o valor **anterior** numa coluna extra (`regiao_atual`, `regiao_anterior`). Suporta
só **uma** mudança/comparação; usado quando se quer analisar "antes vs depois" de uma
reorganização pontual.

### Tipos híbridos (6 = 1+2+3)

Combinam técnicas: linha versionada (tipo 2) + uma coluna "valor atual" (tipo 1) para
permitir analisar tanto "como era" quanto "reatribuindo tudo ao valor atual". O "Tipo 6"
é o mais comum dos híbridos.

## Como escolher o tipo (por atributo!)

A decisão é **por atributo**, não por dimensão inteira:

```text
atributo muda e o histórico importa?   → Tipo 2
atributo muda e só o atual importa?     → Tipo 1
atributo nunca muda?                    → Tipo 0
precisa só comparar atual vs anterior?  → Tipo 3
```

Uma mesma `dim_cliente` pode ter `nome` como tipo 1 e `regiao` como tipo 2.

## Implementação em pipeline (visão)

A carga SCD2 compara o registro de entrada (staging) com a versão atual na dimensão:

1. Se é novo → insere com `is_current=true`.
2. Se mudou um atributo tipo 2 → **fecha** a versão atual (`valido_ate = ontem`,
   `is_current=false`) e **insere** uma nova versão.
3. Se mudou só atributo tipo 1 → sobrescreve na linha atual.

Isso é implementado com `MERGE`/`UPSERT`, [window functions](../../05-sql/05-window-functions/README.md)
para pegar a última versão, ou com **[dbt snapshots](../../28-dbt/04-snapshots/README.md)**
(que automatizam SCD2). O [CDC](../../09-etl-elt/06-cdc/README.md) frequentemente alimenta
esse processo.

## Cuidados

- **Idempotência** — reprocessar a carga não deve criar versões duplicadas (ver
  [idempotência](../../09-etl-elt/07-idempotency-retries/README.md)).
- **Dados tardios/fora de ordem** — mudanças que chegam atrasadas complicam a linha do
  tempo.
- **Crescimento** — SCD2 aumenta a dimensão; ok para dimensões pequenas, cuidado em
  atributos muito voláteis (considere *mini dimension*).
- **Join correto no fato** — o fato deve referenciar a versão vigente **na data do
  evento**.

## Erros comuns

- Usar tipo 1 (sobrescrever) onde o histórico importava → análise histórica errada.
- SCD2 sem surrogate key (impossível — PK duplicaria).
- Carga não idempotente gerando versões duplicadas.
- Aplicar o mesmo tipo a todos os atributos cegamente.
- Fato apontando para a versão "current" em vez da vigente na época.

## Boas práticas

- Decida o tipo **por atributo**, conforme a necessidade de histórico.
- SCD2 com surrogate key + `valido_de/ate` + `is_current`.
- Automatize com [dbt snapshots](../../28-dbt/04-snapshots/README.md) quando possível.
- Garanta idempotência e trate dados tardios.

## Relação com outros conceitos

- Depende de [surrogate keys](../09-surrogate-natural-keys/README.md); aplica-se a
  [dimensões](../08-dimension-tables/README.md).
- Alimentado por [CDC](../../09-etl-elt/06-cdc/README.md); automatizado por
  [dbt snapshots](../../28-dbt/04-snapshots/README.md).
- Usa [window functions](../../05-sql/05-window-functions/README.md) para versionar.

## Exercícios

1. Para uma `dim_cliente`, classifique `nome`, `regiao`, `data_cadastro`, `segmento` em
   tipos de SCD e justifique.
2. Implemente (SQL) a lógica de carga SCD2 para `regiao`: fechar a versão atual e abrir
   uma nova.
3. Escreva a consulta que, para cada venda, junta a versão da dimensão vigente na data do
   evento.
4. Explique por que SCD2 é impossível sem surrogate keys.

## Referências

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed. — SCD (tipos 0–7).
- Documentação do dbt — Snapshots (SCD2 automatizado).
