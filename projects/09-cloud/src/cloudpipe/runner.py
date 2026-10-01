"""Poller local que SIMULA o event source mapping SQS→Lambda (o emulador não executa a Lambda)."""

from __future__ import annotations

import os
import sys
import time

import boto3

from . import handler as h


def poll(queue_url: str, *, idle_s: float = 3.0, visibility: int = 1) -> int:
    sqs = boto3.client("sqs")
    handled, idle_since = 0, time.time()
    while time.time() - idle_since < idle_s:
        msgs = sqs.receive_message(
            QueueUrl=queue_url, MaxNumberOfMessages=10, VisibilityTimeout=visibility, WaitTimeSeconds=1
        ).get("Messages", [])
        if not msgs:
            continue
        idle_since = time.time()
        event = {"Records": [{"messageId": m["MessageId"], "body": m["Body"], "receiptHandle": m["ReceiptHandle"]} for m in msgs]}
        failed = {f["itemIdentifier"] for f in h.handler(event)["batchItemFailures"]}
        for m in msgs:
            if m["MessageId"] not in failed:  # só apaga o que deu certo; o resto reaparece (→ DLQ após N)
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=m["ReceiptHandle"])
                handled += 1
    return handled


if __name__ == "__main__":
    print("processadas:", poll(sys.argv[1] if len(sys.argv) > 1 else os.environ["INGEST_QUEUE_URL"]))
