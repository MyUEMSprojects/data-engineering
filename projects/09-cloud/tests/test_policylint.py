import json

import pytest

from policylint.iam_sim import evaluate
from policylint.lint import lint

ARN = "arn:aws:s3:::b"


def pol(*statements):
    return {"Version": "2012-10-17", "Statement": list(statements)}


# ---------------------------------------------------------------- simulador IAM
def test_implicit_deny_and_allow():
    p = pol({"Sid": "R", "Effect": "Allow", "Action": "s3:GetObject", "Resource": f"{ARN}/in/*"})
    assert evaluate([p], "s3:GetObject", f"{ARN}/in/a.csv").allowed
    d = evaluate([p], "s3:GetObject", f"{ARN}/out/a.csv")
    assert not d.allowed and "implícita" in d.reason
    assert not evaluate([p], "s3:PutObject", f"{ARN}/in/a.csv").allowed


def test_explicit_deny_beats_allow_and_actions_are_case_insensitive():
    p = pol(
        {"Effect": "Allow", "Action": "s3:*", "Resource": "*"},
        {"Sid": "NoDelete", "Effect": "Deny", "Action": "S3:Delete*", "Resource": "*"},
    )
    assert evaluate([p], "s3:getobject", ARN).allowed
    d = evaluate([p], "s3:DeleteObject", ARN)
    assert not d.allowed and "NoDelete" in d.reason


def test_resource_matching_is_case_sensitive_and_json_strings_are_accepted():
    p = json.dumps(pol({"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": [f"{ARN}/A*"]}))
    assert evaluate([p], "s3:GetObject", f"{ARN}/Ab").allowed
    assert not evaluate([p], "s3:GetObject", f"{ARN}/ab").allowed


def test_notaction_is_refused_loudly_instead_of_guessing():
    with pytest.raises(NotImplementedError):
        evaluate([pol({"Effect": "Allow", "NotAction": "s3:*", "Resource": "*"})], "s3:GetObject", ARN)


# ---------------------------------------------------------------- linter
def _plan(*resources):
    return {
        "resource_changes": [{"type": t, "address": a, "change": {"actions": ["create"], "after": v}} for t, a, v in resources]
    }


def _good():
    tls = json.dumps(
        pol(
            {
                "Effect": "Deny",
                "Action": "s3:*",
                "Resource": "*",
                "Principal": "*",
                "Condition": {"Bool": {"aws:SecureTransport": ["false"]}},
            }
        )
    )
    k = '["raw"]'
    return [
        ("aws_s3_bucket", f"aws_s3_bucket.lake{k}", {"bucket": "b"}),
        (
            "aws_s3_bucket_server_side_encryption_configuration",
            f"x.lake{k}",
            {"rule": [{"apply_server_side_encryption_by_default": [{"sse_algorithm": "aws:kms"}]}]},
        ),
        ("aws_s3_bucket_versioning", f"x.lake{k}", {"versioning_configuration": [{"status": "Enabled"}]}),
        (
            "aws_s3_bucket_public_access_block",
            f"x.lake{k}",
            dict.fromkeys(("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets"), True),
        ),
        ("aws_s3_bucket_policy", f"x.lake{k}", {"policy": tls}),
        ("aws_sqs_queue", "q.ingest", {"name": "q", "sqs_managed_sse_enabled": True, "redrive_policy": "{}"}),
        ("aws_sqs_queue", "q.dlq", {"name": "q-dlq", "sqs_managed_sse_enabled": True}),
        ("aws_kms_key", "k", {"enable_key_rotation": True}),
        ("aws_cloudwatch_log_group", "l", {"retention_in_days": 14}),
        (
            "aws_iam_role_policy",
            "p",
            {"policy": json.dumps(pol({"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:x/*"}))},
        ),
    ]


def rules(plan):
    return sorted(f.rule for f in lint(plan))


def test_a_compliant_stack_has_no_findings():
    assert lint(_plan(*_good())) == []


def _mutate(match, **changes):
    out = []
    for t, a, v in _good():
        out.append((t, a, {**v, **changes}) if match(t, a) else (t, a, v))
    return _plan(*out)


@pytest.mark.parametrize(
    ("rule", "plan"),
    [
        (
            "IAM-001",
            _plan(
                (
                    "aws_iam_role_policy",
                    "p",
                    {"policy": json.dumps(pol({"Effect": "Allow", "Action": "s3:*", "Resource": "arn:x"}))},
                )
            ),
        ),
        (
            "IAM-002",
            _plan(
                (
                    "aws_iam_role_policy",
                    "p",
                    {"policy": json.dumps(pol({"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"}))},
                )
            ),
        ),
        (
            "IAM-003",
            _plan(
                (
                    "aws_sqs_queue_policy",
                    "qp",
                    {
                        "policy": json.dumps(
                            pol({"Effect": "Allow", "Action": "sqs:SendMessage", "Resource": "*", "Principal": "*"})
                        )
                    },
                )
            ),
        ),
        ("S3-002", _mutate(lambda t, a: t == "aws_s3_bucket_versioning", versioning_configuration=[{"status": "Suspended"}])),
        ("S3-003", _mutate(lambda t, a: t == "aws_s3_bucket_public_access_block", block_public_acls=False)),
        ("SQS-001", _mutate(lambda t, a: a == "q.ingest", sqs_managed_sse_enabled=False)),
        ("SQS-002", _mutate(lambda t, a: a == "q.ingest", redrive_policy=None)),
        ("KMS-001", _mutate(lambda t, a: t == "aws_kms_key", enable_key_rotation=False)),
        ("LOG-001", _mutate(lambda t, a: t == "aws_cloudwatch_log_group", retention_in_days=0)),
    ],
)
def test_each_rule_catches_its_violation(rule, plan):
    assert rule in rules(plan)


def test_missing_tls_deny_and_missing_encryption_are_caught():
    plan = _plan(
        *[x for x in _good() if x[0] not in ("aws_s3_bucket_policy", "aws_s3_bucket_server_side_encryption_configuration")]
    )
    assert rules(plan) == ["S3-001", "S3-004"]


def test_deny_star_principal_is_fine_but_allow_star_with_condition_too():
    ok = json.dumps(
        pol(
            {
                "Effect": "Allow",
                "Action": "sqs:SendMessage",
                "Resource": "*",
                "Principal": {"AWS": "*"},
                "Condition": {"ArnEquals": {"aws:SourceArn": "x"}},
            }
        )
    )
    assert lint(_plan(("aws_sqs_queue_policy", "qp", {"policy": ok}))) == []


def test_state_format_is_understood_and_deleted_resources_ignored():
    state = {
        "values": {
            "root_module": {"resources": [{"type": "aws_kms_key", "address": "k", "values": {"enable_key_rotation": False}}]}
        }
    }
    assert rules(state) == ["KMS-001"]
    gone = {"resource_changes": [{"type": "aws_kms_key", "address": "k", "change": {"actions": ["delete"], "after": None}}]}
    assert lint(gone) == []
