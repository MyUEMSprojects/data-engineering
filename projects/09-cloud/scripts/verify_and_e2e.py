"""Verifica a infra criada (compliance como código) e roda o e2e: S3 → SQS → handler → curated/DLQ.

    AWS_ENDPOINT_URL=http://localhost:5000 AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1 PYTHONPATH=src python scripts/verify_and_e2e.py
"""

import json
import os
import sys
import time

import boto3

from cloudpipe import runner
from policylint.iam_sim import evaluate

ENV = os.environ.get("ENVIRONMENT", "dev")
ACCOUNT = "123456789012"
RAW, CURATED = f"orders-{ENV}-raw-{ACCOUNT}", f"orders-{ENV}-curated-{ACCOUNT}"
s3, sqs, iam = boto3.client("s3"), boto3.client("sqs"), boto3.client("iam")
checks: list[tuple[str, bool]] = []


def check(label: str, ok: bool) -> None:
    checks.append((label, bool(ok)))
    print(f"   {'✔' if ok else '✖'} {label}")


def keys(bucket: str, prefix: str) -> list[str]:
    return [o["Key"] for o in s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", [])]


print("== 1. a infraestrutura criada cumpre os requisitos ==")
for b in (RAW, CURATED):
    enc = s3.get_bucket_encryption(Bucket=b)["ServerSideEncryptionConfiguration"]["Rules"][0][
        "ApplyServerSideEncryptionByDefault"
    ]
    check(f"{b}: SSE-KMS", enc["SSEAlgorithm"] == "aws:kms")
    check(f"{b}: versionamento", s3.get_bucket_versioning(Bucket=b).get("Status") == "Enabled")
    pab = s3.get_public_access_block(Bucket=b)["PublicAccessBlockConfiguration"]
    check(f"{b}: Public Access Block total", all(pab.values()))
    check(f"{b}: lifecycle configurado", bool(s3.get_bucket_lifecycle_configuration(Bucket=b)["Rules"]))
q = sqs.get_queue_url(QueueName=f"orders-{ENV}-ingest")["QueueUrl"]
dlq = sqs.get_queue_url(QueueName=f"orders-{ENV}-ingest-dlq")["QueueUrl"]
redrive = json.loads(sqs.get_queue_attributes(QueueUrl=q, AttributeNames=["RedrivePolicy"])["Attributes"]["RedrivePolicy"])
check(
    "fila principal tem DLQ com maxReceiveCount=3",
    redrive["maxReceiveCount"] == 3 and "ingest-dlq" in redrive["deadLetterTargetArn"],
)
check(
    "notificação S3 → SQS só para incoming/*.csv",
    any(
        {"Name": "prefix", "Value": "incoming/"} in c["Filter"]["Key"]["FilterRules"]
        for c in s3.get_bucket_notification_configuration(Bucket=RAW)["QueueConfigurations"]
    ),
)

print("== 2. o papel da Lambda tem MENOR privilégio (simulador IAM) ==")
pol = iam.get_role_policy(RoleName=f"orders-{ENV}-transform", PolicyName="least-privilege")["PolicyDocument"]
S3A = "arn:aws:s3:::"
cases = [
    ("s3:GetObject", f"{S3A}{RAW}/incoming/a.csv", True),
    ("s3:PutObject", f"{S3A}{CURATED}/curated/orders/dt=2024-01-01/p.jsonl", True),
    ("s3:PutObject", f"{S3A}{RAW}/incoming/a.csv", False),  # não escreve no raw
    ("s3:DeleteObject", f"{S3A}{RAW}/incoming/a.csv", False),  # não apaga nada
    ("s3:GetObject", f"{S3A}{CURATED}/curated/x", False),  # não lê o curated
    ("s3:GetObject", f"{S3A}{RAW}/outro-prefixo/a.csv", False),  # só incoming/
    ("s3:ListBucket", f"{S3A}{RAW}", False),
    ("iam:PassRole", "*", False),
]
for action, res, want in cases:
    d = evaluate([pol], action, res)
    check(f"{action:<16} {res.replace(S3A, '')[:52]:<52} → {'PERMITIDO' if want else 'NEGADO'}", d.allowed == want)

if os.environ.get("EXPECT_TLS_DENY"):
    try:
        s3.put_object(Bucket=RAW, Key="incoming/x.csv", Body=b"x")
        check("bucket policy nega escrita via HTTP (sem TLS)", False)
    except s3.exceptions.ClientError as e:
        check("bucket policy nega escrita via HTTP (sem TLS)", e.response["Error"]["Code"] in ("403", "AccessDenied"))
    sys.exit(0 if all(ok for _, ok in checks) else 1)

print("== 3. e2e: arquivos no S3 → fila → handler → curated / DLQ ==")
os.environ["CURATED_BUCKET"] = CURATED
good = (
    "order_id,customer_id,amount,status,order_date\n"
    + "\n".join(f"O{i},C{i % 5},{10 + i}.50,paid,2024-03-0{1 + i % 2}" for i in range(6))
    + "\nOBAD,C1,-5,paid,2024-03-01\nOBAD2,,5,paid,2024-03-01\n"
)
tricky_key = "incoming/dt=2024-03-01/ordens de março+1.csv"  # espaço, acento e '+' (chega URL-encoded no evento!)
s3.put_object(Bucket=RAW, Key=tricky_key, Body=good.encode())
s3.put_object(Bucket=RAW, Key="incoming/dt=2024-03-01/veneno.csv", Body=b"coluna_errada\n1\n")  # sem cabeçalho esperado
s3.put_object(Bucket=RAW, Key="outro/ignorado.csv", Body=b"x")  # fora do prefixo: sem notificação
time.sleep(1)
n = runner.poll(q, idle_s=12, visibility=1)
curated = keys(CURATED, "curated/")
rej = keys(CURATED, "rejected/")
rows = sum(len(s3.get_object(Bucket=CURATED, Key=k)["Body"].read().decode().strip().split("\n")) for k in curated)
check(f"processou o arquivo bom (mensagens apagadas: {n}; 1 pode ser o s3:TestEvent da configuração)", n in (1, 2))
check("saída particionada por data (2 partições dt=)", len(curated) == 2)
check("6 linhas válidas em curated", rows == 6)
check(
    "2 linhas inválidas em rejected/ com motivo",
    len(rej) == 1
    and {json.loads(x)["reason"] for x in s3.get_object(Bucket=CURATED, Key=rej[0])["Body"].read().decode().strip().split("\n")}
    == {"bad_amount", "missing_field:customer_id"},
)
dl = sqs.receive_message(QueueUrl=dlq, MaxNumberOfMessages=10, WaitTimeSeconds=1).get("Messages", [])
check("arquivo-veneno foi para a DLQ após 3 tentativas", len(dl) == 1 and "veneno.csv" in dl[0]["Body"])
check("arquivo fora de incoming/ não gerou mensagem", all("ignorado" not in m["Body"] for m in dl))

print("== 4. idempotência: reentregar o mesmo evento não muda o resultado ==")
before = {k: s3.get_object(Bucket=CURATED, Key=k)["Body"].read() for k in curated}
from cloudpipe.handler import handler  # noqa: E402

ev = {
    "Records": [
        {
            "messageId": "m",
            "body": json.dumps(
                {
                    "Records": [
                        {
                            "s3": {
                                "bucket": {"name": RAW},
                                "object": {
                                    "key": tricky_key.replace(" ", "+").replace("ç", "%C3%A7").replace("+1", "%2B1"),
                                    "eTag": s3.head_object(Bucket=RAW, Key=tricky_key)["ETag"].strip('"'),
                                },
                            }
                        }
                    ]
                }
            ),
        }
    ]
}
out = handler(ev)
after = {k: s3.get_object(Bucket=CURATED, Key=k)["Body"].read() for k in keys(CURATED, "curated/")}
check("handler aceitou a chave URL-encoded (unquote_plus) sem falhar", out == {"batchItemFailures": []})
check("saídas reprocessadas têm os mesmos bytes e as mesmas chaves", before == after)
bad = sum(1 for _, ok in checks if not ok)
print(f"\n{len(checks) - bad}/{len(checks)} verificações OK")
sys.exit(1 if bad else 0)
