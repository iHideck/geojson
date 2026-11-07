"""開くだけで全レイヤーがスタイル付きで表示される QGIS プロジェクト（.qgz）を書く。

データは、同じフォルダの GeoPackage を相対パスで参照する。描き方は styles/styles.yml から作った QML と同じ。
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from boundaries import distribution, styles
from boundaries.registry import Layer

TITLE = "geojson — Japan & World Boundaries"
# 上に描くものから順に並べる。面の塗りが線を隠さないよう、国境を一番下にする
ORDER = [
    "japan/islands",
    "world/baselines",
    "japan/municipalities",
    "japan/prefectures",
    "us/states",
    "china/provinces",
    "world/territorial-seas",
    "world/contiguous-zones",
    "world/eez",
    "world/high-seas",
    "world/countries",
]
WKB = {"polygon": ("Polygon", "MultiPolygon"), "line": ("Line", "MultiLineString"), "point": ("Point", "Point")}


def _inner(qml: str, tag: str) -> str:
    match = re.search(rf"<{tag}\b.*?</{tag}>", qml, re.S)
    return match.group(0) if match else ""


def project_xml(layers: list[Layer], gpkg_name: str) -> str:
    table_styles = styles.load()
    ordered = sorted(layers, key=lambda layer: ORDER.index(layer.id))
    tree, maplayers = [], []
    for layer in ordered:
        qml = styles.qml(table_styles[layer.id])
        geometry, wkb = WKB[layer.geometry]
        for res in layer.resolutions:
            table = distribution.table_name(layer, res.id)
            source = f"./{gpkg_name}|layername={table}"
            name = f"{layer.title_ja} {res.id}"
            # 最も細かい解像度だけを表示し、ほかはチェックを外して入れておく
            checked = "Qt::Checked" if res == layer.resolutions[0] else "Qt::Unchecked"
            tree.append(
                f'<layer-tree-layer id="{table}" name={quoteattr(name)} source={quoteattr(source)} '
                f'providerKey="ogr" checked="{checked}" expanded="0"><customproperties/></layer-tree-layer>'
            )
            labels = "1" if 'labelsEnabled="1"' in qml else "0"
            maplayers.append(
                f'<maplayer type="vector" geometry="{geometry}" wkbType="{wkb}" labelsEnabled="{labels}" '
                'styleCategories="AllStyleCategories">'
                f"<id>{table}</id><datasource>{escape(source)}</datasource>"
                f"<layername>{escape(name)}</layername>"
                '<srs><spatialrefsys nativeFormat="Wkt"><authid>EPSG:4326</authid></spatialrefsys></srs>'
                f'<provider encoding="UTF-8">ogr</provider>{_inner(qml, "renderer-v2")}{_inner(qml, "labeling")}'
                "</maplayer>"
            )
    return (
        "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"
        f'<qgis projectname={quoteattr(TITLE)} version="3.30.1">'
        f'<homePath path=""/><title>{escape(TITLE)}</title>'
        '<projectCrs><spatialrefsys nativeFormat="Wkt"><authid>EPSG:4326</authid></spatialrefsys></projectCrs>'
        f"<layer-tree-group><customproperties/>{''.join(tree)}</layer-tree-group>"
        f"<projectlayers>{''.join(maplayers)}</projectlayers>"
        '<properties><Paths><Absolute type="bool">false</Absolute></Paths></properties>'
        "</qgis>\n"
    )


def write_qgz(layers: list[Layer], gpkg: Path, dest: Path, zip_date: tuple[int, ...]) -> Path:
    """.qgz は、プロジェクトの .qgs を1つ入れた zip。作り直しても同じバイト列になるよう日時を固定する。"""
    xml = project_xml(layers, gpkg.name)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo(dest.with_suffix(".qgs").name, zip_date)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, xml)
    return dest
