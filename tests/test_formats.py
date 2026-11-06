"""配布形式を確かめる。dist/release と dist/pages を使う検査は、make build の後に動く。"""

import gzip
import hashlib
import json
import re
import shutil
import sqlite3
import struct
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

from boundaries import distribution, geo, qgis_project, registry, site_index, styles
from boundaries.distribution import FORMATS
from boundaries.limits import FILE_LIMITS, SITE_TOTAL_LIMIT
from range_server import serve

REG = registry.load()
PUBLISHED = [layer for layer in REG.layers if layer.enabled and layer.publish]
DIST = registry.ROOT / "dist"
RELEASE = DIST / "release"
SITE = DIST / "pages"
HAS_GDAL = shutil.which("ogrinfo") is not None


def test_every_layer_has_a_style():
    assert set(styles.load()) == {layer.id for layer in REG.layers}


@pytest.mark.parametrize("layer_id", sorted(styles.load()))
def test_styles_are_well_formed_qml_and_sld(layer_id):
    style = styles.load()[layer_id]
    qml = ET.fromstring(styles.qml(style).split("\n", 1)[1])
    assert qml.find("renderer-v2") is not None
    sld = ET.fromstring(styles.sld(style, layer_id))
    strokes = sld.findall(".//{http://www.opengis.net/se}SvgParameter[@name='stroke-dasharray']")
    assert bool(strokes) == bool(style.dash)
    assert (qml.find("labeling") is not None) == bool(style.label)


def test_the_qgis_project_reads_the_geopackage_next_to_it_by_relative_path():
    root = ET.fromstring(qgis_project.project_xml([REG.layer("world/countries")], distribution.GPKG).split("\n", 1)[1])
    assert [d.text for d in root.iter("datasource")] == [
        "./geojson-boundaries.gpkg|layername=world_countries_50m",
        "./geojson-boundaries.gpkg|layername=world_countries_110m",
    ]
    checked = {n.get("id"): n.get("checked") for n in root.iter("layer-tree-layer")}
    assert checked == {"world_countries_50m": "Qt::Checked", "world_countries_110m": "Qt::Unchecked"}
    assert root.find("properties/Paths/Absolute").text == "false"


def test_the_metadata_schema_lists_the_distributed_formats():
    schema = json.loads((registry.ROOT / "schemas" / "metadata.schema.json").read_text())
    files = schema["properties"]["resolutions"]["items"]["properties"]["files"]["items"]
    assert set(files["properties"]["format"]["enum"]) == set(FORMATS)


def built() -> None:
    if not (RELEASE / distribution.SUMS).exists():
        pytest.skip("dist/release がまだ作られていない（make build で作る）")


def per_resolution() -> list[tuple[registry.Layer, registry.Resolution, str]]:
    return [(layer, res, fmt) for layer in PUBLISHED for res in layer.resolutions for fmt in FORMATS]


def test_the_release_holds_exactly_the_published_files():
    """公開しないレイヤー（確認を待つレイヤー）のファイルが紛れ込んでも、足りなくても落ちる。"""
    built()
    expected = {distribution.release_name(layer, res.id, fmt) for layer, res, fmt in per_resolution()}
    expected |= {
        distribution.csv_name(layer)
        for layer in PUBLISHED
        if (registry.ROOT / "data" / layer.id / "attributes.csv").exists()
    }
    expected |= {
        distribution.GPKG,
        distribution.QGIS_ZIP,
        distribution.STYLES_ZIP,
        distribution.LICENSE,
        distribution.SUMS,
    }
    assert {p.name for p in RELEASE.iterdir()} == expected


