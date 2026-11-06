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
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from boundaries import registry

USER_AGENT = "geojson-boundaries-build (+https://github.com/iHideck/geojson)"
CHUNK = 1 << 20
# 混んでいるときの返事。待ってからやり直す（Wikidata は、続けて取ると 429 を返す）
RETRY_STATUSES = {429, 500, 502, 503, 504}
ATTEMPTS = 6
# 続けて取得するときに空ける間（秒）
PACE = 0.5


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


def retry_after(error: urllib.error.HTTPError, attempt: int) -> float:
    """待つ秒数。Retry-After の秒数があれば従い、無ければ 2・4・8… 秒（60 秒まで）待つ。"""
    value = error.headers.get("Retry-After") if error.headers else None
    if value and value.strip().isdigit():
        return min(float(value), 300.0)
    return min(2.0 ** (attempt + 1), 60.0)


def download(url: str, dest: Path, legacy_tls: bool = False) -> str:
    for attempt in range(ATTEMPTS):
        try:
            return _download_once(url, dest, legacy_tls)
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_STATUSES or attempt == ATTEMPTS - 1:
                raise
            wait = retry_after(e, attempt)
            print(f"待つ: {url} が {e.code} を返した。{wait:g} 秒後にやり直す", file=sys.stderr)
            time.sleep(wait)
    raise AssertionError("ここには来ない")


def _download_once(url: str, dest: Path, legacy_tls: bool) -> str:
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
        time.sleep(PACE)
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
    for source in reg.inputs_for(reg.enabled_layers()):
        for path in ensure(source, args.cache):
            print(f"確認済み: {path.relative_to(args.cache)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
