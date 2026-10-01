# Vector databases

> 🟣 Advanced · Parte de [30 — Advanced](../README.md) · *Natureza: tendência/tecnologia nova (IA)*

## O que é

**Vector databases** armazenam e consultam **vetores de alta dimensão (embeddings)** com **busca por
similaridade**: dado um vetor de consulta, retornam os **k mais próximos** (nearest neighbors). São a
infraestrutura de **busca semântica**, **RAG** (Retrieval-Augmented Generation), **recomendação** e
detecção de similaridade/duplicatas em dados não estruturados (texto, imagens, áudio).

> Estado do campo: **em rápida evolução** (produtos, benchmarks e boas práticas mudam todo semestre).
> Aprenda os **conceitos estáveis** (embeddings, métricas, ANN) e confirme detalhes de produto na
> documentação atual.

## Embeddings (o conceito base)

Um **embedding** é uma **representação numérica densa** (vetor de centenas/milhares de floats) de um item
(frase, documento, imagem, usuário, produto) produzida por um **modelo** (ex.: modelos de linguagem/visão).
Itens **semanticamente parecidos** ficam **próximos** no espaço vetorial.

```text
"como redefinir minha senha" ≈ "esqueci a senha, o que fazer?"   (vetores próximos)
"como redefinir minha senha" ≠ "política de reembolso"            (vetores distantes)
```

### Métricas de similaridade/distância

- **Cosseno** (ângulo; comum p/ texto), **produto interno (dot)**, **distância euclidiana (L2)**.
- Normalizar vetores torna cosseno ≈ dot product. A métrica deve **corresponder** à usada no treino do modelo.

## O problema: busca exata é cara

Comparar a consulta com **todos** os N vetores é **O(N·d)** — inviável em milhões/bilhões. Solução:
**Approximate Nearest Neighbor (ANN)** — **troca um pouco de precisão (recall) por muita velocidade**.

### Índices ANN principais

| Índice | Ideia | Trade-offs |
| --- | --- | --- |
| **HNSW** (Hierarchical Navigable Small World) | grafo em camadas navegável | **alto recall e baixa latência**; memória alta; construção custosa |
| **IVF / IVF-PQ** (inverted file + product quantization) | agrupa em clusters (centroides); **PQ** comprime vetores | menos memória; recall depende de `nprobe`/compressão |
| **Flat (brute force)** | comparação exata | exato, lento; ok em poucos vetores |
| **DiskANN / SPANN** | índices otimizados para **disco/SSD** | escala a bilhões com menos RAM |
| **LSH** | hashing sensível à localidade | simples; geralmente menos usado hoje |

Parâmetros típicos: `M`, `efConstruction`, `efSearch` (HNSW); `nlist`, `nprobe` (IVF) — controlam o
trade-off **recall × latência × memória**.

## Arquitetura de um vector DB

```text
Dados (texto/imagem) ─► modelo de embedding ─► vetor + metadados ─► índice ANN (HNSW/IVF) + armazenamento
Consulta ─► embedding ─► ANN search (+ filtros por metadados) ─► top-k ─► (reranking) ─► aplicação / LLM
```

Capacidades relevantes: **filtros por metadados** (busca vetorial **+** filtros estruturados: `categoria=X`,
`tenant=Y`), **busca híbrida** (vetorial + keyword/BM25), **upserts/deletes**, **namespaces/multi-tenancy**,
persistência, replicação/sharding, quantização.

## Opções (panorama, não endosso)

| Tipo | Exemplos | Notas |
| --- | --- | --- |
| **Extensão em banco existente** | **pgvector** (Postgres), OpenSearch/Elasticsearch k-NN, MongoDB Atlas Vector Search, Redis (vector), Snowflake/BigQuery/Databricks vector search | **aproveita infra, SQL, ACID e governança existentes**; ótimo ponto de partida |
| **Vector DBs nativos** | Milvus, Qdrant, Weaviate, Pinecone (gerenciado), Chroma (dev) | escala/otimizações específicas, recursos de vetor mais ricos |
| **Bibliotecas** | FAISS, ScaNN, hnswlib, Annoy | índice embutido (sem servidor); base de outros sistemas |

> Dica pragmática: para **centenas de milhares a poucos milhões** de vetores, **pgvector** (ou a extensão do
> seu warehouse/search) costuma bastar e **simplifica** arquitetura e governança. Considere DB dedicado em
> **escala/latência/recursos** que justifiquem.

## Casos de uso em Data Engineering

- **RAG**: indexar documentos da empresa em chunks → recuperar contexto relevante para um LLM responder
  ([DE + ML](../../31-data-engineering-and-ml/README.md)).
