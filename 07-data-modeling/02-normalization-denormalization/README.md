# Normalização e desnormalização

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

- **Normalização** — organizar tabelas para **eliminar redundância** e evitar anomalias,
  dividindo dados em tabelas relacionadas por chaves. Guiada pelas **formas normais**.
- **Desnormalização** — o movimento oposto: **duplicar/combinar** dados de propósito para
  ganhar performance de leitura, aceitando redundância.

Normalizar é o default em [OLTP](../03-oltp-vs-olap-modeling/README.md); desnormalizar é
comum em [OLAP/analytics](../04-dimensional-modeling/README.md).

## Por que normalizar: anomalias

Sem normalização, dados repetidos geram **anomalias**:

```text
pedidos(id, cliente_nome, cliente_email, cliente_uf, produto, valor)  -- tudo numa tabela
```

- **Update anomaly** — o cliente muda de e-mail: você precisa atualizar em **todas** as
  linhas dele (e se esquecer uma, fica inconsistente).
- **Insert anomaly** — não dá para cadastrar um cliente sem um pedido.
- **Delete anomaly** — apagar o último pedido de um cliente apaga o cliente.

Normalizar (separar `clientes` de `pedidos`) resolve: cada fato vive em um lugar só.

## As formas normais (progressivas)

### 1NF — Primeira Forma Normal

Valores **atômicos** (sem listas/grupos repetidos numa célula); cada linha única.

```text
RUIM:  pedido(id, produtos="X,Y,Z")      -- lista numa coluna
BOM:   itens(pedido_id, produto)         -- uma linha por produto
```

### 2NF — Segunda Forma Normal

Estar em 1NF **e** todo atributo não-chave depender da **chave inteira** (elimina
dependência parcial de chave composta).

```text
RUIM: itens(pedido_id, produto_id, produto_nome)  -- produto_nome depende só de produto_id
BOM:  itens(pedido_id, produto_id, qtd) + produtos(produto_id, produto_nome)
```

### 3NF — Terceira Forma Normal

Estar em 2NF **e** nenhum atributo não-chave depender de **outro atributo não-chave**
(elimina dependência transitiva).

```text
RUIM: clientes(id, cidade, uf, regiao)   -- regiao depende de uf, não de id
BOM:  clientes(id, cidade, uf) + ufs(uf, regiao)
```

**3NF é o alvo prático** para modelagem transacional. Há formas mais altas (BCNF, 4NF,
5NF) relevantes em casos específicos, mas raramente necessárias no dia a dia.

> Mnemônico (Kimball/Codd): cada atributo não-chave depende "da chave, da chave inteira,
> e de nada além da chave".

## Quando desnormalizar (e por quê)

Normalização otimiza **escrita e integridade** (ótimo para OLTP), mas exige **joins** na
leitura. Em analytics, joins de muitas tabelas a cada consulta são caros e confusos.
Desnormaliza-se para:

- **Reduzir joins** → consultas mais rápidas e simples.
- **Pré-calcular/combinar** dados lidos juntos.
- Servir [modelos dimensionais](../04-dimensional-modeling/README.md) (dimensões são
  deliberadamente desnormalizadas).

O custo: **redundância** (mais espaço) e risco de **inconsistência** — por isso a
desnormalização analítica é mantida por **pipelines** (o ETL recria os dados), não por
updates manuais. Como o dado é recriado a cada carga, a anomalia de update deixa de ser
problema.

```text
OLTP (normalizado):  integridade, escrita eficiente, muitos joins na leitura
OLAP (desnormalizado): leitura rápida, poucas joins, redundância controlada pelo ETL
```

## Exemplo lado a lado

```sql
-- Normalizado (OLTP): 3 tabelas
pedidos(id, cliente_id, data_id, valor)
clientes(id, nome, uf, regiao)
datas(id, dia, mes, ano)

-- Desnormalizado (OLAP star): fato + dimensão larga
fato_vendas(data_sk, cliente_sk, valor)
dim_cliente(cliente_sk, nome, uf, regiao)   -- uf+regiao juntos (desnormalizado)
dim_data(data_sk, dia, mes, ano, trimestre, dia_semana, feriado)
```

## Erros comuns

- **Sub-normalizar** OLTP → anomalias e dados inconsistentes.
- **Normalizar demais** o warehouse → joins intermináveis, consultas lentas e confusas.
- Desnormalizar e depois **atualizar manualmente** (reintroduz anomalias) em vez de
  recriar via pipeline.
- Guardar listas numa coluna (viola 1NF) quando deveriam ser linhas.

## Boas práticas

- OLTP: normalize (3NF) para integridade.
- OLAP: desnormalize de forma controlada (dimensional), recriado por ETL/dbt.
- Documente a **razão** de cada desnormalização.
- Use [constraints](../../05-sql/09-constraints/README.md) para proteger a integridade do
  modelo normalizado.

## Relação com outros conceitos

- Base de [OLTP vs OLAP modeling](../03-oltp-vs-olap-modeling/README.md) e
  [modelagem dimensional](../04-dimensional-modeling/README.md).
- Integridade via [constraints](../../05-sql/09-constraints/README.md).
- Recriação por [ETL/ELT](../../09-etl-elt/README.md).

## Exercícios

1. Pegue uma tabela "tudo em um" e normalize-a até 3NF, nomeando cada anomalia que você
   elimina.
2. Identifique a dependência transitiva em `clientes(id, cidade, uf, regiao)` e corrija.
3. Desnormalize o modelo normalizado em um star schema para analytics e justifique.
4. Explique por que a desnormalização analítica não sofre de update anomaly na prática.

## Referências

- Codd, E. F. — formas normais.
- Kimball, R. *The Data Warehouse Toolkit* — normalização vs dimensional.
- Documentação do PostgreSQL; *Database Design for Mere Mortals*, Hernandez.