def test_the_site_holds_exactly_the_published_files():
    built()
    expected = {
        distribution.pages_path(layer, res.id, fmt) for layer, res, fmt in per_resolution() if FORMATS[fmt].on_pages
    }
    expected |= {distribution.metadata_path(layer) for layer in PUBLISHED}
    expected |= {f"stac/{layer.slug}/{res.id}.json" for layer in PUBLISHED for res in layer.resolutions}
    expected |= {f"stac/{layer.slug}/collection.json" for layer in PUBLISHED} | {"stac/catalog.json"}
    expected |= {site_index.CATALOG, site_index.SEARCH}
    assert {str(p.relative_to(SITE)) for p in SITE.rglob("*") if p.is_file()} == expected
    assert sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file()) <= SITE_TOTAL_LIMIT


def test_release_files_match_the_checksums_and_the_size_limits():
    built()
    sums = dict(reversed(line.split("  ")) for line in (RELEASE / distribution.SUMS).read_text().splitlines())
    assert set(sums) == {p.name for p in RELEASE.iterdir()} - {distribution.SUMS}
    for name, digest in sums.items():
        assert hashlib.sha256((RELEASE / name).read_bytes()).hexdigest() == digest, name
    for layer, res, fmt in per_resolution():
        name = distribution.release_name(layer, res.id, fmt)
        assert (RELEASE / name).stat().st_size <= FILE_LIMITS[fmt], name
    assert (RELEASE / distribution.GPKG).stat().st_size <= FILE_LIMITS["gpkg"]
    assert (RELEASE / distribution.QGIS_ZIP).stat().st_size <= FILE_LIMITS["qgz"]


def test_the_site_metadata_is_the_one_in_data():
    built()
    for layer in PUBLISHED:
        site = SITE / distribution.metadata_path(layer)
        assert site.read_bytes() == (registry.ROOT / "data" / layer.id / "metadata.json").read_bytes()


def test_zips_carry_the_data_license_and_open_readable():
    built()
    for path in RELEASE.glob("*.zip"):
        with zipfile.ZipFile(path) as z:
            if path.name != distribution.STYLES_ZIP:
                assert distribution.LICENSE in z.namelist(), path.name
            for info in z.infolist():
                assert info.external_attr >> 16 == 0o644, f"{path.name}: {info.filename}"


def test_shapefiles_declare_utf8():
    built()
    for layer in PUBLISHED:
        for res in layer.resolutions:
            with zipfile.ZipFile(RELEASE / distribution.release_name(layer, res.id, "shp")) as z:
                cpg = next(n for n in z.namelist() if n.endswith(".cpg"))
                assert z.read(cpg).decode().strip() == "UTF-8"


def gpkg_tables() -> set[str]:
    with sqlite3.connect(RELEASE / distribution.GPKG) as db:
        return {row[0] for row in db.execute("SELECT table_name FROM gpkg_contents WHERE data_type = 'features'")}


def test_the_geopackage_gives_every_table_a_default_style_and_the_credit():
    built()
    expected = {distribution.table_name(layer, res.id): layer for layer in PUBLISHED for res in layer.resolutions}
    assert gpkg_tables() == set(expected)
    with sqlite3.connect(RELEASE / distribution.GPKG) as db:
        styled = db.execute("SELECT f_table_name, styleQML, useAsDefault, description FROM layer_styles").fetchall()
        described = dict(db.execute("SELECT table_name, description FROM gpkg_contents WHERE data_type = 'features'"))
    assert {row[0] for row in styled} == set(expected)
    for table, qml, default, description in styled:
        assert default == 1 and "<renderer-v2" in qml, table
        assert description == described[table] == expected[table].credit_ja, table


def test_the_qgis_zip_holds_a_project_that_points_at_the_geopackage_beside_it(tmp_path):
    built()
    with zipfile.ZipFile(RELEASE / distribution.QGIS_ZIP) as z:
        z.extractall(tmp_path)
    qgz = next(tmp_path.glob("*.qgz"))
    with zipfile.ZipFile(qgz) as z:
        project = ET.fromstring(z.read(z.namelist()[0]).decode().split("\n", 1)[1])
    sources = [d.text for d in project.iter("datasource")]
    assert {s.split("|layername=")[1] for s in sources} == gpkg_tables()
    assert {s.split("|")[0] for s in sources} == {f"./{distribution.GPKG}"}
    assert (tmp_path / distribution.GPKG).exists()


