#!/usr/bin/env python3
"""Verifica links relativos em arquivos Markdown.

Percorre todos os `*.md` do repositório e garante que cada link relativo
(que não começa com http(s):// nem com #) aponta para um arquivo existente.
Sai com código 1 se encontrar qualquer link quebrado.

Uso:
    python3 .github/scripts/check_links.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv"}


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "#", "tel:"))


def main() -> int:
    broken: list[str] = []
    md_files = [
        p
        for p in ROOT.rglob("*.md")
        if not any(part in SKIP_DIRS for part in p.parts)
    ]
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            # Remove âncora e título: (path#sec "title") -> path
            target = target.split()[0]
            target = target.split("#")[0]
            if not target or is_external(target):
                continue
            resolved = (md.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"{md.relative_to(ROOT)} -> {target}")

    if broken:
        print("Links quebrados encontrados:")
        for b in broken:
            print(f"  - {b}")
        return 1
    print(f"OK: {len(md_files)} arquivos Markdown verificados, nenhum link quebrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
