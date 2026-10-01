# HTTP clients (consumir APIs)

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

## Por que isso é essencial

Boa parte da ingestão de dados vem de **APIs HTTP** (REST): SaaS, serviços internos,
dados públicos. Consumir APIs de forma **robusta** — com paginação, autenticação,
retries, *rate limiting* e tratamento de erros — é uma habilidade diária do DE.

## requests vs httpx

- **`requests`** — o cliente síncrono clássico, simples e onipresente.
- **`httpx`** — API parecida, mas suporta **async** e HTTP/2; bom quando você
  precisa de alta concorrência (ver [concorrência](../07-concurrency/README.md)).

```python
import requests

resp = requests.get(
    "https://api.exemplo.com/v1/orders",
    params={"since": "2024-01-01", "limit": 100},
    headers={"Authorization": f"Bearer {token}"},
    timeout=30,                       # SEMPRE defina timeout
)
resp.raise_for_status()              # levanta erro em status >= 400
dados = resp.json()
```

> **Sempre** defina `timeout` — sem ele, uma API travada pendura seu pipeline
> indefinidamente. E use `raise_for_status()` para não processar respostas de erro
> como se fossem dados.

## Sessões (reutilizar conexão)

```python
with requests.Session() as s:
    s.headers.update({"Authorization": f"Bearer {token}"})
    for page in range(1, 10):
        r = s.get(url, params={"page": page}, timeout=30)
        ...
```

A `Session` reaproveita a conexão TCP (mais rápido) e centraliza headers/auth.

## Paginação (o padrão mais importante)

APIs retornam dados em páginas. Encapsule a paginação em um **generator** (ver
[generators](../06-iterators-generators-context-managers/README.md)) para processar
sem acumular tudo na memória.

```python
def iter_orders(session, base_url):
    url = f"{base_url}/orders"
    params = {"limit": 100}
    while url:
        r = session.get(url, params=params, timeout=30)
        r.raise_for_status()
        body = r.json()
        yield from body["data"]            # entrega item a item
        url = body.get("next")             # cursor/next-link; None encerra
        params = {}                         # o next já traz os params
```

Estilos comuns: *offset/limit* (`?page=2`), *cursor* (`?after=abc`), *link header*
(`Link: <...>; rel="next"`). Prefira cursor quando disponível (estável sob escrita).

## Retries e backoff (robustez)

Redes falham. Retente **erros transitórios** (timeouts, 429, 5xx) com *exponential
backoff* + *jitter*; **não** retente erros permanentes (400, 401, 404).

Com `tenacity` (simples e robusto):

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=1, max=30),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
)
def get_com_retry(session, url, **kw):
    r = session.get(url, timeout=30, **kw)
    if r.status_code >= 500 or r.status_code == 429:
        r.raise_for_status()       # dispara retry
    r.raise_for_status()           # 4xx (exceto 429) falha de vez
    return r
```

Alternativa só com `requests`: `HTTPAdapter` + `urllib3.util.Retry`.

## Rate limiting

APIs limitam requisições. Respeite:

- O header **`Retry-After`** em respostas `429` (espere o tempo indicado).
- Limite a concorrência (`max_workers`) e adicione pausas.
- Em paralelo, combine com *backoff* para recuar sob pressão.

## Autenticação

- **API key / Bearer token** — em header `Authorization`. Leia de variável de
  ambiente/secret manager, **nunca** hardcode (ver
  [security](../../26-security/04-secrets-management/README.md)).
- **OAuth2** — obtenha token (client credentials) e **renove** antes de expirar.
- Trate `401` renovando o token uma vez; se persistir, falhe.

## Streaming de respostas grandes

Para downloads grandes, não carregue tudo na memória:

```python
with session.get(url, stream=True, timeout=60) as r:
    r.raise_for_status()
    with open("arquivo.csv", "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):   # 1 MB por vez
            f.write(chunk)
```

## Idempotência na ingestão

Projete a ingestão para ser re-executável sem duplicar: use parâmetros `since`/
cursores persistidos, escreva em arquivo temporário e mova atômico, e deduplique na
transformação. Ver [idempotência](../../09-etl-elt/07-idempotency-retries/README.md).

## Erros comuns

- Sem `timeout` → pipeline pendurado.
- Processar resposta de erro como dados (faltou `raise_for_status`).
- Retentar erros permanentes (401/404) em loop.
- Ignorar `429`/`Retry-After` e ser bloqueado.
- Carregar todas as páginas na memória em vez de *stream*/generator.
- Token hardcoded no código.

## Boas práticas

- `Session` + `timeout` + `raise_for_status` sempre.
- Paginação como generator; retries com backoff só para transitórios.
- Respeite *rate limits*; segredos fora do código.
- Logue contagens e páginas processadas (observabilidade).

## Relação com outros conceitos

- Alimenta [ingestão/extraction](../../09-etl-elt/02-ingestion-extraction/README.md).
- Concorrência: [threading/async](../07-concurrency/README.md).
- Robustez conecta a [fault tolerance](../../10-data-pipelines/05-fault-tolerance/README.md).

## Exercícios

1. Escreva um generator que itera todas as páginas de uma API com cursor.
2. Adicione retries com backoff+jitter que retentam só 429/5xx/timeout.
3. Implemente respeito ao header `Retry-After` em respostas 429.
4. Baixe um arquivo grande via `stream=True` sem estourar a memória.

## Referências

- Documentação de `requests`, `httpx`, `tenacity`, `urllib3`.
- RFC 9110 (HTTP Semantics); RFC 6585 (429 Too Many Requests).
