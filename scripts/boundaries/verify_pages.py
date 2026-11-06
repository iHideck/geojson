"""公開した GitHub Pages を確かめる。デプロイの後に動かす。

- ビューア・目録・STAC のカタログを読める
- 目録にある PMTiles と、metadata.json にある FlatGeobuf のすべてが、Range 要求に 206 を返し、CORS を許す
- 公開していないレイヤー（海域や、確認を待つレイヤー）のファイルが無い

使い方: python -m boundaries.verify_pages https://ihideck.github.io/geojson/
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

from boundaries import distribution, registry

USER_AGENT = "geojson-boundaries-verify"


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict[str, str]
    body: bytes


def get(url: str, range_: str | None = None) -> Response:
    headers = {"User-Agent": USER_AGENT, "Origin": "https://example.org"}
    if range_:
        headers["Range"] = range_
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as r:
            return Response(r.status, {k.lower(): v for k, v in r.headers.items()}, r.read())
    except urllib.error.HTTPError as e:
        return Response(e.code, {k.lower(): v for k, v in e.headers.items()}, b"")


def check(base: str) -> list[str]:
    base = base.rstrip("/") + "/"
    problems: list[str] = []
    for path in ("", f"{distribution.PAGES_DATA}/catalog.json", f"{distribution.STAC}/catalog.json"):
        if (status := get(base + path).status) != 200:
            problems.append(f"{base + path}: {status}")
    catalog = json.loads(get(f"{base}{distribution.PAGES_DATA}/catalog.json").body or b'{"layers": []}')
    ranged = [res["pmtiles"] for layer in catalog["layers"] for res in layer["resolutions"]]
    for layer in catalog["layers"]:
        meta = json.loads(get(base + layer["metadata"]).body or b'{"resolutions": []}')
        for res in meta["resolutions"]:
            ranged += [
                f["pages_url"].removeprefix(f"{distribution.PAGES}/") for f in res["files"] if f["format"] == "fgb"
            ]
    if not ranged:
        problems.append("目録に PMTiles が無い")
    for path in ranged:
        r = get(base + path, "bytes=0-15")
        if r.status != 206 or len(r.body) != 16:
            problems.append(f"{path}: Range 要求に {r.status}（{len(r.body)} バイト）")
        if r.headers.get("access-control-allow-origin") != "*":
            problems.append(f"{path}: CORS を許していない")
    published = {layer["id"] for layer in catalog["layers"]}
    for layer in registry.load().layers:
        if layer.id in published or layer.publish:
            continue
        path = distribution.pages_path(layer, layer.resolutions[0].id, "pmtiles")
        if (status := get(base + path).status) != 404:
            problems.append(f"公開していないレイヤーのファイルがある: {path}（{status}）")
    return problems


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(__doc__)
        return 2
    problems = check(args[0])
    for p in problems:
        print(f"問題: {p}")
    if not problems:
        print(f"確かめた: {args[0]}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
