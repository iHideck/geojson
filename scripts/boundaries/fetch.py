"""有効なレイヤーが使う元データを取得し、台帳の SHA256 と照合する。

使い方:
    python -m boundaries.fetch               # 足りないものを取得して照合する
    python -m boundaries.fetch --update ID   # 版を上げたあと、取り直して台帳の sha256・bytes・retrieved を書き換える
"""

from __future__ import annotations

import argparse
import hashlib
import re
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

from boundaries import registry

USER_AGENT = "geojson-boundaries-build (+https://github.com/iHideck/geojson)"
CHUNK = 1 << 20


class ChecksumMismatch(RuntimeError):
    pass


class ManualDownloadRequired(RuntimeError):
    pass


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def tls_context(legacy: bool) -> ssl.SSLContext:
    context = ssl.create_default_context()
    if legacy:
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT
    return context


def download(url: str, dest: Path, legacy_tls: bool = False) -> str:
    """dest.part に書いてから名前を変え、途中で止まっても壊れたファイルを残さない。"""
    part = dest.with_name(dest.name + ".part")
    digest = hashlib.sha256()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = tls_context(legacy_tls) if url.startswith("https:") else None
    with urllib.request.urlopen(request, timeout=120, context=context) as response, part.open("wb") as out:
        while chunk := response.read(CHUNK):
            digest.update(chunk)
            out.write(chunk)
    part.replace(dest)
    return digest.hexdigest()


def ensure(source: registry.Source, cache: Path) -> list[Path]:
    paths = []
    for f in source.files:
        dest = cache / source.id / f.name
        if dest.exists() and (f.sha256 is None or sha256_of(dest) == f.sha256):
            paths.append(dest)
            continue
        if source.manual:
            raise ManualDownloadRequired(
                f"{source.id}: {f.url} から {f.name} を手で取得し、{dest} に置く（{source.page_url}）"
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"取得: {f.url}", file=sys.stderr)
        got = download(f.url, dest, source.legacy_tls)
        if got != f.sha256:
            dest.unlink()
            raise ChecksumMismatch(f"{source.id}: {f.name} の SHA256 が台帳と違う（台帳 {f.sha256}、取得 {got}）")
        paths.append(dest)
    return paths


def update(source: registry.Source, cache: Path, ledger: Path) -> None:
    text = ledger.read_text()
    for f in source.files:
        dest = cache / source.id / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        got = download(f.url, dest, source.legacy_tls)
        size = dest.stat().st_size
        block = re.compile(rf"(- url: {re.escape(f.url)}\n(?:    .*\n)*?    sha256: )\S+(\n    bytes: )\S+")
        text, n = block.subn(rf"\g<1>{got}\g<2>{size}", text)
        if n != 1:
            raise RuntimeError(f"{ledger.name}: {f.url} の sha256 と bytes の行が見つからない")
    text = re.sub(r"^retrieved: .*$", f"retrieved: {date.today().isoformat()}", text, count=1, flags=re.M)
    ledger.write_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=registry.cache_dir() / "sources")
    parser.add_argument("--update", metavar="SOURCE_ID")
    args = parser.parse_args(argv)
    reg = registry.load()
    if args.update:
        update(reg.sources[args.update], args.cache, registry.ROOT / "sources" / f"{args.update}.yml")
        return 0
    for source in reg.sources_for(reg.enabled_layers()):
        for path in ensure(source, args.cache):
            print(f"確認済み: {path.relative_to(args.cache)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