- **Busca semântica** sobre catálogo de dados/documentos/tickets.
- **Recomendação** e "itens similares" (embeddings de usuários/produtos).
- **Deduplicação/entity resolution** semântica ([dedupe](../../09-etl-elt/09-deduplication/README.md)).
- **Detecção de anomalias/fraude** por distância em espaço de embeddings.
- **Feature/embedding stores** para ML online ([feature stores](../../31-data-engineering-and-ml/03-feature-stores-online-offline/README.md)).

## O trabalho do Data Engineer (a parte que é "dados" de verdade)

A qualidade de um sistema vetorial depende **mais do pipeline de dados** do que do banco:

```text
Fontes ─► extração/parsing ─► limpeza ─► CHUNKING ─► EMBEDDING (batch/stream) ─► upsert no vector DB (+ metadados) ─► monitoramento
                                                       │
                              reindexação quando muda modelo/chunking (versão do embedding!)
```

- **Ingestão e atualização**: pipelines idempotentes para novos/alterados/**excluídos** documentos
  (sincronização incremental — [CDC](../01-cdc-debezium/README.md), [incremental](../../09-etl-elt/05-full-vs-incremental/README.md)).
- **Chunking** (tamanho/overlap/estrutura) impacta fortemente a relevância.
- **Versionamento de embeddings**: trocar o **modelo** muda o espaço vetorial → **reindexar tudo**;
  mantenha `embedding_model_version` nos metadados.
- **Custo/latência de embedding** (chamadas a APIs/GPU) — batch, cache, rate limits
  ([HTTP clients](../../04-python-for-data-engineering/08-http-clients/README.md)).
- **Metadados e filtros** bem modelados; **multi-tenancy** e **controle de acesso** (não vazar documentos
  entre usuários — [acesso](../../25-data-governance/05-access-control-classification/README.md),
  [segurança](../../26-security/README.md)).
- **Qualidade/avaliação**: medir **recall/precisão** do retrieval (conjuntos de avaliação), monitorar
  *drift* ([drift](../../31-data-engineering-and-ml/README.md)).
- **Privacidade**: embeddings de dados pessoais continuam sendo dado pessoal potencialmente reidentificável
  ([LGPD](../../26-security/08-lgpd/README.md)); exclusão deve remover vetores.

## Trade-offs

- **Recall × latência × memória/custo** (ANN é aproximado).
- **Filtros + ANN** podem degradar recall/latência (depende da engine; pré/pós-filtragem).
- **Atualizações/deleções** frequentes custam (índices de grafo).
- Memória: HNSW em RAM; quantização reduz com perda de precisão.
- **Acoplamento ao modelo de embedding** (reindexação ao trocar).
- Busca vetorial **não substitui** busca lexical/estruturada — **híbrida** costuma ganhar.

## Erros comuns

- Escolher DB dedicado sem necessidade (pgvector bastaria).
- Chunking ruim / sem avaliação de retrieval ("RAG que alucina").
- Misturar modelos/versões de embedding no mesmo índice.
- Esquecer deleções/atualizações (índice desatualizado, dados excluídos ainda recuperáveis).
- Métrica de distância diferente da do modelo.
- Ignorar controle de acesso por documento/tenant.
- Sem métricas de qualidade do retrieval.

## Boas práticas

- Comece simples (pgvector/extensão existente); meça recall/latência; escale se preciso.
- Pipeline de embedding **idempotente, versionado e incremental**; guarde `model_version` e `source_id`.
- Busca **híbrida** + filtros; reranking quando valer; avaliação contínua com conjuntos de teste.
- Controle de acesso e privacidade desde o desenho; observabilidade do pipeline e do índice.

## Relação com outros conceitos

- [DE + ML](../../31-data-engineering-and-ml/README.md), [feature stores](../../31-data-engineering-and-ml/03-feature-stores-online-offline/README.md),
  [pipelines incrementais](../../09-etl-elt/05-full-vs-incremental/README.md),
  [Postgres](../../06-databases/02-postgresql/README.md), [LGPD](../../26-security/08-lgpd/README.md).

## Exercícios

1. Explique embeddings, similaridade por cosseno e por que ANN troca precisão por velocidade.
2. Desenhe o pipeline de ingestão de documentos para um RAG (parsing → chunking → embedding → upsert) com
   atualização incremental e exclusão.
3. Compare pgvector e um vector DB dedicado para 2M vs 2B de vetores.
4. Como você versionaria e migraria embeddings ao trocar de modelo? E tratar controle de acesso por tenant?

## Referências

- Documentação de pgvector, Milvus, Qdrant, Weaviate, FAISS; Malkov & Yashunin, "HNSW" (2016/2018);
  Jégou et al., "Product Quantization"; Lewis et al., "Retrieval-Augmented Generation" (2020).
