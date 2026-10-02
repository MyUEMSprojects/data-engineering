"""Linter de `terraform show -json <plano>`: regras de segurança/custo verificadas ANTES do apply.

Cada regra devolve Findings; o CLI sai com código 1 se houver algum. É o mesmo papel de Checkov/tfsec/OPA —
aqui em ~100 linhas para o mecanismo ficar à vista.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    rule: str
    resource: str
    message: str


def _resources(doc: dict) -> list[dict]:
    """Aceita `terraform show -json` de um PLANO (resource_changes) ou de um ESTADO (values).

    ⚠️ No plano, tudo que depende de atributo computado (ARN de bucket numa policy, p.ex.) é "conhecido
    só após o apply" e some do JSON ⇒ regras sobre esses campos só são confiáveis no ESTADO — daí o
    fluxo: apply no emulador → lint do estado → (só então) apply na nuvem.
    """
    out = []
    if "resource_changes" in doc:
        for rc in doc["resource_changes"]:
            if "delete" not in rc["change"]["actions"]:
                out.append({"type": rc["type"], "address": rc["address"], **(rc["change"].get("after") or {})})
        return out

    def walk(mod: dict):
        for r in mod.get("resources", []):
            out.append({"type": r["type"], "address": r["address"], **(r.get("values") or {})})
        for child in mod.get("child_modules", []):
            walk(child)

    walk(doc.get("values", {}).get("root_module", {}))
    return out


def _key(r: dict) -> str:
    """Identidade do bucket: no PLANO o nome ainda é 'desconhecido até o apply', então casamos pelo índice
    do for_each (`...["raw"]`) — ou por '' quando o recurso não usa for_each."""
    a = r["address"]
    return a[a.index("[") :] if "[" in a else ""


def _of(res: list[dict], t: str) -> list[dict]:
    return [r for r in res if r["type"] == t]


def _statements(policy_json: str | None) -> list[dict]:
    if not policy_json:
        return []
    st = json.loads(policy_json).get("Statement", [])
    return st if isinstance(st, list) else [st]


def _as_list(v) -> list:
    return v if isinstance(v, list) else [v]


def lint(plan: dict) -> list[Finding]:
    res, f = _resources(plan), []

    # ---- IAM: menor privilégio
    for r in _of(res, "aws_iam_role_policy") + _of(res, "aws_iam_policy"):
        for st in _statements(r.get("policy")):
            if st.get("Effect") != "Allow":
                continue
            for a in _as_list(st.get("Action", [])):
                if a == "*" or a.endswith(":*"):
                    f.append(Finding("IAM-001", r["address"], f"ação com curinga: {a}"))
            for rs in _as_list(st.get("Resource", [])):
                if rs == "*":
                    f.append(Finding("IAM-002", r["address"], f"Resource '*' em {st.get('Sid', '?')}"))

    # ---- políticas de recurso: Principal "*" exige Condition (ou ser um Deny)
    for t in ("aws_s3_bucket_policy", "aws_sqs_queue_policy"):
        for r in _of(res, t):
            for st in _statements(r.get("policy")):
                p = st.get("Principal")
                star = p == "*" or (isinstance(p, dict) and "*" in _as_list(p.get("AWS", [])) + _as_list(p.get("*", [])))
                if star and st.get("Effect") == "Allow" and not st.get("Condition"):
                    f.append(Finding("IAM-003", r["address"], "Allow para Principal '*' sem Condition"))

    # ---- S3
    buckets = {_key(r): r["address"] for r in _of(res, "aws_s3_bucket")}
    enc = {
        _key(r)
        for r in _of(res, "aws_s3_bucket_server_side_encryption_configuration")
        if any(
            d.get("sse_algorithm") == "aws:kms"
            for rule in r.get("rule", [])
            for d in rule.get("apply_server_side_encryption_by_default", [])
        )
    }
    ver = {
        _key(r)
        for r in _of(res, "aws_s3_bucket_versioning")
        if any(v.get("status") == "Enabled" for v in r.get("versioning_configuration", []))
    }
    pab = {
        _key(r)
        for r in _of(res, "aws_s3_bucket_public_access_block")
        if all(r.get(k) for k in ("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets"))
    }
    tls = set()
    for r in _of(res, "aws_s3_bucket_policy"):
        for st in _statements(r.get("policy")):
            cond = json.dumps(st.get("Condition", {}))
            if st.get("Effect") == "Deny" and "aws:SecureTransport" in cond and "false" in cond.lower():
                tls.add(_key(r))
    for name, addr in buckets.items():
        for rule, ok, msg in (
            ("S3-001", name in enc, "sem criptografia SSE-KMS"),
            ("S3-002", name in ver, "sem versionamento"),
            ("S3-003", name in pab, "Public Access Block incompleto"),
            ("S3-004", name in tls, "sem Deny para tráfego não-TLS"),
        ):
            if not ok:
                f.append(Finding(rule, addr, msg))

    # ---- SQS
    for r in _of(res, "aws_sqs_queue"):
        if not (r.get("sqs_managed_sse_enabled") or r.get("kms_master_key_id")):
            f.append(Finding("SQS-001", r["address"], "fila sem criptografia"))
        if not r["name"].endswith("-dlq") and not r.get("redrive_policy"):
            f.append(Finding("SQS-002", r["address"], "fila sem DLQ (redrive_policy)"))

    # ---- KMS / logs
    for r in _of(res, "aws_kms_key"):
        if not r.get("enable_key_rotation"):
            f.append(Finding("KMS-001", r["address"], "rotação de chave desligada"))
    for r in _of(res, "aws_cloudwatch_log_group"):
        if not r.get("retention_in_days"):
            f.append(Finding("LOG-001", r["address"], "log group sem retenção (custo cresce para sempre)"))
    return f


def main(argv: list[str] | None = None) -> int:
    path = (argv or sys.argv[1:])[0]
    findings = lint(json.load(open(path)))
    for x in findings:
        print(f"✖ {x.rule}  {x.resource}: {x.message}")
    print(f"{len(findings)} achado(s)" if findings else "✔ nenhuma violação")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
