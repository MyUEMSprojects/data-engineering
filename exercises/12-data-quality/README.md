# Exercícios — Módulo 12: Qualidade de dados

Teoria em [12-data-quality](../../12-data-quality/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Dimensões de qualidade

Associe cada problema à dimensão: (a) CPF com 10 dígitos; (b) o mesmo cliente em duas linhas; (c) pedido de ontem que ainda não chegou; (d) `status` = "paid" no CRM e "pending" no financeiro.

<details><summary>Gabarito</summary>

(a) **Validade**. (b) **Unicidade**. (c) **Atualidade/completude** (frescor). (d) **Consistência**. Outras: acurácia, integridade referencial. Ver [dimensões](../../12-data-quality/01-dimensions-of-quality/README.md).
</details>

## 2. 🟢 SQL — Três testes clássicos

Escreva consultas que **retornam linhas quando há problema**: (a) `order_id` duplicado; (b) `customer_id` de `orders` inexistente em `customers`; (c) `amount` negativo.

<details><summary>Gabarito</summary>

```sql
SELECT order_id, COUNT(*) FROM orders GROUP BY order_id HAVING COUNT(*) > 1;                         -- unique
SELECT o.* FROM orders o LEFT JOIN customers c USING (customer_id) WHERE c.customer_id IS NULL;      -- relationships
SELECT * FROM orders WHERE amount < 0;                                                               -- validade
```

É o formato dos *singular tests* do dbt: **teste = consulta que deve retornar 0 linhas**. Ver [dbt tests](../../12-data-quality/06-dbt-tests/README.md).
</details>

## 3. 🔵 Implementação — Hard × soft

Classifique como **hard** (bloqueia) ou **soft** (avisa): chave duplicada; coluna opcional com 15% de nulos (era 2%); lote vazio; média de `amount` 4× o normal. Justifique.

<details><summary>Gabarito</summary>

**Hard:** chave duplicada (corrompe junções) e lote vazio (publicar "nada" é pior que atrasar). **Soft:** nulos em coluna opcional e mudança de média — podem ser legítimos (campanha, mudança de produto): avise, investigue. Se a confiança aumentar, promova para hard. Implementado no [Projeto 04](../../projects/04-data-quality/README.md).
</details>

## 4. 🔵 Debugging — O alerta que nunca para

Um monitor de volume usa "média ± 3 desvios padrão" dos últimos 30 dias e dispara toda segunda-feira. Por quê e como melhorar?

<details><summary>Gabarito</summary>

**Sazonalidade semanal**: segunda tem volume diferente e a média global não sabe disso. Compare com o **mesmo dia da semana** (baseline sazonal), use estatística **robusta** (mediana/MAD) para não ser distorcida por outliers e exija **histórico mínimo** antes de alertar. Ver [detecção de anomalias](../../12-data-quality/07-anomaly-detection/README.md).
</details>

## 5. 🟣 Arquitetura — Onde colocar a validação

Compare validar **na origem**, **na ingestão** e **na transformação**. Onde cada tipo de regra deve viver?

<details><summary>Gabarito</summary>

**Origem:** contrato/constraints do produtor (previne). **Ingestão (gate):** schema, tipos, volume, frescor — decide **bloquear/quarentenar** antes de poluir o lake. **Transformação:** regras de negócio e integridade entre tabelas (dbt tests). Defesa em profundidade: quanto mais cedo, mais barato corrigir; mas só quem conhece a regra de negócio a valida bem. Ver [contratos](../../12-data-quality/02-data-contracts/README.md).
</details>

## 6. 🟣 Implementação — Quarentena sem perder nada

Implemente `split(rows)` que devolve `(válidas, rejeitadas)` onde cada rejeitada carrega o **motivo**, e escreva a propriedade que **sempre** deve valer.

<details><summary>Gabarito</summary>

```python
def split(rows, validate):
    ok, bad = [], []
    for r in rows:
        reason = validate(r)          # None = válida
        (bad if reason else ok).append({**r, "_reason": reason} if reason else r)
    assert len(ok) + len(bad) == len(rows)   # conservação: nada some
    return ok, bad
```

Propriedade: **`válidas + rejeitadas = lidas`**. Teste com *property-based testing* (Hypothesis) e entradas aleatórias. Ver [expectation testing](../../12-data-quality/04-expectation-testing/README.md).
</details>
