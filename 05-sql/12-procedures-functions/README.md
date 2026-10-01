# Procedures e functions

> 🔵 Core · Parte de [05 — SQL](../README.md)

## O que é

- **Function (UDF)** — rotina que recebe parâmetros e **retorna um valor** (escalar,
  linha ou tabela); pode ser usada dentro de queries.
- **Stored procedure** — rotina executada com `CALL`, voltada a **efeitos** (operações,
  controle de transação); não retorna valor para uso em `SELECT`.

Ambas guardam lógica **dentro do banco**, em linguagens como SQL puro ou PL/pgSQL
(Postgres).

## Por que (e por que com cautela) usar

Lógica no banco pode ser útil (encapsular regras, reduzir *round-trips*, operar perto
dos dados), mas tem custos: é mais difícil de versionar, testar, revisar e portar que
código de aplicação. Em **Data Engineering moderno**, boa parte da lógica de
transformação migrou para [dbt](../../28-dbt/README.md)/Spark (versionado em Git,
testável) — então use procedures/functions com parcimônia e critério.

## Functions

### SQL function (simples)

```sql
CREATE FUNCTION valor_com_imposto(valor numeric, taxa numeric DEFAULT 0.1)
RETURNS numeric
LANGUAGE sql IMMUTABLE AS $$
    SELECT valor * (1 + taxa);
$$;

SELECT valor_com_imposto(100);          -- 110
SELECT id, valor_com_imposto(valor) FROM pedidos;
```

### PL/pgSQL (com lógica procedural)

```sql
CREATE FUNCTION classifica_cliente(total numeric)
RETURNS text
LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    IF total >= 10000 THEN RETURN 'vip';
    ELSIF total >= 1000 THEN RETURN 'regular';
    ELSE RETURN 'novo';
    END IF;
END;
$$;
```

### Table function (retorna conjunto)

```sql
CREATE FUNCTION pedidos_do_cliente(p_cliente bigint)
RETURNS TABLE (id bigint, valor numeric)
LANGUAGE sql STABLE AS $$
    SELECT id, valor FROM pedidos WHERE cliente_id = p_cliente;
$$;

SELECT * FROM pedidos_do_cliente(42);
```

## Volatilidade (importante para performance e correção)

Declare corretamente — o planejador usa isso para otimizar/cachear:

- **IMMUTABLE** — mesma entrada → mesma saída, sem acessar o banco (ex.: cálculo puro).
- **STABLE** — não muda dentro de uma query (pode ler o banco, mas não escreve).
- **VOLATILE** (default) — pode mudar a cada chamada (ex.: `random()`, `now()`, escrita).

Marcar errado (ex.: VOLATILE quando poderia ser IMMUTABLE) impede otimizações; marcar
IMMUTABLE algo que não é causa resultados errados.

## Stored procedures

```sql
CREATE PROCEDURE arquivar_pedidos_antigos(p_dias int)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO pedidos_arquivo SELECT * FROM pedidos
      WHERE criado_em < now() - make_interval(days => p_dias);
    DELETE FROM pedidos WHERE criado_em < now() - make_interval(days => p_dias);
    COMMIT;                     -- procedures podem controlar transações
END;
$$;

CALL arquivar_pedidos_antigos(365);
```

Diferente de functions, procedures (Postgres 11+) podem **gerenciar transações**
(`COMMIT`/`ROLLBACK`) internamente — útil para processar em lotes.

## Triggers (menção)

Funções associadas a eventos de tabela (`BEFORE/AFTER INSERT/UPDATE/DELETE`). Usos:
auditoria, `updated_at` automático, validações complexas, captura para
[CDC](../../09-etl-elt/06-cdc/README.md). Cuidado: triggers escondem lógica e podem
surpreender — documente bem.

```sql
CREATE TRIGGER trg_set_updated
BEFORE UPDATE ON pedidos
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

## Function vs View vs dbt model

| | UDF | [View](../06-views-materialized-views/README.md) | [dbt model](../../28-dbt/README.md) |
| --- | --- | --- | --- |
| Encapsula | lógica paramétrica | consulta nomeada | transformação versionada |
| Versionável em Git | difícil | difícil | sim |
| Testável | difícil | difícil | sim (testes de dados) |
| Portável | não (dialeto) | parcial | sim (Jinja/adaptadores) |

## Quando usar / quando evitar

- **Use** para: regras simples reutilizadas em muitas queries, operações próximas aos
  dados com muito I/O, validações/auditoria via triggers.
- **Evite** para: lógica de transformação complexa do pipeline (prefira dbt/Spark,
  versionado e testado), lógica de negócio crítica que precisa de testes/revisão
  rigorosos.

## Erros comuns

- Volatilidade mal declarada (perde otimização ou gera resultado errado).
- Lógica de negócio crítica enterrada em procedures sem testes nem versionamento.
- Triggers "mágicos" que causam efeitos inesperados.
- UDFs lentas chamadas linha a linha em tabelas grandes (sem *inlining*).
- Assumir portabilidade — PL/pgSQL não roda em outro banco.

## Boas práticas

- Declare volatilidade corretamente.
- Mantenha funções pequenas e puras quando possível.
- Versione o DDL (migrações) em Git; teste o comportamento.
- Prefira dbt/Spark para transformação; reserve o banco para o que faz sentido ali.

## Relação com outros conceitos

- Alternativas modernas: [dbt](../../28-dbt/README.md),
  [Spark](../../16-distributed-processing/README.md),
  [views/MVs](../06-views-materialized-views/README.md).
- Triggers conectam a [CDC](../../09-etl-elt/06-cdc/README.md) e auditoria
  ([governance](../../25-data-governance/README.md)).

## Exercícios

1. Escreva uma SQL function `IMMUTABLE` de cálculo e use-a numa query.
2. Crie uma table function que retorna pedidos de um cliente e consulte-a.
3. Escreva uma procedure que arquiva e apaga registros antigos em lote, controlando a
   transação.
4. Argumente, para um caso real, por que mover uma transformação de uma procedure para
   um modelo dbt melhora testabilidade e versionamento.

## Referências

- Documentação do PostgreSQL — "User-Defined Functions", "Procedures", "PL/pgSQL",
  "Triggers".
