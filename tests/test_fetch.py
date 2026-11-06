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
