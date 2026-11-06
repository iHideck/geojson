"""外部の道具（mapshaper など）を呼ぶ。"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import zipfile
from pathlib import Path

from boundaries.registry import ROOT


def cache_key(*settings: object) -> str:
    """途中のファイルの名前に付ける短いハッシュ。作り方の設定が変われば、別のファイルになる。"""
    return hashlib.sha256(repr(settings).encode()).hexdigest()[:12]


def mapshaper(*args: str | Path) -> None:
    exe = shutil.which("mapshaper") or str(ROOT / "node_modules" / ".bin" / "mapshaper")
    subprocess.run([exe, "-quiet", *map(str, args)], check=True)


def unzip(archive: Path, dest: Path, members: list[str] | None = None) -> Path:
    """取り出し済みなら何もしない。途中で止まっても、目印のファイルが無いので次に取り出し直す。"""
    done = dest / ".unzipped"
    if not done.exists():
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            z.extractall(dest, members=members)
        done.write_text(archive.name)
    return dest