def pmtiles_header(path: Path) -> tuple[int, int, dict]:
    data = path.read_bytes()
    assert data[:7] == b"PMTiles" and data[7] == 3
    meta_offset, meta_length = struct.unpack("<2Q", data[24:40])
    assert data[97] == 2, "メタデータは gzip のはず"
    return data[100], data[101], json.loads(gzip.decompress(data[meta_offset : meta_offset + meta_length]))


def test_pmtiles_follow_the_registered_zooms_and_keep_every_feature():
    built()
    for layer in PUBLISHED:
        name = layer.id.split("/")[-1]
        for res in layer.resolutions:
            minzoom, maxzoom, meta = pmtiles_header(RELEASE / distribution.release_name(layer, res.id, "pmtiles"))
            assert (minzoom, maxzoom) == (res.minzoom, res.maxzoom), f"{layer.id} {res.id}"
            assert meta["attribution"] == layer.credit_ja
            counts = {t["layer"]: t["count"] for t in meta["tilestats"]["layers"]}
            features = len(geo.load(DIST / layer.id / f"{res.id}.geojson")["features"])
            assert counts.pop(name) == features, f"{layer.id} {res.id}"
            if layer.geometry == "polygon":
                assert counts.pop("borders") > 0, f"{layer.id} {res.id}: 境界の線が無い"
                assert counts.pop("labels") == features, f"{layer.id} {res.id}: 名前を置く点が地物と同じ数でない"
            assert counts == {}


def test_the_stac_catalog_links_resolve_and_its_assets_match_the_files():
    built()
    root = SITE / "stac"
    catalog = json.loads((root / "catalog.json").read_text())
    children = [link["href"] for link in catalog["links"] if link["rel"] == "child"]
    assert len(children) == len(PUBLISHED)
    seen = 0
    for href in children:
        collection_path = root / href
        collection = json.loads(collection_path.read_text())
        for link in (x for x in collection["links"] if x["rel"] == "item"):
            item = json.loads((collection_path.parent / link["href"]).read_text())
            assert set(item["assets"]) == set(FORMATS)
            for asset in item["assets"].values():
                href = asset["href"]
                local = (
                    SITE / href.removeprefix(f"{distribution.PAGES}/")
                    if href.startswith(distribution.PAGES)
                    else RELEASE / href.removeprefix(f"{distribution.RELEASE}/")
                )
                assert local.stat().st_size == asset["file:size"], href
                assert asset["file:checksum"] == "1220" + hashlib.sha256(local.read_bytes()).hexdigest(), href
            seen += 1
    assert seen == sum(len(layer.resolutions) for layer in PUBLISHED)


