"""Extração: lê CSV (streaming) e APIs paginadas.

Cada extrator é um *generator*: processa registro a registro, memória ~constante
(ver módulo 04 — generators).
"""

from __future__ import annotations

import csv
import logging
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol

log = logging.getLogger(__name__)


def read_csv(path: Path | str) -> Iterator[dict[str, str]]:
    """Lê um CSV linha a linha respeitando aspas/escapes (nunca `split(',')`)."""
    with open(path, newline="", encoding="utf-8-sig") as fh:  # utf-8-sig tolera BOM
        yield from csv.DictReader(fh)


class _Response(Protocol):
    status_code: int
    headers: Any

    def json(self) -> Any: ...
    def raise_for_status(self) -> None: ...


class _Session(Protocol):
    def get(self, url: str, **kwargs: Any) -> _Response: ...


TRANSIENT_STATUS = {429, 500, 502, 503, 504}


def _get_with_retry(
    session: _Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    retries: int = 4,
    backoff_s: float = 1.0,
    sleep=time.sleep,
) -> _Response:
    """GET com timeout e backoff exponencial **só** para erros transitórios."""
    for attempt in range(retries + 1):
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code not in TRANSIENT_STATUS:
            resp.raise_for_status()  # 4xx (exceto 429) falha de vez: retry não ajuda
            return resp
        if attempt == retries:
            resp.raise_for_status()
        retry_after = resp.headers.get("Retry-After")
        delay = (
            float(retry_after) if retry_after and retry_after.isdigit() else backoff_s * 2**attempt
        )
        log.warning(
            "status %s em %s; tentativa %d/%d, aguardando %.1fs",
            resp.status_code,
            url,
            attempt + 1,
            retries,
            delay,
        )
        sleep(delay)
    raise RuntimeError("inalcançável")  # pragma: no cover


def read_api(
    session: _Session,
    base_url: str,
    *,
    since: str | None = None,
    page_size: int = 100,
    sleep=time.sleep,
) -> Iterator[dict[str, Any]]:
    """Itera uma API paginada por cursor.

    Contrato esperado: `GET {base_url}?limit=N&since=...` retorna
    `{"data": [...], "next": "<url|null>"}`.
    """
    url: str | None = base_url
    params: dict[str, Any] | None = {"limit": page_size}
    if since:
        params["since"] = since
    pages = 0
    while url:
        body = _get_with_retry(session, url, params=params, sleep=sleep).json()
        yield from body.get("data", [])
        url = body.get("next")
        params = None  # o cursor `next` já carrega os parâmetros
        pages += 1
    log.info("API: %d páginas lidas", pages)
