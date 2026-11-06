"""GitHub Release の説明を、CHANGELOG.md の版の節から作る。リリースのワークフローが使う。

使い方: python -m boundaries.release_notes v1.2.3
"""

from __future__ import annotations

import re
import sys

from boundaries import registry

FOOTER = """
## 使い方

- 地図で見る: https://ihideck.github.io/geojson/
- 全レイヤーを QGIS で開く: `geojson-boundaries-qgis.zip` を展開し、`.qgz` を開く
- ファイルの SHA256 は `SHA256SUMS` にある（`sha256sum -c SHA256SUMS`）
- この版の URL は `https://github.com/iHideck/geojson/releases/download/{tag}/<ファイル名>`

## ライセンスとクレジット

データを使うときは、使ったレイヤーのクレジットを書いてください。書き方は `DATA_LICENSE.md` にあります。

境界は法的な境界を示しません。航海など、安全に関わる用途には使えません。
"""


def notes(tag: str, changelog: str) -> str:
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError(f"タグは v1.2.3 の形にする: {tag}")
    version = tag[1:]
    match = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", changelog, re.M | re.S)
    if not match or not match.group(1).strip():
        raise ValueError(f"CHANGELOG.md に {version} の節が無い。Unreleased の中身を移してからタグを打つ")
    return match.group(1).strip() + "\n" + FOOTER.format(tag=tag)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    print(notes(args[0], (registry.ROOT / "CHANGELOG.md").read_text()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
