"""npm パッケージ japan-world-boundaries の中身を dist/npm/ に組む。公開はしない（npm publish は人が確かめてから）。

入れるのは、公開するレイヤーの軽い GeoJSON（最も粗い解像度）・TopoJSON・metadata.json と、データのライセンス。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from boundaries import registry
from boundaries.registry import Registry

NAME = "japan-world-boundaries"
DIST = registry.ROOT / "dist"
DATA = registry.ROOT / "data"
OUT = DIST / "npm"
# リリースのときに、タグの版に書き換える
VERSION = "0.0.0"
LICENSES = {"CC0-1.0", "CC-BY-4.0"}


def files_for(reg: Registry, dist: Path = DIST, data: Path = DATA) -> dict[str, Path]:
    """パッケージの中のパスと、元にするファイル。"""
    files: dict[str, Path] = {}
    for layer in reg.layers:
        if not (layer.enabled and layer.publish):
            continue
        light = layer.resolutions[-1]
        files[f"{layer.id}/{light.id}.geojson"] = dist / layer.id / f"{light.id}.geojson"
        for res in layer.resolutions:
            files[f"{layer.id}/{res.id}.topojson"] = data / layer.id / f"{res.id}.topojson"
        files[f"{layer.id}/metadata.json"] = data / layer.id / "metadata.json"
    return files


def manifest(reg: Registry, paths: list[str]) -> dict:
    licenses = sorted({layer.license for layer in reg.layers if layer.enabled and layer.publish})
    unknown = set(licenses) - LICENSES
    if unknown:
        raise ValueError(f"npm の license に書けないライセンス: {unknown}")
    return {
        "name": NAME,
        "version": VERSION,
        "description": "Lightweight GeoJSON and TopoJSON boundaries for Japan and the world.",
        "keywords": ["geojson", "topojson", "gis", "japan", "boundaries", "maps", "open-data"],
        "homepage": "https://ihideck.github.io/geojson/",
        "repository": {"type": "git", "url": "git+https://github.com/iHideck/geojson.git"},
        "bugs": "https://github.com/iHideck/geojson/issues",
        "license": f"({' AND '.join(licenses)})" if len(licenses) > 1 else licenses[0],
        "files": sorted(paths) + ["DATA_LICENSE.md"],
        "exports": {"./*": "./*", "./package.json": "./package.json"},
    }


README = """# japan-world-boundaries

日本と世界の境界の、軽い GeoJSON・TopoJSON とメタデータです。

Lightweight GeoJSON and TopoJSON boundaries for Japan and the world.

```js
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const path = require.resolve("japan-world-boundaries/world/countries/110m.geojson");
const countries = JSON.parse(await readFile(path, "utf8"));
```

- 地図で見る / Viewer: https://ihideck.github.io/geojson/
- 全形式（GeoPackage・Shapefile・FlatGeobuf・GeoParquet・PMTiles）/ All formats: https://github.com/iHideck/geojson/releases
- クレジットとライセンス / Credits and licenses: DATA_LICENSE.md

境界は法的な境界を示しません。航海など、安全に関わる用途には使えません。
The boundaries have no legal status and must not be used for navigation or other safety-critical purposes.
"""


def build(reg: Registry, out: Path = OUT, dist: Path = DIST, data: Path = DATA) -> Path:
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    files = files_for(reg, dist, data)
    for path, source in files.items():
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    shutil.copyfile(registry.ROOT / "DATA_LICENSE.md", out / "DATA_LICENSE.md")
    (out / "README.md").write_text(README)
    (out / "package.json").write_text(json.dumps(manifest(reg, list(files)), ensure_ascii=False, indent=2) + "\n")
    return out


def main() -> int:
    print(f"組んだ: {build(registry.load()).relative_to(registry.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
