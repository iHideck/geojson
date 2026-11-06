"""ビューアが読む目録（catalog.json）と検索の索引（search.json）を作り、GitHub Pages の latest/ に置く。

パスは、GitHub Pages のサイトの根からの相対パスで書く。ビューアは、自分の置き場所（/geojson/）に足して読む。
検索の索引は、地物を最も細かい解像度の GeoJSON と同じ順に並べる。PMTiles の地物の番号（tippecanoe の
--generate-ids）も同じ順なので、ビューアは地図の上の地物から索引の行を番号で引ける。
"""

from __future__ import annotations

import json
from pathlib import Path

from boundaries import distribution, geo
from boundaries.registry import Layer

CATALOG = f"{distribution.PAGES_DATA}/catalog.json"
SEARCH = f"{distribution.PAGES_DATA}/search.json"


def catalog(layers: list[Layer]) -> dict:
    return {
        "layers": [
            {
                "id": layer.id,
                "title": {"ja": layer.title_ja, "en": layer.title_en},
                "geometry": layer.geometry,
                "credit": {"ja": layer.credit_ja, "en": layer.credit_en},
                "license": layer.license,
                "metadata": distribution.metadata_path(layer),
                "resolutions": [
                    {
                        "id": res.id,
                        "minzoom": res.minzoom,
                        "maxzoom": res.maxzoom,
                        "pmtiles": distribution.pages_path(layer, res.id, "pmtiles"),
                    }
                    for res in layer.resolutions
                ],
            }
            for layer in layers
        ]
    }


def bbox(geometry: dict) -> list[float]:
    """地物を囲む範囲 [西, 南, 東, 北]。180度線をまたぐ地物は、東の端を 180 より大きくして、狭いほうを返す。"""
    lons, lats = [], []
    for ring in geo.rings(geometry):
        lons.extend(p[0] for p in ring)
        lats.extend(p[1] for p in ring)
    west, east = min(lons), max(lons)
    shifted = [lon + 360 if lon < 0 else lon for lon in lons]
    if max(shifted) - min(shifted) < east - west:
        west, east = min(shifted), max(shifted)
    return [round(west, 3), round(min(lats), 3), round(east, 3), round(max(lats), 3)]


def search_index(layers: list[Layer], dist: Path) -> dict:
    entries = {}
    for layer in layers:
        features = geo.load(dist / layer.id / f"{layer.resolutions[0].id}.geojson")["features"]
        entries[layer.id] = [
            {**{k: v for k, v in f["properties"].items() if v is not None}, "bbox": bbox(f["geometry"])}
            for f in features
        ]
    return {"layers": entries}


def write(layers: list[Layer], dist: Path, site: Path) -> list[Path]:
    written = []
    for path, doc in ((CATALOG, catalog(layers)), (SEARCH, search_index(layers, dist))):
        out = site / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
        written.append(out)
    return written
