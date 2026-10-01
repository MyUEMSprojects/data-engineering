import pytest

from basic_etl.extract import _get_with_retry, read_api, read_csv


def test_read_csv_respeita_aspas_e_virgulas(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text('id,nome\n1,"Silva, João"\n2,"linha\ncom quebra"\n', encoding="utf-8")
    rows = list(read_csv(p))
    assert rows[0]["nome"] == "Silva, João"
    assert rows[1]["nome"] == "linha\ncom quebra"


def test_read_csv_tolera_bom(tmp_path):
    p = tmp_path / "x.csv"
    p.write_bytes("﻿id,v\n1,a\n".encode())
    assert list(read_csv(p)) == [{"id": "1", "v": "a"}]


class FakeResp:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body or {}, headers or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs.get("params")))
        return self.responses.pop(0)


def test_paginacao_segue_cursor_e_params_so_na_primeira():
    s = FakeSession(
        [
            FakeResp(body={"data": [{"id": 1}, {"id": 2}], "next": "http://api/p2"}),
            FakeResp(body={"data": [{"id": 3}], "next": None}),
        ]
    )
    out = list(read_api(s, "http://api/orders", since="2024-01-01", page_size=2))
    assert [r["id"] for r in out] == [1, 2, 3]
    assert s.calls[0] == ("http://api/orders", {"limit": 2, "since": "2024-01-01"})
    assert s.calls[1] == ("http://api/p2", None)


def test_retry_so_para_transitorios_e_respeita_retry_after():
    sleeps = []
    s = FakeSession([FakeResp(429, headers={"Retry-After": "7"}), FakeResp(503), FakeResp(200)])
    resp = _get_with_retry(s, "u", sleep=sleeps.append)
    assert resp.status_code == 200
    assert sleeps == [7.0, 2.0]  # Retry-After; depois backoff exponencial (1.0 * 2**1)


def test_erro_permanente_nao_e_retentado():
    s = FakeSession([FakeResp(404)])
    with pytest.raises(RuntimeError, match="404"):
        _get_with_retry(s, "u", sleep=lambda _: None)
    assert len(s.calls) == 1


def test_esgota_tentativas():
    s = FakeSession([FakeResp(503)] * 3)
    with pytest.raises(RuntimeError, match="503"):
        _get_with_retry(s, "u", retries=2, sleep=lambda _: None)
    assert len(s.calls) == 3
