# Catálogos, discovery e impact analysis

> 🟣 Production · Parte de [27 — Catalog & Metadata](../README.md)

## O que é

Um **catálogo de dados** é o **inventário pesquisável** dos ativos de dados da organização, enriquecido
com [metadados](../01-metadata-types/README.md) e [lineage](../02-lineage-column-lineage/README.md).
Habilita **discovery** (descoberta) — achar e entender dados — e **impact analysis** (análise de impacto)
— saber o que muda se algo mudar.

## Por que existe

Sem catálogo, analistas **não sabem o que existe**, recriam tabelas, usam a errada, e dependem de "quem
conhece alguém". Resultado: tempo perdido, métricas divergentes, risco de uso indevido de dados sensíveis.
O catálogo é o "Google + Wikipédia + mapa" dos dados.

## Capacidades

### 1. Discovery (descoberta)
- **Busca** por nome, descrição, coluna, tag, domínio, dono (full-text + facetas).
- **Navegação** por domínio/produto/camada; **ranking** por uso/popularidade/certificação.
- **Perfil do ativo**: descrição, schema, amostra (com mascaramento), estatísticas, frescor, qualidade,
  dono, lineage, consultas de exemplo, como pedir acesso.
- **Sinais de confiança**: selo "certificado", testes passando, SLA cumprido, uso recente.
- **Integração no fluxo**: link do dashboard/IDE/dbt para o catálogo; busca embutida em notebooks/BI.

### 2. Impact analysis (análise de impacto)
Usa o **lineage a jusante** (downstream) para responder: *"se eu alterar/descontinuar X, o que quebra?"*

- Lista **tabelas, colunas, dashboards, modelos de ML e donos** afetados.
- Antes de **renomear coluna, mudar tipo/semântica, depreciar tabela, migrar pipeline**.
- Integra ao **PR/CI**: o PR que altera um modelo mostra os consumidores e **notifica os donos**
  ([CI/CD](../../23-cicd-dataops/README.md), [contratos](../../29-data-contracts/README.md)).
- **Análise reversa (upstream)** — raiz de causa de um número errado.

### 3. Governança acionável
- **Ownership**, **classificação/PII**, **políticas** (mascaramento/acesso por tag), **retenção**,
  **glossário** de negócio ligado aos ativos ([governança](../../25-data-governance/README.md)).
- **Fluxo de pedido de acesso** a partir do catálogo (aprovação pelo dono).
- **Certificação** e ciclo de vida (rascunho → certificado → depreciado).

### 4. Colaboração
Comentários, Q&A, tags, favoritos, documentação compartilhada ([metadados sociais](../01-metadata-types/README.md)).

### 5. Qualidade e observabilidade
Exibe resultados de testes ([dbt/GX](../../12-data-quality/README.md)), frescor/SLO
([observability](../../24-observability/06-data-freshness/README.md)), anomalias e incidentes por ativo.

## Arquitetura típica de um catálogo

```text
Conectores/ingestão (pull) ─┐   dbt · warehouse · lake · Airflow · BI · Kafka · qualidade · OpenLineage (push)
                            ▼
                  Plano de metadados (API + armazenamento de grafo/relacional)
                  ├─ índice de busca (Elasticsearch/OpenSearch)
                  ├─ lineage (grafo)
                  └─ políticas/tags/owners
                            ▼
              UI de discovery · APIs/SDK · webhooks (ações: alertas, bloqueios, CI)
```

Metadados entram por **ingestão agendada** (pull) e/ou **eventos em tempo real** (push, Kafka/OpenLineage);
saem por **UI, API, SDK e integrações** (Slack, CI, IDE).

## Como adotar com sucesso

1. **Comece pequeno e valioso**: domínio/datasets **tier-1**, com donos engajados — não tente catalogar tudo.
2. **Automatize** a ingestão (técnico/operacional/lineage); humanos curam o **negócio** dos ativos críticos.
3. **Exija o mínimo**: dono + descrição para publicar/certificar (via dbt/CI).
4. **Meça adoção e saúde**: buscas, usuários ativos, % de ativos com dono/descrição/classificação, buscas
   sem resultado, tempo para descobrir dado.
5. **Integre ao fluxo** (dbt, BI, Slack, IDE) — catálogo isolado não é aberto.
6. **Mantenha**: remova obsoleto; revise donos; reconcilie com a realidade.

## Anti-padrões

- **"Catálogo-cemitério"**: ferramenta cara, metadados desatualizados, ninguém usa.
- Catalogar **tudo** de uma vez (ruído) sem priorizar valor/risco.
- Depender de preenchimento manual sem incentivo/automação.
- Catálogo desconectado do código/pipelines (diverge da realidade).
- Sem ownership dos metadados.

## Discovery vs search em BI vs data marketplace

- **Catálogo** — governança e descoberta de ativos técnicos/negócio.
- **Marketplace/portal de data products** — camada de consumo "self-service" sobre catálogo (inclui SLAs,
  contratos, acesso) no [data mesh](../../30-advanced/03-data-mesh/README.md).
- **Semantic layer/métricas** (dbt Semantic Layer, Looker, Cube) — definições de métrica consistentes,
  complementar ao catálogo.

## Erros comuns

- Catálogo sem curadoria → resultados de busca poluídos (duplicatas, tabelas de teste).
- Sem sinais de confiança → analistas não sabem qual tabela usar.
- Impact analysis só table-level (perde colunas/dashboards).
- Não ligar ao PR/CI (mudanças quebram consumidores sem aviso).
- Medir só "ativos catalogados", não adoção/valor.

## Boas práticas

- Foco em tier-1 e domínios prioritários; ingestão automática; mínimo obrigatório (dono + descrição).
- Certificação e sinais de confiança visíveis; amostras mascaradas.
- Impact analysis integrada ao CI; notificação aos donos.
- Métricas de adoção/saúde e revisão periódica.

## Relação com outros conceitos

- [Tipos de metadados](../01-metadata-types/README.md), [lineage](../02-lineage-column-lineage/README.md),
  [ferramentas](../04-tools/README.md), [governança](../../25-data-governance/README.md),
  [data contracts](../../29-data-contracts/README.md), [data mesh](../../30-advanced/03-data-mesh/README.md).

## Exercícios

1. Descreva a jornada de um analista que precisa de "receita líquida por região" usando o catálogo.
2. Faça uma análise de impacto de depreciar a coluna `clientes.segmento_antigo`.
3. Defina 6 métricas de adoção/saúde do catálogo.
4. Planeje o rollout do catálogo em 3 fases para uma empresa com 2 mil tabelas.

## Referências

- Documentação de DataHub, OpenMetadata, Amundsen; Eryurek et al., *Data Governance: The Definitive Guide*;
  DAMA-DMBOK (Metadata).
