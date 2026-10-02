"""Orquestra extract -> validate -> dedupe -> load e expõe uma CLI."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .extract import read_api, read_csv
from .transform import deduplicate, validate_rows

log = logging.getLogger("basic_etl")


@dataclass(frozen=True)
class RunStats:
    run_id: str
    read: int
    valid: int
    rejected: int
    after_dedupe: int
    loaded: int

    @property
    def reject_rate(self) -> float:
        return self.rejected / self.read if self.read else 0.0


def transform_stage(rows: Iterable[Mapping[str, Any]]):
    """Parte pura do pipeline (sem banco): devolve (orders, rejected, nº lido)."""
    rows = list(rows)
    valid, rejected = validate_rows(rows)
    return deduplicate(valid), rejected, len(rows), len(valid)


def run(
    rows: Iterable[Mapping[str, Any]],
    *,
    database_url: str | None,
    max_reject_rate: float = 0.2,
    dry_run: bool = False,
) -> RunStats:
    run_id = uuid.uuid4().hex[:12]
    orders, rejected, n_read, n_valid = transform_stage(rows)
    stats_kwargs = dict(
        run_id=run_id, read=n_read, valid=n_valid, rejected=len(rejected), after_dedupe=len(orders)
    )
    log.info(
        "run=%s lidas=%d válidas=%d rejeitadas=%d após_dedupe=%d",
        run_id,
        n_read,
        n_valid,
        len(rejected),
        len(orders),
    )

    # Gate de qualidade: se a taxa de rejeição passa do limite, algo está errado na
    # origem (schema mudou?) — falha alto em vez de carregar um lote suspeito.
    if n_read and len(rejected) / n_read > max_reject_rate:
        raise RuntimeError(
            f"taxa de rejeição {len(rejected) / n_read:.0%} > {max_reject_rate:.0%}; "
            "abortando antes de carregar (verifique a fonte)"
        )
    if dry_run or not database_url:
        log.info("dry-run: nada gravado")
        return RunStats(**stats_kwargs, loaded=0)

    import psycopg  # import tardio: a parte pura não exige driver

    from .load import quarantine, upsert_orders

    with psycopg.connect(database_url) as conn:
        quarantine(conn, run_id, rejected)
        loaded = upsert_orders(conn, orders)
    log.info("run=%s carregadas=%d", run_id, loaded)
    return RunStats(**stats_kwargs, loaded=loaded)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ETL básico de pedidos (CSV/API -> PostgreSQL)")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", type=Path, help="caminho do CSV de entrada")
    src.add_argument("--api-url", help="URL base de uma API paginada por cursor")
    p.add_argument("--since", help="(API) traz só registros a partir deste timestamp ISO-8601")
    p.add_argument("--max-reject-rate", type=float, default=0.2)
    p.add_argument("--dry-run", action="store_true", help="valida e transforma, sem gravar")
    return p


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = _build_parser().parse_args(argv)

    if args.csv:
        rows: Iterable[Mapping[str, Any]] = read_csv(args.csv)
    else:
        import requests

        rows = read_api(requests.Session(), args.api_url, since=args.since)

    try:
        stats = run(
            rows,
            database_url=os.environ.get("DATABASE_URL"),
            max_reject_rate=args.max_reject_rate,
            dry_run=args.dry_run,
        )
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1
    print(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
