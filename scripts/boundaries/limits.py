"""解像度とサイズの上限。検査と docs/size-report.md は、この表だけを見る。"""

from __future__ import annotations

MB = 1024 * 1024

# 形式ごとの1ファイルの上限（バイト）。GeoJSON と TopoJSON は目標が 5MB で、上限が 10MB
FILE_LIMITS = {
    "geojson": 10 * MB,
    "topojson": 10 * MB,
    "pmtiles": 50 * MB,
    "gpkg": 100 * MB,
    "shp": 100 * MB,
    "fgb": 100 * MB,
    "parquet": 100 * MB,
    "qgz": 100 * MB,
}
JSON_TARGET = 5 * MB
TRACKED_FILE_LIMIT = 10 * MB
SITE_TOTAL_LIMIT = 200 * MB
CSV_LIMIT = 512 * 1024
