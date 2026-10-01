import json

import boto3
import pytest
from moto import mock_aws

from cloudpipe import handler as h

RAW, CUR = "raw-b", "cur-b"
HDR = "order_id,customer_id,amount,status,order_date\n"


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "t")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "t")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("CURATED_BUCKET", CUR)
    monkeypatch.setattr(h, "_s3", None)
    with mock_aws():
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket=RAW)
        s3.create_bucket(Bucket=CUR)
        yield s3
    h._s3 = None


def ev(key, etag="e1", mid="m1"):
    return {
        "Records": [
            {
                "messageId": mid,
                "body": json.dumps({"Records": [{"s3": {"bucket": {"name": RAW}, "object": {"key": key, "eTag": etag}}}]}),
            }
        ]
    }


def objs(s3, prefix):
    return sorted(o["Key"] for o in s3.list_objects_v2(Bucket=CUR, Prefix=prefix).get("Contents", []))


def test_validate_row_reasons():
    base = {"order_id": "1", "customer_id": "c", "amount": "9.5", "status": "PAID", "order_date": "2024-01-01"}
    ok, _ = h.validate_row(base)
    assert ok["status"] == "paid" and ok["amount"] == "9.50"
    for patch, reason in [
        ({"amount": "x"}, "bad_amount"),
        ({"amount": "-1"}, "bad_amount"),
        ({"amount": "NaN"}, "bad_amount"),
        ({"order_date": "2024-13-01"}, "bad_date"),
        ({"status": "teleported"}, "unknown_status"),
        ({"order_id": " "}, "missing_field:order_id"),
    ]:
        assert h.validate_row({**base, **patch})[1] == reason


def test_happy_path_partitions_by_date_and_quarantines_bad_rows(aws):
    body = HDR + "1,c1,10,paid,2024-01-01\n2,c2,20,paid,2024-01-02\n3,c3,-1,paid,2024-01-01\n"
    aws.put_object(Bucket=RAW, Key="incoming/a.csv", Body=body.encode())
    assert h.handler(ev("incoming/a.csv")) == {"batchItemFailures": []}
    out = objs(aws, "curated/")
    assert [o.split("/")[2] for o in out] == ["dt=2024-01-01", "dt=2024-01-02"]
    assert len(objs(aws, "rejected/")) == 1


def test_encoded_key_with_space_plus_and_accent(aws):
    key = "incoming/ordens de março+1.csv"
    aws.put_object(Bucket=RAW, Key=key, Body=(HDR + "1,c,1,paid,2024-01-01\n").encode())
    encoded = "incoming/ordens+de+mar%C3%A7o%2B1.csv"
    assert h.handler(ev(encoded))["batchItemFailures"] == []
    assert len(objs(aws, "curated/")) == 1


def test_reprocessing_is_idempotent_and_new_etag_makes_new_output(aws):
    aws.put_object(Bucket=RAW, Key="incoming/a.csv", Body=(HDR + "1,c,1,paid,2024-01-01\n").encode())
    h.handler(ev("incoming/a.csv"))
    first = objs(aws, "curated/")
    h.handler(ev("incoming/a.csv"))  # reentrega do mesmo evento (SQS é at-least-once)
    assert objs(aws, "curated/") == first
    h.handler(ev("incoming/a.csv", etag="e2"))  # arquivo REGRAVADO (outro ETag) ⇒ nova saída
    assert len(objs(aws, "curated/")) == 2


def test_permanent_errors_are_reported_as_partial_batch_failures(aws):
    aws.put_object(Bucket=RAW, Key="incoming/bad.csv", Body=b"foo,bar\n1,2\n")
    aws.put_object(Bucket=RAW, Key="incoming/ok.csv", Body=(HDR + "1,c,1,paid,2024-01-01\n").encode())
    event = {"Records": [ev("incoming/bad.csv", mid="bad")["Records"][0], ev("incoming/ok.csv", mid="ok")["Records"][0]]}
    assert h.handler(event) == {"batchItemFailures": [{"itemIdentifier": "bad"}]}  # só a ruim volta à fila
    assert len(objs(aws, "curated/")) == 1


def test_missing_object_and_non_utf8_fail_without_crashing(aws):
    aws.put_object(Bucket=RAW, Key="incoming/latin1.csv", Body=HDR.encode() + b"1,c,1,paid,2024-01-01\n" + b"\xe9")
    for key in ("incoming/nao-existe.csv", "incoming/latin1.csv"):
        assert h.handler(ev(key, mid=key))["batchItemFailures"] == [{"itemIdentifier": key}]


def test_s3_test_event_and_garbage_body(aws):
    t = {"Records": [{"messageId": "t", "body": json.dumps({"Event": "s3:TestEvent"})}]}
    assert h.handler(t) == {"batchItemFailures": []}
    g = {"Records": [{"messageId": "g", "body": "não é json"}]}
    assert h.handler(g) == {"batchItemFailures": [{"itemIdentifier": "g"}]}


def test_oversized_object_is_a_permanent_error(aws, monkeypatch):
    monkeypatch.setattr(h, "MAX_BYTES", 10)
    aws.put_object(Bucket=RAW, Key="incoming/big.csv", Body=(HDR + "1,c,1,paid,2024-01-01\n").encode())
    assert h.handler(ev("incoming/big.csv", mid="big"))["batchItemFailures"] == [{"itemIdentifier": "big"}]
