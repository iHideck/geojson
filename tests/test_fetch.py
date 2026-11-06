import hashlib
from pathlib import Path

import pytest

from boundaries import fetch
from boundaries.registry import Source, SourceFile


def make_source(tmp_path: Path, payload: bytes, sha256: str | None, manual: bool = False) -> Source:
    origin = tmp_path / "origin.bin"
    origin.write_bytes(payload)
    file = SourceFile(url=origin.as_uri(), name="data.bin", sha256=sha256, bytes=len(payload))
    return Source(
        id="sample",
        title="sample",
        publisher="test",
        version="1",
        retrieved=None,
        license="CC0-1.0",
        license_url="https://example.org/license",
        page_url="https://example.org/",
        manual=manual,
        legacy_tls=False,
        files=(file,),
    )


def test_a_file_with_the_recorded_checksum_is_kept(tmp_path):
    payload = b"boundary"
    source = make_source(tmp_path, payload, hashlib.sha256(payload).hexdigest())
    [path] = fetch.ensure(source, tmp_path / "cache")
    assert path.read_bytes() == payload


def test_a_checksum_mismatch_stops_and_leaves_no_file(tmp_path):
    source = make_source(tmp_path, b"changed upstream", hashlib.sha256(b"original").hexdigest())
    cache = tmp_path / "cache"
    with pytest.raises(fetch.ChecksumMismatch, match="SHA256 が台帳と違う"):
        fetch.ensure(source, cache)
    assert list((cache / "sample").iterdir()) == []


def test_a_corrupted_cached_file_is_downloaded_again(tmp_path):
    payload = b"boundary"
    source = make_source(tmp_path, payload, hashlib.sha256(payload).hexdigest())
    cache = tmp_path / "cache"
    (cache / "sample").mkdir(parents=True)
    (cache / "sample" / "data.bin").write_bytes(b"truncated")
    [path] = fetch.ensure(source, cache)
    assert path.read_bytes() == payload


def test_a_manual_source_that_is_missing_asks_for_a_manual_download(tmp_path):
    source = make_source(tmp_path, b"x", None, manual=True)
    with pytest.raises(fetch.ManualDownloadRequired, match="手で取得"):
        fetch.ensure(source, tmp_path / "cache")


def test_update_rewrites_the_checksum_size_and_date(tmp_path):
    payload = b"new version"
    source = make_source(tmp_path, payload, "0" * 64)
    ledger = tmp_path / "sample.yml"
    ledger.write_text(
        "id: sample\nretrieved: 2020-01-01\nfiles:\n"
        f"  - url: {source.files[0].url}\n    name: data.bin\n    sha256: {'0' * 64}\n    bytes: 1\n"
    )
    fetch.update(source, tmp_path / "cache", ledger)
    text = ledger.read_text()
    assert f"sha256: {hashlib.sha256(payload).hexdigest()}" in text
    assert f"bytes: {len(payload)}" in text
    assert "retrieved: 2020-01-01" not in text


def test_legacy_renegotiation_is_allowed_only_when_the_ledger_asks():
    assert fetch.tls_context(legacy=True).options & fetch.ssl.OP_LEGACY_SERVER_CONNECT
    assert not fetch.tls_context(legacy=False).options & fetch.ssl.OP_LEGACY_SERVER_CONNECT


class FlakyServer:
    """最初の何回かは指定の状態を返し、そのあと中身を返す、検査用のサーバー。"""

    def __init__(self, failures: int, status: int, retry_after: str | None):
        import http.server
        import threading

        self.calls = 0
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                outer.calls += 1
                if outer.calls <= failures:
                    self.send_response(status)
                    if retry_after is not None:
                        self.send_header("Retry-After", retry_after)
                    self.end_headers()
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"payload")

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/data.bin"

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def test_a_busy_server_is_retried_after_the_time_it_asks(tmp_path, monkeypatch):
    waits = []
    monkeypatch.setattr(fetch.time, "sleep", waits.append)
    server = FlakyServer(failures=2, status=429, retry_after="3")
    try:
        got = fetch.download(server.url, tmp_path / "data.bin")
    finally:
        server.close()
    assert got == hashlib.sha256(b"payload").hexdigest()
    assert waits == [3.0, 3.0]
    assert server.calls == 3


def test_without_retry_after_the_wait_doubles(tmp_path, monkeypatch):
    waits = []
    monkeypatch.setattr(fetch.time, "sleep", waits.append)
    server = FlakyServer(failures=3, status=503, retry_after=None)
    try:
        fetch.download(server.url, tmp_path / "data.bin")
    finally:
        server.close()
    assert waits == [2.0, 4.0, 8.0]


def test_a_missing_file_is_not_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch.time, "sleep", lambda s: pytest.fail("待ってはいけない"))
    server = FlakyServer(failures=99, status=404, retry_after=None)
    try:
        with pytest.raises(fetch.urllib.error.HTTPError):
            fetch.download(server.url, tmp_path / "data.bin")
    finally:
        server.close()
    assert server.calls == 1
    assert not (tmp_path / "data.bin").exists()
