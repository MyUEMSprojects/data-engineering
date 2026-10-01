# Exercícios — Módulo 10: Pipelines de dados

Teoria em [10-data-pipelines](../../10-data-pipelines/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — Por que um DAG?

Por que pipelines são modelados como **grafos acíclicos dirigidos** e não como uma lista de scripts? O que acontece se houver um ciclo?

<details><summary>Gabarito</summary>

O DAG expressa **dependências** explícitas: permite paralelizar o que é independente, retomar a partir da tarefa que falhou e saber o impacto de cada falha. Um **ciclo** tornaria impossível definir uma ordem de execução (cada tarefa esperaria por si mesma). Ver [DAGs](../../10-data-pipelines/02-dags-dependencies/README.md).
</details>

## 2. 🟢 Conceitual — Data lógica × hora de execução

O job de "ontem" rodou hoje às 02:00. Qual é a **data lógica** e por que nunca devemos usar `now()` para escolher a partição?

<details><summary>Gabarito</summary>

A data lógica é "ontem" (o intervalo de dados que o run representa), não o instante em que roda. Com `now()`, **reprocessar** o mesmo run em outro dia lê outra partição — não é reproduzível nem idempotente. Ver [agendamento](../../10-data-pipelines/03-scheduling/README.md) e o [Projeto 03](../../projects/03-orchestration/README.md).
</details>

## 3. 🔵 Debugging — A tarefa "verde" que mentiu

Uma tarefa termina com sucesso, mas escreveu **0 linhas** porque a fonte entregou um arquivo vazio. O dashboard ficou zerado por 2 dias. Quais **verificações** impediriam isso e em que ponto do pipeline?

<details><summary>Gabarito</summary>

Checagens de **volume**: `rows > 0` e comparação com o histórico (anomalia), **frescor** (`max(updated_at)`), e **reconciliação** origem × destino. Posicione-as como **gate** entre extração e publicação (o lote vazio **bloqueia**). Sucesso técnico ≠ sucesso de dados. Ver [testes de pipeline](../../10-data-pipelines/07-pipeline-testing/README.md) e o gate do [Projeto 04](../../projects/04-data-quality/README.md).
</details>

## 4. 🔵 Implementação — Escrita atômica

Um job grava `out/day=2024-03-01/part.csv` e às vezes é morto no meio, deixando um arquivo truncado que o job seguinte lê. Escreva a função `write_atomic(path, data)` correta.

<details><summary>Gabarito</summary>

```python
import os, tempfile

def write_atomic(path: str, data: bytes) -> None:
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")      # MESMO filesystem do destino
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)                            # rename atômico (POSIX)
    except BaseException:
        if os.path.exists(tmp): os.remove(tmp)
        raise
```
Quem lê vê **ou o arquivo antigo ou o novo completo**, nunca o meio. Em S3, o `PUT` já é atômico por objeto. Ver [checkpoints/idempotência](../../10-data-pipelines/04-checkpoints-idempotency/README.md).
</details>

## 5. 🟣 Arquitetura — Linhagem e impacto

Uma coluna `amount` muda de significado (bruto → líquido) na fonte. Como a **linhagem** ajuda a medir o impacto e que processo evita a surpresa?

<details><summary>Gabarito</summary>

Com linhagem (idealmente **por coluna**) você lista todos os modelos, dashboards e features que dependem de `amount` e **notifica os donos** antes da mudança. O processo: **contrato de dados** versionado com aviso de depreciação, teste de compatibilidade no CI do produtor e período de coexistência (`amount_gross`/`amount_net`). Ver [linhagem](../../10-data-pipelines/06-data-lineage/README.md) e [contratos](../../29-data-contracts/README.md).
</details>

## 6. 🟣 Arquitetura — Observabilidade de pipeline

Defina **cinco métricas** e **três alertas** para um pipeline diário de pedidos (com justificativa do limite de um deles).

<details><summary>Gabarito (um caminho)</summary>

Métricas: duração por tarefa, linhas lidas/válidas/rejeitadas, **taxa de rejeição**, **frescor** do dado, timestamp do último sucesso. Alertas: (1) **gate bloqueado** (page); (2) **sem execução há > 26 h** (*dead man's switch*, 24 h + folga); (3) frescor > SLO. Limite: 26 h = período + tolerância para atraso normal, evitando alerta de falso positivo a cada pequeno atraso. Ver [observabilidade de pipelines](../../10-data-pipelines/08-pipeline-observability/README.md) e o [Projeto 04](../../projects/04-data-quality/README.md).
</details>
