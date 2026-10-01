import json
import os
from datetime import date

import pytest

from lake.bronze import ingest
from lake.storage import Lake, open_lake


@pytest.fixture
def lake(tmp_path) -> Lake:
    """Lake em disco local (rápido, sem Docker). Com LAKE_URI=s3://… os mesmos testes rodam no S3."""
    uri = os.environ.get("LAKE_URI_TEST")
    if uri:  # opt-in: usa um prefixo único por teste no bucket
        lk = open_lake(f"{uri.rstrip('/')}/t-{tmp_path.name}")
    else:
        lk = open_lake(f"file://{tmp_path}/lake")
    lk.init()
    return lk


def event(
    order_id="O1",
    *,
    amount=10.0,
    status="paid",
    order_date="2024-01-01",
    updated_at="2024-01-01T10:00:00+00:00",
    customer="C1",
    country="BR",
    category="books",
):
    return {
        "order_id": order_id,
        "customer_id": customer,
        "country": country,
        "category": category,
        "amount": amount,
        "status": status,
        "order_date": order_date,
        "updated_at": updated_at,
    }


def batch(*events, raw=()):
    lines = [json.dumps(e) for e in events] + list(raw)
    return ("\n".join(lines) + "\n").encode()


def put(lake, ingest_date, *events, raw=()):
    return ingest(lake, batch(*events, raw=raw), date.fromisoformat(ingest_date))
