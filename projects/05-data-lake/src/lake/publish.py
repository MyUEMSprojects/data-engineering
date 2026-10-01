"""Publicação idempotente de um "diretório de tabela/partição" no object storage.

Os arquivos se chamam ``part-<hash do conteúdo>-<i>-of-<N>.parquet`` (o ``of-N`` codifica o layout:
sem isso, trocar só o tamanho dos arquivos reaproveitaria o nome ``-000`` e deixaria dados antigos
lado a lado com os novos — bug real encontrado ao testar). Assim:
- mesmo conteúdo + mesmo layout ⇒ **nada é escrito** (reexecução é barata e segura);
- conteúdo novo ⇒ escreve os arquivos novos **primeiro** e só depois apaga os antigos.

⚠️ Limite honesto: entre "escrever os novos" e "apagar os antigos" um leitor concorrente enxerga
as duas versões. Resolver isso de verdade exige um *log de transações* — é exatamente o que Delta/
Iceberg/Hudi adicionam (módulo 15). Aqui, o desenho minimiza a janela, não a elimina.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import pyarrow as pa

from .storage import Lake


def content_hash(table: pa.Table, sort_by: str | None = None) -> str:
    if sort_by:
        table = table.sort_by(sort_by)
    h = hashlib.sha256()
    h.update(json.dumps(table.schema.names).encode())
    h.update(json.dumps(table.to_pylist(), default=str, sort_keys=True).encode())
    return h.hexdigest()[:12]


@dataclass(frozen=True)
class PublishResult:
    directory: str
    files: int
    rows: int
    written: bool  # False = já estava idêntico


def publish_dir(
    lake: Lake,
    directory: str,
    table: pa.Table,
    *,
    sort_by: str | None = None,
    rows_per_file: int = 1_000_000,
) -> PublishResult:
    if sort_by:
        table = table.sort_by(sort_by)
    digest = content_hash(table)
    n_files = max(1, -(-table.num_rows // rows_per_file))
    wanted = {
        f"{directory}/part-{digest}-{i:03d}-of-{n_files:03d}.parquet": table.slice(
            i * rows_per_file, rows_per_file
        )
        for i in range(n_files)
    }
    existing = {f.path for f in lake.list_files(directory) if f.path.endswith(".parquet")}
    if existing == set(wanted):
        return PublishResult(directory, n_files, table.num_rows, written=False)
    for rel, part in wanted.items():
        if rel not in existing:
            lake.write_parquet(rel, part)
    for rel in existing - set(wanted):
        lake.delete(rel)
    return PublishResult(directory, n_files, table.num_rows, written=True)
