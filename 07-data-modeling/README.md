# 07 — Data Modeling

> 🔵 Nível 2 — Core · Pré: [05 — SQL](../05-sql/README.md),
> [06 — Databases](../06-databases/README.md) · Próximo:
> [08 — Data Formats](../08-data-formats/README.md)

Modelagem de dados é projetar **como os dados são estruturados** — tabelas, colunas,
chaves, relacionamentos — para servir a um propósito. É uma das habilidades mais
valiosas (e duradouras) do Data Engineer: um modelo bom torna consultas simples,
rápidas e corretas; um modelo ruim condena o projeto a *queries* monstruosas e números
errados. Ferramentas vêm e vão; um bom modelo dimensional de 1996 ainda funciona.

## Por que importa

- Define a performance e a clareza de toda a camada analítica.
- É a diferença entre um warehouse que o time entende e usa, e um "pântano" de tabelas.
- Modelar certo na origem (OLTP) e no destino (OLAP) são problemas **diferentes** — e
  este módulo cobre os dois.

## Tópicos

| # | Tópico | Conteúdo |
| --- | --- | --- |
| 01 | [Conceitual, lógico e físico](01-conceptual-logical-physical/README.md) | Os três níveis de modelagem |
| 02 | [Normalização e desnormalização](02-normalization-denormalization/README.md) | Formas normais e quando quebrá-las |
| 03 | [Modelagem OLTP vs OLAP](03-oltp-vs-olap-modeling/README.md) | Por que modelar diferente para cada carga |
| 04 | [Modelagem dimensional](04-dimensional-modeling/README.md) | Fatos, dimensões, grão (Kimball) |
| 05 | [Star schema](05-star-schema/README.md) | O esquema estrela |
| 06 | [Snowflake schema](06-snowflake-schema/README.md) | Dimensões normalizadas |
| 07 | [Fact tables](07-fact-tables/README.md) | Tipos de fato, aditividade, grão |
| 08 | [Dimension tables](08-dimension-tables/README.md) | Atributos, hierarquias, conformadas |
| 09 | [Surrogate vs natural keys](09-surrogate-natural-keys/README.md) | Escolha de chaves |
| 10 | [Slowly Changing Dimensions](10-slowly-changing-dimensions/README.md) | Histórico de dimensões (SCD) |
| 11 | [Data Vault](11-data-vault/README.md) | Hubs, links, satellites |

## Dependências internas

```text
Conceitual/lógico/físico ─► Normalização/desnormalização ─► OLTP vs OLAP modeling
                                                                    │
                                                                    ▼
                        Modelagem dimensional ─► Star schema ─► Snowflake schema
                                 │                     │
                                 ▼                     ▼
                 Fact tables + Dimension tables   Surrogate/natural keys ─► SCD
                                 │
                                 ▼
                             Data Vault (abordagem alternativa)
```

## Checkpoint

- [ ] Distinguir modelo conceitual, lógico e físico.
- [ ] Normalizar até 3NF e justificar quando desnormalizar.
- [ ] Explicar por que OLTP é normalizado e OLAP é dimensional.
- [ ] Projetar um star schema a partir de um processo de negócio (definindo o **grão**).
- [ ] Diferenciar tipos de fato (transacional, snapshot, acumulativo) e aditividade.
- [ ] Implementar SCD tipo 1 e tipo 2 com surrogate keys.
- [ ] Comparar Kimball (dimensional) e Data Vault, e quando usar cada.

## Referências do módulo

- Kimball, R.; Ross, M. *The Data Warehouse Toolkit*, 3ª ed. Wiley, 2013.
- Inmon, W. *Building the Data Warehouse*.
- Linstedt, D. *Building a Scalable Data Warehouse with Data Vault 2.0*.
