"""公開するデータの一覧を、STAC 1.0 のカタログにする。GitHub Pages の stac/ に置く。

リンクはカタログの中では相対パスで、データの資産は GitHub Pages（ブラウザから読める形式）か、リリースの URL を指す。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from boundaries import distribution, geo
from boundaries.distribution import FORMATS, PAGES, RELEASE
from boundaries.registry import Layer, Registry

STAC_VERSION = "1.0.0"
FILE_EXTENSION = "https://stac-extensions.github.io/file/v2.1.0/schema.json"
JSON = "application/json"


def _bbox(geojson: Path) -> list[float]:
    xs, ys = [], []
    for f in geo.load(geojson)["features"]:
        for ring in geo.rings(f["geometry"]):
            xs.extend(p[0] for p in ring)
            ys.extend(p[1] for p in ring)
    return [min(xs), min(ys), max(xs), max(ys)]


def _datetime(reg: Registry, layer: Layer) -> str:
    """元データを取得した日のうち、最も古い日。"""
    return f"{min(s.retrieved for s in reg.sources_for([layer]) if s.retrieved).isoformat()}T00:00:00Z"


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


def item(reg: Registry, layer: Layer, resolution: str, dist: Path) -> dict:
    bbox = _bbox(dist / layer.id / f"{resolution}.geojson")
    west, south, east, north = bbox
    assets = {}
    for fmt in FORMATS.values():
        name = distribution.release_name(layer, resolution, fmt.id)
        path = dist / "release" / name
        page = distribution.pages_path(layer, resolution, fmt.id)
        assets[fmt.id] = {
            "href": f"{PAGES}/{page}" if page else f"{RELEASE}/{name}",
            "type": fmt.media_type,
            "roles": ["data"],
            "file:size": path.stat().st_size,
            "file:checksum": "1220" + hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return {
        "type": "Feature",
        "stac_version": STAC_VERSION,
        "stac_extensions": [FILE_EXTENSION],
        "id": f"{layer.slug}-{resolution}",
        "collection": layer.slug,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
        },
        "bbox": bbox,
        "properties": {
            "title": f"{layer.title_ja} {resolution} / {layer.title_en} {resolution}",
            "datetime": _datetime(reg, layer),
            "license": layer.license,
        },
        "links": [
            {"rel": "root", "href": "../catalog.json", "type": JSON},
            {"rel": "parent", "href": "./collection.json", "type": JSON},
            {"rel": "collection", "href": "./collection.json", "type": JSON},
        ],
        "assets": assets,
    }


def build(reg: Registry, layers: list[Layer], dist: Path, out: Path) -> Path:
    catalog_links = [{"rel": "root", "href": "./catalog.json", "type": JSON}]
    for layer in layers:
        items = {res.id: item(reg, layer, res.id, dist) for res in layer.resolutions}
        boxes = [i["bbox"] for i in items.values()]
        bbox = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
        for res_id, doc in items.items():
            _write(out / layer.slug / f"{res_id}.json", doc)
        _write(
            out / layer.slug / "collection.json",
            {
                "type": "Collection",
                "stac_version": STAC_VERSION,
                "stac_extensions": [FILE_EXTENSION],
                "id": layer.slug,
                "title": f"{layer.title_ja} / {layer.title_en}",
                "description": f"{layer.title_ja}（{layer.title_en}）。{layer.credit_ja}",
                "license": layer.license,
                "extent": {
                    "spatial": {"bbox": [bbox]},
                    "temporal": {"interval": [[_datetime(reg, layer), None]]},
                },
                "links": [
                    {"rel": "root", "href": "../catalog.json", "type": JSON},
                    {"rel": "parent", "href": "../catalog.json", "type": JSON},
                    {"rel": "describedby", "href": f"{PAGES}/{distribution.metadata_path(layer)}", "type": JSON},
                    *({"rel": "item", "href": f"./{res_id}.json", "type": "application/geo+json"} for res_id in items),
                ],
            },
        )
        catalog_links.append({"rel": "child", "href": f"./{layer.slug}/collection.json", "type": JSON})
    _write(
        out / "catalog.json",
        {
            "type": "Catalog",
            "stac_version": STAC_VERSION,
            "id": "geojson-boundaries",
            "title": "geojson — Japan & World Boundaries",
            "description": "日本と世界の陸と海の境界を、同じ基準で重ねて使える軽いオープンデータ集",
            "links": catalog_links,
        },
    )
    return out
