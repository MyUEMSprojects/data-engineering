"""Simulador MÍNIMO de avaliação IAM (identity policies): Deny explícito > Allow > negação implícita.

Limites honestos: ignora Condition, NotAction/NotResource, permission boundaries, SCPs e policies de
recurso. Serve para responder "este papel PODE/NÃO PODE fazer X?" nos testes — não substitui o
IAM Policy Simulator da AWS.
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass


def _list(v) -> list:
    return v if isinstance(v, list) else [v]


def _match(pattern: str, value: str, *, ci: bool) -> bool:
    if ci:
        pattern, value = pattern.lower(), value.lower()
    return fnmatch.fnmatchcase(value, pattern)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


def evaluate(policies: list[dict | str], action: str, resource: str) -> Decision:
    allowed_by = None
    for pol in policies:
        doc = json.loads(pol) if isinstance(pol, str) else pol
        for st in _list(doc.get("Statement", [])):
            if "NotAction" in st or "NotResource" in st:
                raise NotImplementedError("NotAction/NotResource não suportados pelo simulador")
            if not any(_match(a, action, ci=True) for a in _list(st.get("Action", []))):
                continue
            if not any(_match(r, resource, ci=False) for r in _list(st.get("Resource", []))):
                continue
            if st["Effect"] == "Deny":
                return Decision(False, f"Deny explícito ({st.get('Sid', '?')})")
            allowed_by = allowed_by or st.get("Sid", "?")
    return Decision(True, f"Allow ({allowed_by})") if allowed_by else Decision(False, "negação implícita")