def ogrinfo(*args: str) -> str:
    result = subprocess.run(["ogrinfo", "-ro", *args], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.skipif(not HAS_GDAL, reason="GDAL が無い（make build のイメージの中で動かす）")
def test_gdal_reads_every_format_with_every_feature_and_the_japanese_names():
    built()
    for layer, res, fmt in per_resolution():
        if fmt == "pmtiles":
            continue
        path = RELEASE / distribution.release_name(layer, res.id, fmt)
        target = f"/vsizip/{path}" if fmt == "shp" else str(path)
        features = geo.load(DIST / layer.id / f"{res.id}.geojson")["features"]
        assert f"Feature Count: {len(features)}" in ogrinfo("-so", "-al", target), path.name
        # FlatGeobuf は空間索引のために地物を並べ替えるので、読めた名前が元のどれかと一致するかを見る。
        # 海域には日本語の名前が無い。日本語の名前があるレイヤーでは、名前のある地物を読む
        names = {f["properties"]["name_ja"] for f in features}
        where = ["-where", "name_ja IS NOT NULL"] if names - {None} else []
        first = re.search(r"name_ja \(String\) = (.+)", ogrinfo("-al", "-q", "-limit", "1", *where, target))
        read = None if first is None or first[1] == "(null)" else first[1]
        assert read in names, path.name
    assert "Feature Count" in ogrinfo("-so", "-al", str(RELEASE / distribution.GPKG))


@pytest.mark.skipif(not HAS_GDAL, reason="GDAL が無い（make build のイメージの中で動かす）")
def test_flatgeobuf_is_read_over_http_with_range_requests():
    built()
    layer, res = PUBLISHED[0], PUBLISHED[0].resolutions[0]
    with serve(SITE) as base:
        url = f"{base}/{distribution.pages_path(layer, res.id, 'fgb')}"
        with urllib.request.urlopen(urllib.request.Request(url, headers={"Range": "bytes=0-7"})) as response:
            assert response.status == 206
            assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert "Feature Count" in ogrinfo("-so", "-al", f"/vsicurl/{url}")


def test_a_bbox_across_the_antimeridian_extends_east_past_180():
    fiji = {
        "type": "MultiPolygon",
        "coordinates": [
            [[[177, -18], [180, -18], [180, -16], [177, -18]]],
            [[[-180, -17], [-178, -17], [-178, -16], [-180, -17]]],
        ],
    }
    assert site_index.bbox(fiji) == [177, -18, 182, -16]
    uk = {"type": "Polygon", "coordinates": [[[-8, 50], [2, 50], [2, 59], [-8, 50]]]}
    assert site_index.bbox(uk) == [-8, 50, 2, 59]


def test_the_catalog_points_at_the_tiles_and_the_metadata_on_the_site():
    built()
    catalog = json.loads((SITE / site_index.CATALOG).read_text())
    assert [entry["id"] for entry in catalog["layers"]] == [layer.id for layer in PUBLISHED]
    for entry, layer in zip(catalog["layers"], PUBLISHED, strict=True):
        assert (SITE / entry["metadata"]).exists()
        assert [(r["id"], r["minzoom"], r["maxzoom"]) for r in entry["resolutions"]] == [
            (r.id, r.minzoom, r.maxzoom) for r in layer.resolutions
        ]
        assert all((SITE / r["pmtiles"]).exists() for r in entry["resolutions"])


def test_search_entries_line_up_with_the_features_of_every_resolution():
    """ビューアは、どの解像度の PMTiles の地物の番号からも、同じ索引の行を引く。"""
    built()
    index = json.loads((SITE / site_index.SEARCH).read_text())["layers"]
    assert list(index) == [layer.id for layer in PUBLISHED]
    for layer in PUBLISHED:
        for res in layer.resolutions:
            features = geo.load(DIST / layer.id / f"{res.id}.geojson")["features"]
            props = [{k: v for k, v in f["properties"].items() if v is not None} for f in features]
            assert [{k: v for k, v in e.items() if k != "bbox"} for e in index[layer.id]] == props, (
                f"{layer.id} {res.id}"
            )


def test_a_label_point_sits_inside_the_largest_part(tmp_path):
    from boundaries import formats

    honshu = [[[135, 34], [140, 34], [140, 38], [135, 38], [135, 34]]]
    small = [[[129, 33], [129.5, 33], [129.5, 33.5], [129, 33.5], [129, 33]]]
    source = tmp_path / "in.geojson"
    source.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"name_ja": "日本"},
                        "geometry": {"type": "MultiPolygon", "coordinates": [small, honshu]},
                    }
                ],
            }
        )
    )
    [label] = json.loads(formats.label_points(source, tmp_path / "out.geojson").read_text())["features"]
    x, y = label["geometry"]["coordinates"]
    assert 135 < x < 140 and 34 < y < 38
    assert label["properties"] == {"name_ja": "日本"}
