# Exercícios — Módulo 14: Data Lake

Teoria em [14-data-lake](../../14-data-lake/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Medalhão

O que guarda cada camada **bronze, silver e gold** e quem normalmente as consome?

<details><summary>Gabarito</summary>

**Bronze:** dado **cru**, imutável, como chegou (reprocessável). **Silver:** limpo, tipado, deduplicado, conformado. **Gold:** modelos de negócio/agregações prontos (BI, ML). Engenharia de dados trabalha nas duas primeiras; analistas/cientistas consomem silver/gold. Ver [medalhão](../../14-data-lake/03-medallion-architecture/README.md) e o [Projeto 05](../../projects/05-data-lake/README.md).
</details>

## 2. 🟢 Conceitual — Pântano de dados

Cite **três** sintomas de um *data swamp* e uma prática que previne cada um.

<details><summary>Gabarito</summary>

(1) Ninguém sabe o que há nas pastas → **catálogo/metadados** e convenção de nomes. (2) Dados duplicados/sem dono → **ownership** e política de ciclo de vida. (3) Dados sem qualidade/schema → **gates de qualidade** e contratos. Ver [metadados](../../14-data-lake/07-metadata/README.md).
</details>

## 3. 🔵 Implementação — Estratégia de partição

Eventos de 50 GB/dia, consultados quase sempre por **data** e às vezes por `country` (30 valores). Proponha o layout de pastas e justifique por que **não** particionar por `user_id`.

<details><summary>Gabarito</summary>

`events/dt=2024-03-01/` (data primeiro), opcionalmente `country=BR/` se filtros por país forem comuns e cada partição ficar ≥ ~128 MB–1 GB. **Nunca `user_id`**: alta cardinalidade ⇒ milhões de diretórios/arquivos minúsculos (lentidão de listagem, overhead). Regra: partições **grandes e em número moderado**. Ver [particionamento](../../14-data-lake/05-partitioning/README.md).
</details>

## 4. 🔵 Debugging — Consulta lenta com muitos arquivos

Uma tabela de 20 GB tem 400 mil arquivos de ~50 KB. A consulta leva minutos. Explique e corrija.

<details><summary>Gabarito</summary>

**Problema dos arquivos pequenos:** listagem e abertura de cada objeto (latência por requisição ao object storage) dominam o tempo. Corrija com **compactação** (reescrever em arquivos de 128–512 MB) — `OPTIMIZE` em Delta/Iceberg ou job de *compaction* — e ajuste a ingestão (lotes maiores). Ver [arquivos pequenos](../../14-data-lake/06-small-files-compaction/README.md) e o experimento no [Projeto 05](../../projects/05-data-lake/README.md).
</details>

## 5. 🟣 Arquitetura — Schema on read × on write

Compare as abordagens e diga em qual camada do medalhão cada uma faz mais sentido.

<details><summary>Gabarito</summary>

**Schema-on-read** (bronze): aceita qualquer coisa, interpreta na leitura — flexível, mas empurra o erro para o consumidor. **Schema-on-write** (silver/gold): valida e tipa na gravação — erros aparecem cedo e o consumo é confiável. Combine: bronze flexível + silver/gold com schema forçado. Ver [schema on read/write](../../14-data-lake/04-schema-on-read-write/README.md).
</details>

## 6. 🟣 Implementação — Idempotência na bronze

Projete o nome dos arquivos da bronze para que **reingerir o mesmo lote** seja um *no-op* e dois lotes diferentes nunca colidam.

<details><summary>Gabarito</summary>

Nomeie pelo **hash do conteúdo**: `bronze/orders/ingest_date=2024-03-01/batch-<sha256[:12]>.jsonl`. Mesmo conteúdo ⇒ mesmo nome (`if exists: skip`); conteúdo diferente ⇒ nome diferente (imutabilidade). Implementado em [`bronze.py`](../../projects/05-data-lake/src/lake/bronze.py).
</details>
