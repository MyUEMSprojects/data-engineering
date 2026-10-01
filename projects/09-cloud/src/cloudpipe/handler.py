"""Lambda: CSV em raw/incoming/ → JSONL validado em curated/ (particionado por data) + rejeitadas em rejected/.

Fluxo real: S3 (ObjectCreated) → SQS → Lambda. SQS entrega *at-least-once*, então TUDO aqui é idempotente:
as chaves de saída derivam de (chave de origem + ETag); reprocessar sobrescreve com os mesmos bytes.
Falha parcial: devolve `batchItemFailures` — só as mensagens que falharam voltam à fila (e, após
`maxReceiveCount` tentativas, vão para a DLQ). Arquivo ilegível/sem cabeçalho = falha PERMANENTE.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import urllib.parse
from datetime import date
from decimal import Decimal, InvalidOperation

import boto3

REQUIRED = ("order_id", "customer_id", "amount", "status", "order_date")
STATUSES = {"created", "paid", "shipped", "delivered", "canceled"}
MAX_BYTES = 50 * 1024 * 1024  # a Lambda tem memória limitada: arquivos maiores pedem outro caminho (Glue/Spark)

_s3 = None


def s3():
    global _s3
    if _s3 is None:  # AWS_ENDPOINT_URL (boto3 ≥ 1.28) aponta para o emulador sem mudar o código
        _s3 = boto3.client("s3")
    return _s3


class PermanentError(Exception):
    """Reprocessar não adianta (arquivo corrompido, cabeçalho errado, grande demais)."""


def validate_row(row: dict) -> tuple[dict | None, str | None]:
    for f in REQUIRED:
        if not (row.get(f) or "").strip():
            return None, f"missing_field:{f}"
    try:
        amount = Decimal(row["amount"].strip())
    except InvalidOperation:
        return None, "bad_amount"
    if not amount.is_finite() or amount < 0:
        return None, "bad_amount"
    try:
        d = date.fromisoformat(row["order_date"].strip())
    except ValueError:
        return None, "bad_date"
    status = row["status"].strip().lower()
    if status not in STATUSES:
        return None, "unknown_status"
    return (
        {
            "order_id": row["order_id"].strip(),
            "customer_id": row["customer_id"].strip(),
            "amount": str(amount.quantize(Decimal("0.01"))),
            "status": status,
            "order_date": d.isoformat(),
        },
        None,
    )


def process_object(bucket: str, key: str, etag: str, curated_bucket: str) -> dict:
    head = s3().head_object(Bucket=bucket, Key=key)
    if head["ContentLength"] > MAX_BYTES:
        raise PermanentError(f"objeto de {head['ContentLength']} bytes excede {MAX_BYTES}")
    try:
        text = s3().get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    except UnicodeDecodeError as e:
        raise PermanentError("arquivo não é UTF-8") from e
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not set(REQUIRED) <= set(reader.fieldnames):
        raise PermanentError(f"cabeçalho inválido: {reader.fieldnames}")

    tag = hashlib.sha256(f"{key}|{etag}".encode()).hexdigest()[:12]
    by_date: dict[str, list[dict]] = {}
    rejects, rows_in = [], 0
    for line_no, row in enumerate(reader, start=2):
        rows_in += 1
        ok, reason = validate_row(row)
        if ok is None:
            rejects.append({"line": line_no, "reason": reason, "row": row})
        else:
            by_date.setdefault(ok["order_date"], []).append(ok)

    outputs = []
    for d, rows in sorted(by_date.items()):
        out = f"curated/orders/dt={d}/part-{tag}.jsonl"
        body = "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n"
        s3().put_object(Bucket=curated_bucket, Key=out, Body=body.encode())
        outputs.append(out)
    if rejects:
        out = f"rejected/orders/{tag}.jsonl"
        body = "\n".join(json.dumps({**r, "source": f"s3://{bucket}/{key}"}) for r in rejects) + "\n"
        s3().put_object(Bucket=curated_bucket, Key=out, Body=body.encode())
        outputs.append(out)
    return {"source": key, "rows_in": rows_in, "rows_ok": rows_in - len(rejects), "rejected": len(rejects), "outputs": outputs}


def handler(event, context=None):
    curated = os.environ["CURATED_BUCKET"]
    failures = []
    for rec in event.get("Records", []):
        try:
            body = json.loads(rec["body"])
            if body.get("Event") == "s3:TestEvent":  # o S3 envia isso ao configurar a notificação
                continue
            for r in body.get("Records", []):
                key = urllib.parse.unquote_plus(r["s3"]["object"]["key"])  # chaves chegam URL-encoded!
                res = process_object(r["s3"]["bucket"]["name"], key, r["s3"]["object"].get("eTag", ""), curated)
                print(json.dumps({"level": "INFO", **res}))
        except Exception as e:  # noqa: BLE001 — qualquer falha devolve a mensagem à fila
            print(json.dumps({"level": "ERROR", "message_id": rec.get("messageId"), "error": repr(e)}))
            failures.append({"itemIdentifier": rec["messageId"]})
    return {"batchItemFailures": failures}
