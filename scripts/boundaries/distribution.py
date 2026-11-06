"""配布するファイルの名前と置き場所。リリース・GitHub Pages・metadata.json・STAC は、この表から名前と URL を作る。"""

from __future__ import annotations

from dataclasses import dataclass

from boundaries.registry import Layer

PAGES = "https://ihideck.github.io/geojson"
RELEASE = "https://github.com/iHideck/geojson/releases/latest/download"
# GitHub Pages では、データを latest/ の下に置く。版を固定した URL は、リリースと jsDelivr（data/）で出す
PAGES_DATA = "latest"
STAC = "stac"

GPKG = "geojson-boundaries.gpkg"
QGIS_ZIP = "geojson-boundaries-qgis.zip"
STYLES_ZIP = "geojson-boundaries-styles.zip"
LICENSE = "DATA_LICENSE.md"
SUMS = "SHA256SUMS"


@dataclass(frozen=True)
class Format:
    id: str
    suffix: str
    media_type: str
    # GitHub Pages にも置く。ブラウザから CORS と Range 要求で読める
    on_pages: bool


FORMATS: dict[str, Format] = {
    f.id: f
    for f in (
        Format("geojson", ".geojson", "application/geo+json", True),
        Format("topojson", ".topojson", "application/json", False),
        Format("fgb", ".fgb", "application/vnd.flatgeobuf", True),
        Format("parquet", ".parquet", "application/vnd.apache.parquet", False),
        Format("shp", ".shp.zip", "application/zip", False),
        Format("pmtiles", ".pmtiles", "application/vnd.pmtiles", True),
    )
}


def table_name(layer: Layer, resolution: str) -> str:
    """GeoPackage・FlatGeobuf・GeoParquet・Shapefile のレイヤー名。"""
    return f"{layer.slug.replace('-', '_')}_{resolution}"


def release_name(layer: Layer, resolution: str, fmt: str) -> str:
    return f"{layer.slug}-{resolution}{FORMATS[fmt].suffix}"


def csv_name(layer: Layer) -> str:
    return f"{layer.slug}-attributes.csv"


def pages_path(layer: Layer, resolution: str, fmt: str) -> str | None:
    if not FORMATS[fmt].on_pages:
        return None
    return f"{PAGES_DATA}/{layer.id}/{resolution}{FORMATS[fmt].suffix}"


def metadata_path(layer: Layer) -> str:
    return f"{PAGES_DATA}/{layer.id}/metadata.json"


def file_entry(layer: Layer, resolution: str, fmt: str, size: int) -> dict:
    """metadata.json の、解像度ごとのファイルの一覧の1行。"""
    name = release_name(layer, resolution, fmt)
    entry = {"format": fmt, "name": name, "bytes": size, "url": f"{RELEASE}/{name}"}
    if path := pages_path(layer, resolution, fmt):
        entry["pages_url"] = f"{PAGES}/{path}"
    return entry
