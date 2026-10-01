"""Camada de armazenamento: o MESMO código roda em disco local e em S3/MinIO.

`pyarrow.fs` abstrai os dois. Todos os caminhos do projeto são *relativos à raiz do lake*
(ex.: ``bronze/orders/ingest_date=2024-01-01/batch-ab12.jsonl``) — trocar o backend não
muda nenhuma regra de negócio.
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass

import pyarrow as pa
import pyarrow.fs as pafs
import pyarrow.parquet as pq


@dataclass(frozen=True)
class FileEntry:
    path: str  # relativo à raiz do lake
    size: int


class Lake:
    def __init__(self, fs: pafs.FileSystem, root: str, *, local: bool):
        self.fs = fs
        self.root = root.rstrip("/")
        self.local = local

    # -- caminhos -----------------------------------------------------------------
    def abs(self, rel: str) -> str:
        return f"{self.root}/{rel}" if rel else self.root

    # -- operações básicas --------------------------------------------------------
    def init(self) -> None:
        """Cria a raiz (diretório local ou *bucket*). Idempotente."""
        self.fs.create_dir(self.root, recursive=True)

    def exists(self, rel: str) -> bool:
        return self.fs.get_file_info(self.abs(rel)).type == pafs.FileType.File

    def write(self, rel: str, data: bytes) -> None:
        """Grava um objeto. Local: tmp + rename (atômico). S3: o PUT já é atômico por objeto."""
        target = self.abs(rel)
        if self.local:
            self.fs.create_dir(target.rsplit("/", 1)[0], recursive=True)
            tmp = target + ".tmp"
            with self.fs.open_output_stream(tmp) as out:
                out.write(data)
            self.fs.move(tmp, target)
        else:
            with self.fs.open_output_stream(target) as out:
                out.write(data)

    def read(self, rel: str) -> bytes:
        with self.fs.open_input_stream(self.abs(rel)) as src:
            return src.read()

    def delete(self, rel: str) -> None:
        self.fs.delete_file(self.abs(rel))

    def list_files(self, prefix: str = "") -> list[FileEntry]:
        sel = pafs.FileSelector(self.abs(prefix), recursive=True, allow_not_found=True)
        base = self.root + "/"
        return sorted(
            (
                FileEntry(i.path[len(base) :], i.size or 0)
                for i in self.fs.get_file_info(sel)
                if i.type == pafs.FileType.File and not i.path.endswith(".tmp")
            ),
            key=lambda f: f.path,
        )

    # -- parquet ------------------------------------------------------------------
    def write_parquet(self, rel: str, table: pa.Table) -> None:
        buf = io.BytesIO()
        pq.write_table(table, buf, compression="zstd")
        self.write(rel, buf.getvalue())

    def read_parquet(self, rel: str, columns: list[str] | None = None) -> pa.Table:
        return pq.read_table(self.abs(rel), filesystem=self.fs, columns=columns)

    def parquet_metadata(self, rel: str) -> pq.FileMetaData:
        with self.fs.open_input_file(self.abs(rel)) as f:
            return pq.ParquetFile(f).metadata


def open_lake(uri: str | None = None) -> Lake:
    """``file://./lake-data`` (padrão) ou ``s3://bucket[/prefixo]`` (MinIO/S3)."""
    uri = uri or os.environ.get("LAKE_URI", "file://./lake-data")
    if uri.startswith("file://"):
        root = os.path.abspath(uri[len("file://") :])
        return Lake(pafs.LocalFileSystem(), root, local=True)
    if uri.startswith("s3://"):
        fs = pafs.S3FileSystem(
            access_key=os.environ.get("LAKE_S3_ACCESS_KEY", "lakeaccess"),
            secret_key=os.environ.get("LAKE_S3_SECRET_KEY", "lakesecret123"),
            endpoint_override=os.environ.get("LAKE_S3_ENDPOINT", "localhost:8333"),
            scheme=os.environ.get("LAKE_S3_SCHEME", "http"),
            region="us-east-1",
            allow_bucket_creation=True,
        )
        return Lake(fs, uri[len("s3://") :], local=False)
    raise ValueError(f"URI não suportada: {uri!r} (use file://… ou s3://…)")
