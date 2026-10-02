# Prefect

> 🔵 Pipelines · Parte de [11 — Orquestração](../README.md)

## O que é

**Prefect** é um orquestrador Python que prioriza simplicidade e flexibilidade: você escreve
código Python normal e o decora para torná-lo um **flow** orquestrado, com retries,
scheduling, logging e observabilidade. Destaca-se por lidar bem com **fluxos dinâmicos** (a
estrutura do pipeline pode depender de valores em runtime) e por uma curva de entrada suave.

## A filosofia: "seu código, orquestrado"

Enquanto o [Airflow](../02-airflow/README.md) pede que você estruture tudo como DAG estático
antecipadamente, o Prefect deixa você escrever Python quase comum e adicionar orquestração por
cima. O grafo pode ser **construído dinamicamente** durante a execução.

```python
from prefect import flow, task

@task(retries=3, retry_delay_seconds=10)
def extract(date: str) -> str:
    return extrair_para_raw(date)

@task
def transform(path: str) -> str:
    return transformar(path)

@flow(name="vendas-diarias")
def pipeline(date: str):
    raw = extract(date)
    out = transform(raw)
    load(out)       # idempotente

if __name__ == "__main__":
    pipeline("2024-01-15")
```

## Conceitos

| Conceito | O que é |
| --- | --- |
| **Flow** | o pipeline (uma função decorada `@flow`) |
| **Task** | unidade de trabalho (`@task`) com retries/cache |
| **Deployment** | como/onde/quando um flow roda (schedule, infra) |
| **Work pool / worker** | onde a execução acontece (processo, Docker, Kubernetes) |
| **Blocks** | configuração reutilizável (credenciais, storage) |
| **State** | estados ricos de tasks/flows (Completed, Failed, Retrying...) |

## Diferenciais

- **Dinamismo** — número de tarefas, branches e loops podem depender de runtime (ex.: "para
  cada arquivo que chegou, processe"). Mais natural que no Airflow estático.
- **Pythônico** — barreira de entrada baixa; parece código normal.
- **Estados ricos** e *results caching* (pular tarefas já computadas).
- **Híbrido** — o plano de controle (Prefect Cloud/Server) coordena, mas a execução roda na
  **sua** infra (bom para dados sensíveis/privacidade).

## Prefect vs Airflow vs Dagster

| Aspecto | Airflow | Dagster | Prefect |
| --- | --- | --- | --- |
| Modelo | task-centric, DAG estático | asset-centric | flows dinâmicos, pythônico |
| DAG dinâmico | limitado | moderado | **forte** |
| Lineage de dados | extra | **nativo** | parcial |
| Curva de entrada | média | média | **baixa** |
| Ecossistema/comunidade | **maior** | crescente | crescente |

## Rodando

- **Local** — rode o flow como script Python; `prefect server start` para UI local.
- **Prefect Cloud** — plano de controle gerenciado + workers na sua infra (containers/
  [Kubernetes](../../21-kubernetes/README.md)).

## Idempotência e retries

Como nos demais, retries e reexecução só são seguros com tarefas
[idempotentes](../../09-etl-elt/07-idempotency-retries/README.md). Prefect dá `retries`,
`retry_delay` e *caching* de resultados por task.

## Quando usar / quando NÃO usar

- **Use** quando valoriza simplicidade, fluxos **dinâmicos**, baixa curva de entrada, e um
  modelo híbrido (controle gerenciado + execução na sua infra).
- **Considere Airflow** se precisa do maior ecossistema/comunidade/padrão de mercado, ou
  **Dagster** se quer abordagem asset-centric com lineage/observabilidade de dados nativos.

## Erros comuns

- Tarefas não-idempotentes (retries duplicam).
- Abusar do dinamismo a ponto de tornar o pipeline difícil de entender.
- Processar dados gigantes dentro do flow sem delegar a engines.

## Boas práticas

- Idempotência + parametrização por data; delegue transformação pesada.
- Use *deployments* + work pools adequados à infra.
- Aproveite caching de resultados onde fizer sentido; configure retries por task.

## Relação com outros conceitos

- Implementa [conceitos de orquestração](../01-orchestration-concepts/README.md).
- Compara com [Airflow](../02-airflow/README.md) e [Dagster](../03-dagster/README.md).
- Roda em [containers](../../20-containers/README.md)/[Kubernetes](../../21-kubernetes/README.md).

## Exercícios

1. Escreva um flow Prefect extract→transform→load com retries por task.
2. Implemente um fluxo **dinâmico**: para cada arquivo em um diretório, dispare uma task de
   processamento.
3. Explique a vantagem do modelo híbrido (controle gerenciado, execução na sua infra) para
   dados sensíveis.
4. Compare, para o seu caso, Prefect vs Airflow vs Dagster.

## Referências

- Documentação oficial do Prefect (docs.prefect.io).
