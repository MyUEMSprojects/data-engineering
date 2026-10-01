# Data Vault

> 🔵 Core · Parte de [07 — Data Modeling](../README.md)

## O que é

**Data Vault** (Dan Linstedt) é uma metodologia de modelagem para a **camada de
integração** de um data warehouse corporativo, projetada para **auditabilidade**,
**histórico completo** e **flexibilidade** diante de mudanças e múltiplas fontes. Separa o
modelo em três tipos de tabela: **Hubs**, **Links** e **Satellites**.

Não é um concorrente direto do [star schema](../05-star-schema/README.md): Data Vault
costuma ser a camada **intermediária** (raw/integração), da qual se derivam *marts*
dimensionais para consumo.

## Por que existe / que problema resolve

Modelos dimensionais são ótimos para **consumo**, mas podem ser trabalhosos de evoluir
quando há **muitas fontes**, **mudanças frequentes de schema** e requisitos rígidos de
**auditoria/compliance** (saber exatamente de onde e quando cada dado veio). Data Vault
ataca isso com um modelo altamente **modular, insert-only e rastreável**:

- Adicionar uma fonte/atributo = adicionar tabelas, **sem reestruturar** o existente.
- **Histórico total** (nada é atualizado/apagado — tudo é inserido com timestamp).
- **Linhagem e auditoria** embutidas (cada registro sabe sua origem e carga).

## Os três componentes

### Hub — as chaves de negócio

Armazena a lista de **chaves de negócio** únicas de uma entidade (ex.: todos os
`cliente_id`), com uma surrogate (hash) key, a data de carga e a fonte.

```text
hub_cliente(cliente_hk, cliente_id, load_date, record_source)
```

### Link — os relacionamentos

Representa **relacionamentos/associações** entre hubs (ex.: cliente fez pedido). É sempre
N:M e insert-only.

```text
link_pedido(pedido_hk, cliente_hk, produto_hk, load_date, record_source)
```

### Satellite — os atributos descritivos e seu histórico

Guarda os **atributos** (contexto) de um hub ou link, **versionados por tempo** (como um
[SCD2](../10-slowly-changing-dimensions/README.md) embutido). Toda mudança gera uma nova
linha.

```text
sat_cliente(cliente_hk, load_date, nome, regiao, segmento, hash_diff, record_source)
```

```text
         ┌────────────┐
         │ hub_cliente│───< sat_cliente (atributos + histórico)
         └─────┬──────┘
               │
         link_pedido ───< sat_pedido
               │
         ┌─────┴──────┐
         │ hub_produto│───< sat_produto
         └────────────┘
```

## Princípios-chave

- **Insert-only** — nunca se faz UPDATE/DELETE; tudo é inserção com `load_date` →
  auditoria e paralelismo de carga.
- **Separação de chaves, relacionamentos e contexto** — mudanças ficam isoladas (um novo
  atributo = novo satellite; uma nova relação = novo link).
- **Hash keys** — [surrogate keys](../09-surrogate-natural-keys/README.md) determinísticas
  por hash da chave de negócio → cargas paralelas/distribuídas sem coordenação.
- **`record_source`/`load_date`** em tudo — lineage por construção.

## A arquitetura em camadas (onde Data Vault se encaixa)

```text
Fontes ─► Staging ─► Raw Data Vault (hubs/links/sats) ─► Business Vault ─► Marts dimensionais (star) ─► BI
                      (integração, histórico, auditoria)                    (consumo)
```

Data Vault **não é consumido diretamente** por analistas (é verboso, muitos joins) — ele
alimenta *marts* dimensionais.

## Vantagens

- Altamente **flexível/escalável** a novas fontes e mudanças (adiciona, não reestrutura).
- **Histórico e auditoria completos** (compliance).
- Cargas **paralelizáveis** (insert-only + hash keys).
- Boa para ambientes com **muitas fontes heterogêneas**.

## Limitações / trade-offs

- **Complexidade e verbosidade** — muitas tabelas e joins; curva de aprendizado alta.
- **Não é para consumo direto** — exige a camada dimensional por cima (mais ETL).
- **Overkill** para projetos pequenos/simples (um star direto basta).
- Volume de dados maior (histórico de tudo).

## Quando usar / quando NÃO usar

- **Use** em warehouses corporativos grandes, com muitas fontes, mudança constante e
  requisitos fortes de auditoria/histórico.
- **NÃO use** em projetos pequenos/médios, times enxutos, ou quando um modelo dimensional
  direto (Kimball) já resolve — a complexidade não se paga.

## Data Vault vs Kimball vs Inmon

| | Data Vault | [Kimball](../04-dimensional-modeling/README.md) | Inmon |
| --- | --- | --- | --- |
| Papel | integração/raw auditável | consumo (marts) | EDW normalizado |
| Estrutura | hubs/links/sats | fato/dimensão | 3NF corporativo |
| Flexibilidade a mudanças | altíssima | média | média |
| Consumo direto | não | sim | não |
| Complexidade | alta | baixa/média | média/alta |

Comum: **Data Vault (integração) → Kimball (consumo)**.

## Erros comuns

- Adotar Data Vault por *hype* em um projeto que não precisa → complexidade enorme.
- Fazer analistas consumirem o Vault direto (em vez dos marts).
- Confundir Data Vault com modelo de consumo (ele é de integração).

## Boas práticas

- Use como camada de integração, com marts dimensionais por cima.
- Hash keys determinísticas; insert-only; `load_date`/`record_source` em tudo.
- Automatize a geração das tabelas (há frameworks: automate-dv para dbt, etc.).
- Avalie honestamente se o projeto **precisa** dessa robustez.

## Relação com outros conceitos

- Alimenta modelos [dimensionais](../04-dimensional-modeling/README.md)/
  [star](../05-star-schema/README.md).
- Satellites são [SCD2](../10-slowly-changing-dimensions/README.md) embutidos.
- Hash keys: [surrogate keys](../09-surrogate-natural-keys/README.md); lineage conecta a
  [governança](../../25-data-governance/README.md).

## Exercícios

1. Modele um mini Data Vault para "cliente faz pedido de produto" (hubs, link,
   satellites).
2. Explique por que o modelo ser insert-only melhora auditoria e paralelismo de carga.
3. Descreva o fluxo Raw Vault → marts dimensionais para consumo.
4. Argumente, para um projeto pequeno, por que Data Vault seria exagero.

## Referências

- Linstedt, D.; Olschimke, M. *Building a Scalable Data Warehouse with Data Vault 2.0*.
- datavaultalliance.com; projeto `automate-dv` (dbt).
