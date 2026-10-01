# JOINs

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

`JOIN` combina linhas de duas (ou mais) tabelas com base em uma condição de
relacionamento (geralmente chave estrangeira = chave primária). É como você reúne
dados normalizados espalhados em várias tabelas — operação diária em DE.

## As tabelas de exemplo

```text
clientes(id, nome, uf)           pedidos(id, cliente_id, valor, status)
```

## Tipos de JOIN

### INNER JOIN — só o que casa nos dois lados

```sql
SELECT p.id, c.nome, p.valor
FROM pedidos p
INNER JOIN clientes c ON c.id = p.cliente_id;
```

Retorna só pedidos que têm cliente correspondente (e vice-versa). Pedidos órfãos ou
clientes sem pedidos **somem**.

### LEFT JOIN — tudo da esquerda + o que casar da direita

```sql
SELECT c.nome, p.id AS pedido
FROM clientes c
LEFT JOIN pedidos p ON p.cliente_id = c.id;   -- clientes SEM pedido aparecem com NULL
```

O `LEFT JOIN` é o mais usado em analytics: "todos os clientes, com seus pedidos se
houver". Clientes sem pedidos vêm com colunas da direita em `NULL`.

### RIGHT / FULL OUTER JOIN

- `RIGHT JOIN` — espelho do left (raro; reescreva como left trocando a ordem).
- `FULL OUTER JOIN` — tudo dos dois lados; o que não casa vem com `NULL` no lado
  faltante. Útil para reconciliar dois conjuntos.

```text
A INNER B : ∩          A LEFT B : A + (A∩B)
A FULL  B : A ∪ B      A RIGHT B: B + (A∩B)
```

### CROSS JOIN — produto cartesiano

```sql
SELECT * FROM datas CROSS JOIN produtos;   -- toda combinação (cuidado: explode!)
```

Útil para gerar grades (ex.: todas as datas × todos os produtos para preencher
lacunas). Perigoso por acidente — sem condição de join, você multiplica tudo.

## Encontrar não-correspondências (anti-join)

"Clientes que nunca compraram":

```sql
SELECT c.*
FROM clientes c
LEFT JOIN pedidos p ON p.cliente_id = c.id
WHERE p.id IS NULL;             -- padrão anti-join via LEFT JOIN + IS NULL
```

Ou com `NOT EXISTS` (ver [subqueries](../04-subqueries-ctes/README.md)), geralmente
mais claro e seguro com NULLs.

## Semi-join (existência)

"Clientes que têm ao menos um pedido pago" — sem trazer os pedidos:

```sql
SELECT c.*
FROM clientes c
WHERE EXISTS (SELECT 1 FROM pedidos p
              WHERE p.cliente_id = c.id AND p.status = 'pago');
```

## Self-join — tabela consigo mesma

```sql
-- encontrar funcionários e seus gerentes na mesma tabela
SELECT e.nome AS funcionario, g.nome AS gerente
FROM funcionarios e
LEFT JOIN funcionarios g ON g.id = e.gerente_id;
```

## JOINs com múltiplas tabelas

```sql
SELECT p.id, c.nome, i.produto, i.qtd
FROM pedidos p
JOIN clientes c ON c.id = p.cliente_id
JOIN itens i    ON i.pedido_id = p.id
WHERE p.status = 'pago';
```

## O perigo nº 1: fan-out (join que multiplica linhas)

Se a condição de join não é 1:1, as linhas se **multiplicam**. Join de `pedidos`
(1) com `itens` (N) produz uma linha por item — se você então `SUM(p.valor)`, o valor
do pedido é **contado várias vezes** (uma por item). Esse é o bug silencioso mais
comum em analytics.

```sql
-- ERRADO: valor do pedido inflado pelo nº de itens
SELECT c.uf, SUM(p.valor)
FROM pedidos p JOIN itens i ON i.pedido_id = p.id
GROUP BY c.uf;
```

Soluções: agregue antes de juntar (agregue `itens` por pedido numa CTE), ou use
`COUNT(DISTINCT p.id)`, ou garanta a granularidade correta. **Sempre verifique a
cardinalidade** (`1:1`, `1:N`, `N:M`) antes de juntar e agregar.

## Como o banco executa um JOIN (noção)

O planejador escolhe o algoritmo conforme tamanhos e índices (ver
[query planning](../10-query-planning-explain/README.md)):

- **Nested loop** — bom para conjuntos pequenos / com índice na condição.
- **Hash join** — bom para grandes volumes sem ordenação.
- **Merge join** — bom quando ambos já estão ordenados pela chave.

Em sistemas distribuídos, joins exigem **shuffle** (mover dados entre nós) — caríssimo
— por isso existem *broadcast joins* para tabelas pequenas (ver
[Spark joins](../../16-distributed-processing/04-distributed-joins-skew/README.md)).

## Erros comuns

- Esquecer a condição `ON` → vira produto cartesiano.
- `fan-out`: somar após um join 1:N e inflar valores.
- Filtrar a tabela direita de um `LEFT JOIN` no `WHERE` (vira `INNER` sem querer —
  coloque a condição no `ON`).
- `NOT IN` com nulos (ver [select/NULL](../01-select-filtering/README.md)); prefira
  `NOT EXISTS`.

## Boas práticas

- Qualifique colunas com alias de tabela (`p.id`, `c.nome`).
- Declare o tipo de join explicitamente (`INNER JOIN`, não vírgula).
- Verifique cardinalidade antes de agregar.
- Condições de filtro da tabela "opcional" no `ON`, não no `WHERE`, em outer joins.

## Relação com outros conceitos

- Depende da [modelagem](../../07-data-modeling/README.md) (chaves/relacionamentos) e
  [constraints](../09-constraints/README.md).
- Performance via [índices](../07-indexes/README.md) e
  [planejamento](../10-query-planning-explain/README.md).
- Em escala: [distributed joins](../../16-distributed-processing/04-distributed-joins-skew/README.md).

## Exercícios

1. Liste todos os clientes e sua receita total (incluindo os que nunca compraram).
2. Encontre clientes que nunca fizeram um pedido (anti-join) de duas formas.
3. Reproduza um bug de *fan-out* somando valores após `pedidos ⋈ itens` e corrija
   agregando os itens antes.
4. Use um self-join para listar funcionários e seus gerentes.

## Referências

- Documentação do PostgreSQL — "Joins Between Tables".
- Winand, M. *SQL Performance Explained* — joins e índices.
