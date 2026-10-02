# Full vs incremental

> 🔵 Pipelines · Parte de [09 — ETL/ELT](../README.md)

## O que é

Duas estratégias de carga/extração:

- **Full load** — processa **todos** os dados toda vez (extrai a tabela inteira, reconstrói
  o destino do zero).
- **Incremental load** — processa **só o que mudou** desde a última execução (novos/
  alterados).

É uma das decisões de design mais frequentes e impactantes em pipelines.

## O trade-off central

```text
Full:         simples e sempre correto, mas lento e caro (reprocessa tudo)
Incremental:  rápido e barato, mas complexo (precisa saber "o que mudou" e lidar com estado)
```

| Aspecto | Full | Incremental |
| --- | --- | --- |
| Simplicidade | alta | menor (gerencia estado/marca) |
| Custo/tempo | alto (cresce com o total) | baixo (proporcional ao delta) |
| Correção | trivial | exige cuidado (dados tardios, deletes) |
| Idempotência | fácil (overwrite total) | exige upsert/overwrite por partição |
| Escala | não escala | escala |

Regra prática: **full enquanto for barato; incremental quando o volume doer.**

## Como fazer incremental

### Por watermark (high-water mark)

Guarda a "marca" do último processado (um timestamp ou id crescente) e extrai o que está
acima dela.

```sql
SELECT * FROM pedidos WHERE updated_at > :ultima_marca ORDER BY updated_at;
-- ao fim, salve a nova marca = max(updated_at) processado
```

Requisitos: uma coluna **confiável e monotônica** (`updated_at`/`id`) que a fonte atualize
em **toda** mudança. Armadilhas:

- Se `updated_at` **não** muda em updates → você perde alterações.
- **Relógios/fuso** e registros com o mesmo timestamp na fronteira → use `>=` com dedupe, ou
  guarde id+timestamp.
- **Deletes** não aparecem (uma linha apagada não tem `updated_at` novo) → ver abaixo.

### Por partição de tempo

Reprocessa partições recentes (ex.: "reprocessa os últimos 3 dias todo dia") com overwrite
por partição — simples e robusto para dados que chegam atrasados.

### Por [CDC](../06-cdc/README.md)

Lê o log de mudanças da fonte (inclui **deletes**!) — a forma mais completa de incremental.
Ver [CDC](../06-cdc/README.md).

## O problema dos deletes

Incremental por watermark captura inserts e updates, mas **não** deletes (uma linha some
sem deixar rastro). Soluções:

- **Soft delete** na fonte (uma flag `deleted_at`) → vira um update capturável.
- **[CDC](../06-cdc/README.md)** → captura o evento de delete.
- **Reconciliação periódica** — um full ocasional para corrigir divergências.

## Dados tardios / fora de ordem

Dados podem chegar **depois** da janela em que deveriam (atraso de rede, correção
retroativa). Por isso é comum reprocessar uma **janela de segurança** (ex.: últimos N dias)
em vez de só "desde a última marca", garantindo que registros atrasados sejam capturados.

## Idempotência é obrigatória no incremental

Como você vai reexecutar/sobrepor janelas, a carga **precisa** ser idempotente (overwrite
por partição ou upsert — ver [loading](../04-loading/README.md) e
[idempotência](../07-idempotency-retries/README.md)). Caso contrário, reprocessar duplica.

## Padrão híbrido (muito comum)

- **Dimensões pequenas** → full (overwrite total; trivial e sempre correto).
- **Fatos/eventos grandes** → incremental (por data/CDC).
- **Full periódico de reconciliação** → corrige drifts do incremental (ex.: mensal).

## Em dbt

[dbt](../../28-dbt/README.md) formaliza isso com *materializations*:

- `table`/`view` → full a cada run.
- [`incremental`](../../28-dbt/08-incremental-models/README.md) → processa só o novo (com
  `is_incremental()` e uma estratégia de merge/insert), tipicamente com uma janela de
  *lookback*.

## Erros comuns

- Incremental com coluna de watermark que a fonte não atualiza em updates → perde mudanças.
- Ignorar deletes no incremental → destino com registros fantasmas.
- Não reprocessar janela de dados tardios → lacunas.
- Incremental sem idempotência → duplicação ao reexecutar.
- Full em tabela gigante quando incremental resolveria (custo/tempo).

## Boas práticas

- Full enquanto barato; mude para incremental ao escalar.
- Watermark confiável + janela de lookback para dados tardios.
- Trate deletes (soft delete/CDC) e faça reconciliação periódica.
- Garanta idempotência na carga; guarde a marca de forma durável.

## Relação com outros conceitos

- [CDC](../06-cdc/README.md), [idempotência](../07-idempotency-retries/README.md),
  [loading](../04-loading/README.md), [backfill](../08-backfill/README.md).
- [dbt incremental](../../28-dbt/08-incremental-models/README.md),
  [partitioning](../../14-data-lake/05-partitioning/README.md).

## Exercícios

1. Implemente extração incremental por `updated_at` com guarda de marca e janela de
   lookback de 2 dias.
2. Explique por que deletes somem no incremental por watermark e proponha 2 soluções.
3. Projete uma estratégia híbrida para um e-commerce (o que é full, o que é incremental).
4. Mostre por que incremental sem idempotência duplica ao reprocessar.

## Referências

- Reis & Housley, *Fundamentals of Data Engineering* — ingestão incremental.
- Documentação do dbt — incremental models.
