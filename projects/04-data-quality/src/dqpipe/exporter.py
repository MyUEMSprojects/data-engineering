"""Exporter mínimo (stdlib): serve o arquivo de métricas em /metrics para o Prometheus raspar."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def make_handler(metrics_file: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path not in ("/metrics", "/"):
                self.send_error(404)
                return
            body = metrics_file.read_bytes() if metrics_file.exists() else b"# sem metricas ainda\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # silencia o log por request
            pass

    return Handler


def serve(metrics_file: Path, host: str = "0.0.0.0", port: int = 9108) -> None:  # noqa: S104
    print(f"exporter: servindo {metrics_file} em http://{host}:{port}/metrics")
    HTTPServer((host, port), make_handler(metrics_file)).serve_forever()


if __name__ == "__main__":  # `python -m dqpipe.exporter` — só stdlib (imagem mínima, sem duckdb)
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", default="out/metrics/dq.prom")
    ap.add_argument("--port", type=int, default=9108)
    a = ap.parse_args()
    serve(Path(a.metrics), port=a.port)
