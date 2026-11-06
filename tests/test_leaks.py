"""元データが、git・リリース・GitHub Pages に入っていないことを確かめる。

元データの SHA256 は、台帳（sources/*.yml）の値と、取得済みの zip の中のファイルから求めた値を使う。
配るファイルは、zip の中のファイルと、QGIS プロジェクト（.qgz）の中まで開いて比べる。
"""

import functools
import hashlib
import io
import subprocess
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from boundaries import registry

REG = registry.load()
DIST = registry.ROOT / "dist"
# 元データの zip の中の .cpg（中身は UTF-8 だけ）や .prj は、こちらの Shapefile と同じ中身になりうる。
# 小さなファイルは比べない
MIN_BYTES = 4096


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@functools.cache
def source_digests() -> frozenset[str]:
    digests = {f.sha256 for s in REG.sources.values() for f in s.files if f.sha256}
    for s in REG.sources.values():
        for f in s.files:
            path = registry.cache_dir() / "sources" / s.id / f.name
            if path.exists() and zipfile.is_zipfile(path):
                with zipfile.ZipFile(path) as z:
                    for info in z.infolist():
                        if not info.is_dir() and info.file_size >= MIN_BYTES:
                            with z.open(info) as fh:
                                digests.add(hashlib.file_digest(fh, "sha256").hexdigest())
    return frozenset(digests)


def unpacked(name: str, data: bytes) -> Iterator[tuple[str, bytes]]:
    """ファイルと、zip（.qgz を含む）の中のファイルを、入れ子まで開いて返す。"""
    yield name, data
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for info in z.infolist():
                if not info.is_dir():
                    yield from unpacked(f"{name}/{info.filename}", z.read(info))


def tracked() -> list[Path]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=registry.ROOT, capture_output=True)
    if result.returncode != 0:
        pytest.skip("git の作業ツリーではない（make build のイメージの中の worktree など）")
    return [registry.ROOT / p for p in result.stdout.decode().split("\0") if p]


@pytest.mark.parametrize("where", ["git", "release", "pages"])
def test_no_source_file_is_redistributed(where):
    if where == "git":
        files = [p for p in tracked() if p.is_file()]
    else:
        folder = DIST / where
        if not folder.exists():
            pytest.skip(f"dist/{where} がまだ作られていない（make build で作る）")
        files = [p for p in folder.rglob("*") if p.is_file()]
    sources = source_digests()
    leaked = [
        name
        for path in files
        for name, data in unpacked(str(path.relative_to(registry.ROOT)), path.read_bytes())
        if digest(data) in sources
    ]
    assert leaked == []
