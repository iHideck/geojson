"""配布形式を作る。イメージの中（GDAL と tippecanoe がある所）で動かす。

dist/<レイヤー>/<解像度>.geojson から、公開するレイヤーについて次を作る。
- dist/release/: GitHub Release に載せるファイル（全形式、GeoPackage、QGIS プロジェクト、スタイル、SHA256SUMS）
- dist/pages/: GitHub Pages に置くデータ（latest/ に PMTiles・FlatGeobuf・GeoJSON・metadata.json、stac/ に STAC）。
  ビューアとは別のフォルダーにし、デプロイのときに合わせる
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import zipfile
from pathlib import Path

from boundaries import distribution, qgis_project, registry, site_index, stac, styles, tools
from boundaries.limits import CSV_LIMIT
from boundaries.package import attributes_csv
from boundaries.registry import Layer, Registry, Resolution

DIST = registry.ROOT / "dist"
# 作り直しても同じバイト列になるよう、ファイルの中の日時を固定する
FIXED_DATE = "2026-01-01T00:00:00Z"
ZIP_DATE = (2026, 1, 1, 0, 0, 0)
# ここで作る形式。GeoJSON と TopoJSON は、レイヤーを作るとき（boundaries.build）に作る
MADE_HERE = ("fgb", "parquet", "shp", "pmtiles")


def _env() -> dict[str, str]:
    return {**os.environ, "OGR_CURRENT_DATE": FIXED_DATE}


def _ogr(*args: str | Path) -> None:
    subprocess.run(["ogr2ogr", *map(str, args)], check=True, env=_env())


def _zip(paths: list[Path], dest: Path) -> Path:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for path in paths:
            info = zipfile.ZipInfo(path.name, ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            # 権限を書かないと、展開したファイルを読めない環境がある
            info.external_attr = 0o644 << 16
            z.writestr(info, path.read_bytes())
    return dest


def flatgeobuf(layer: Layer, resolution: str, geojson: Path) -> Path:
    out = geojson.with_suffix(".fgb")
    out.unlink(missing_ok=True)
    _ogr(
        "-f", "FlatGeobuf", "-lco", "SPATIAL_INDEX=YES", "-lco", f"TITLE={layer.title_ja} {resolution}",
        "-lco", f"DESCRIPTION={layer.credit_ja}", "-nln", distribution.table_name(layer, resolution), out, geojson,
    )  # fmt: skip
    return out


def geoparquet(layer: Layer, resolution: str, geojson: Path) -> Path:
    out = geojson.with_suffix(".parquet")
    out.unlink(missing_ok=True)
    _ogr("-f", "Parquet", "-lco", "COMPRESSION=ZSTD", "-nln", distribution.table_name(layer, resolution), out, geojson)
    return out


def shapefile_zip(layer: Layer, resolution: str, geojson: Path, work: Path, license_file: Path) -> Path:
    table = distribution.table_name(layer, resolution)
    folder = work / f"{table}-shp"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    _ogr(
        "-f", "ESRI Shapefile", "-lco", "ENCODING=UTF-8", "-lco", f"DBF_DATE_LAST_UPDATE={FIXED_DATE[:10]}",
        "-nln", table, folder, geojson,
    )  # fmt: skip
    parts = sorted(folder.iterdir())
    if not any(p.suffix == ".cpg" for p in parts):
        raise RuntimeError(f"{table}: Shapefile に .cpg が無い")
    return _zip([*parts, license_file], geojson.with_name(f"{resolution}.shp.zip"))


def pmtiles(layer: Layer, res: Resolution, geojson: Path, work: Path) -> Path:
    """面のレイヤーは、塗りの面と、隣と接する境界の線（borders）の2つのタイルレイヤーにする。

    ズームは登録表の範囲で作り、上限より先はビューアが拡大して描く。
    """
    out = geojson.with_suffix(".pmtiles")
    out.unlink(missing_ok=True)
    inputs = ["-L", f"{layer.id.split('/')[-1]}:{geojson}"]
    if layer.geometry == "polygon":
        lines = work / f"{distribution.table_name(layer, res.id)}-borders.geojson"
        # 属性の無い線は GeometryCollection で書かれ、tippecanoe が地物として読まないので、FeatureCollection にする
        tools.mapshaper("-i", geojson, "-innerlines", "-o", "format=geojson", "geojson-type=FeatureCollection", lines)
        inputs += ["-L", f"borders:{lines}"]
    # 点は、低いズームでも間引かない（-r1）。面は、小さな島を四角に置き換えない
    shape = ["-r1"] if layer.geometry == "point" else ["--no-tiny-polygon-reduction", "--detect-shared-borders"]
    subprocess.run(
        [
            "tippecanoe", "-o", str(out), "-q", "-Z", str(res.minzoom), "-z", str(res.maxzoom),
            "--no-tile-size-limit", "--simplification=2", "--generate-ids", *shape, "-n", f"{layer.title_ja} {res.id}",
            "-N", f"{layer.title_en} {res.id}", "-A", layer.credit_ja, *inputs,
        ],
        check=True,
        env=_env(),
    )  # fmt: skip
    return out


def geopackage(layers: list[Layer], dist: Path, dest: Path) -> Path:
    """公開する全レイヤーを1つの GeoPackage にまとめ、QGIS が最初に使うスタイルを layer_styles に入れる。"""
    dest.unlink(missing_ok=True)
    table_styles = styles.load()
    for layer in layers:
        for res in layer.resolutions:
            _ogr(
                "-f", "GPKG", "-append" if dest.exists() else "-overwrite",
                "-lco", f"IDENTIFIER={layer.title_ja} {res.id}", "-lco", f"DESCRIPTION={layer.credit_ja}",
                "-nln", distribution.table_name(layer, res.id), dest, dist / layer.id / f"{res.id}.geojson",
            )  # fmt: skip
    with sqlite3.connect(dest) as db:
        db.executescript(
            """
            CREATE TABLE layer_styles (
              id INTEGER PRIMARY KEY AUTOINCREMENT, f_table_catalog TEXT(256), f_table_schema TEXT(256),
              f_table_name TEXT(256), f_geometry_column TEXT(256), styleName TEXT(30), styleQML TEXT,
              styleSLD TEXT, useAsDefault BOOLEAN, description TEXT, owner TEXT(30), ui TEXT(30), update_time DATETIME
            );
            """
        )
        for layer in layers:
            style = table_styles[layer.id]
            for res in layer.resolutions:
                title = f"{layer.title_ja} {res.id}"
                db.execute(
                    "INSERT INTO layer_styles (f_table_catalog, f_table_schema, f_table_name, f_geometry_column, "
                    "styleName, styleQML, styleSLD, useAsDefault, description, owner, ui, update_time) "
                    "VALUES ('', '', ?, 'geom', ?, ?, ?, 1, ?, '', '', ?)",
                    (
                        distribution.table_name(layer, res.id), title, styles.qml(style),
                        styles.sld(style, title), layer.credit_ja, FIXED_DATE,
                    ),
                )  # fmt: skip
        db.execute(
            "INSERT INTO gpkg_contents (table_name, data_type, identifier, description, last_change) "
            "VALUES ('layer_styles', 'attributes', 'layer_styles', '', ?)",
            (FIXED_DATE,),
        )
    return dest


def style_zip(layers: list[Layer], work: Path, dest: Path) -> Path:
    folder = work / "styles"
    folder.mkdir()
    table_styles = styles.load()
    return _zip([path for layer in layers for path in styles.write(layer, table_styles[layer.id], folder)], dest)


def record_files(metadata: Path, layer: Layer, sizes: dict[str, dict[str, int]]) -> None:
    """metadata.json の解像度ごとのファイルの一覧に、ここで作った形式を書く。

    前の行は置き換えるので、何度動かしても同じになる。
    """
    meta = json.loads(metadata.read_text())
    for res in meta["resolutions"]:
        made = sizes[res["id"]]
        kept = [f for f in res["files"] if f["format"] not in made]
        res["files"] = kept + [distribution.file_entry(layer, res["id"], fmt, size) for fmt, size in made.items()]
    metadata.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def write_sums(folder: Path) -> Path:
    lines = [
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}"
        for p in sorted(folder.iterdir())
        if p.name != distribution.SUMS
    ]
    out = folder / distribution.SUMS
    out.write_text("\n".join(lines) + "\n")
    return out


def build_all(reg: Registry, dist: Path = DIST) -> list[Path]:
    layers = [layer for layer in reg.layers if layer.enabled and layer.publish]
    work = registry.cache_dir() / "work" / "formats"
    release, site = dist / "release", dist / "pages"
    for folder in (work, release, site):
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
    license_file = Path(shutil.copyfile(registry.ROOT / distribution.LICENSE, release / distribution.LICENSE))
    for layer in layers:
        sizes = {}
        for res in layer.resolutions:
            geojson = dist / layer.id / f"{res.id}.geojson"
            outputs = {
                "geojson": geojson,
                "topojson": geojson.with_suffix(".topojson"),
                "fgb": flatgeobuf(layer, res.id, geojson),
                "parquet": geoparquet(layer, res.id, geojson),
                "shp": shapefile_zip(layer, res.id, geojson, work, license_file),
                "pmtiles": pmtiles(layer, res, geojson, work),
            }
            for fmt, path in outputs.items():
                shutil.copyfile(path, release / distribution.release_name(layer, res.id, fmt))
                if page := distribution.pages_path(layer, res.id, fmt):
                    (site / page).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, site / page)
            sizes[res.id] = {fmt: outputs[fmt].stat().st_size for fmt in MADE_HERE}
        metadata = dist / layer.id / "metadata.json"
        record_files(metadata, layer, sizes)
        shutil.copyfile(metadata, site / distribution.metadata_path(layer))
        table = attributes_csv(
            dist / layer.id / f"{layer.resolutions[0].id}.geojson", [a.name for a in layer.attributes]
        )
        if len(table.encode()) <= CSV_LIMIT:
            (release / distribution.csv_name(layer)).write_text(table)
    site_index.write(layers, dist, site)
    gpkg = geopackage(layers, dist, release / distribution.GPKG)
    qgz = qgis_project.write_qgz(layers, gpkg, work / "geojson-boundaries.qgz", ZIP_DATE)
    _zip([qgz, gpkg, license_file], release / distribution.QGIS_ZIP)
    style_zip(layers, work, release / distribution.STYLES_ZIP)
    write_sums(release)
    stac.build(reg, layers, dist, site / distribution.STAC)
    return sorted(p for p in (*release.iterdir(), *site.rglob("*")) if p.is_file())


def main() -> int:
    for path in build_all(registry.load()):
        print(f"作った: {path.relative_to(registry.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
