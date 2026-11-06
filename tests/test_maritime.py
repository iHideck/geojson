"""海域のレイヤーの処理を、架空の合成データで確かめる。

tests/fixtures/maritime/ のデータは、このテストのために作った架空の海域で、実在の境界ではない。
Marine Regions のデータは使わない。
"""

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from shapely.geometry import Polygon, shape
from shapely.strtree import STRtree

from boundaries import geo, maritime, metadata, package, registry

FIXTURES = Path(__file__).parent / "fixtures" / "maritime"
LAW = registry.cache_dir() / "sources" / "egov-ryokai-sekorei" / "law_data.json"
HAS_MAPSHAPER = shutil.which("mapshaper") or (registry.ROOT / "node_modules" / ".bin" / "mapshaper").exists()
# 架空の島。架空の海域の境界の線から、この島の海岸に沿う部分が除かれる
ISLAND = [[139.9, 29.9], [140.1, 29.9], [140.1, 30.1], [139.9, 30.1], [139.9, 29.9]]
LAND = STRtree([Polygon(ISLAND)])


@pytest.mark.parametrize(
    "props",
    [
        {"MRGID": 8487, "GEONAME": "Japanese EEZ", "POL_TYPE": "200NM", "ISO_SOV1": "JPN"},
        {"mrgid": 8487.0, "geoname": "Japanese EEZ", "pol_type": "200NM", "iso_sov1": "JPN"},
    ],
)
def test_marine_regions_columns_map_to_the_registry_attributes(props):
    assert maritime.attributes(props) == {
        "mrgid": "8487",
        "iso_a3": "JPN",
        "name_en": "Japanese EEZ",
        "name_ja": None,
        "pol_type": "200NM",
    }


def test_high_seas_use_the_name_column():
    assert maritime.attributes({"name": "High Seas", "mrgid": 63203})["name_en"] == "High Seas"


def test_a_polygon_across_the_antimeridian_is_split_there():
    crossing = {"type": "Polygon", "coordinates": [[[179, -16], [-179, -16], [-179, -15], [179, -15], [179, -16]]]}
    fixed = maritime.split_antimeridian(crossing)
    assert fixed["type"] == "MultiPolygon"
    assert geo.problems({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": fixed}]}, 6) == []
    assert shape(fixed).area == pytest.approx(2.0)


def test_a_polygon_away_from_the_antimeridian_is_unchanged():
    square = {"type": "Polygon", "coordinates": [[[140, 30], [141, 30], [141, 31], [140, 31], [140, 30]]]}
    assert maritime.split_antimeridian(square) is square


@pytest.mark.skipif(not HAS_MAPSHAPER, reason="mapshaper が無い（npm ci で入れる）")
def test_synthetic_eez_is_simplified_with_registry_attributes(tmp_path, monkeypatch):
    monkeypatch.setenv("GEOJSON_ENABLE_MARITIME", "1")
    layer = registry.load().layer("world/eez")
    built = maritime.build_from_geojson(layer, FIXTURES / "eez.geojson", LAND, tmp_path, tmp_path / "dist")
    for res in layer.resolutions:
        fc = geo.load(tmp_path / "dist" / "world" / "eez" / f"{res.id}.geojson")
        assert [f["properties"]["mrgid"] for f in fc["features"]] == ["9001", "9002", "9003"]
        assert geo.problems(fc, res.precision) == []
    assert {o.format for o in built.outputs} == {"geojson", "topojson"}


@pytest.mark.skipif(not HAS_MAPSHAPER, reason="mapshaper が無い（make setup で入れる）")
def test_boundary_lines_keep_the_limits_and_each_shared_edge_once_and_drop_the_coast(tmp_path):
    def zone(rings):
        return {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": rings}}

    # 西の区域は島を囲み、東の区域と経度 140.5 度の辺を共有する
    west = [[[139.5, 29.5], [140.5, 29.5], [140.5, 30.5], [139.5, 30.5], [139.5, 29.5]], ISLAND[::-1]]
    east = [[[140.5, 29.5], [141.5, 29.5], [141.5, 30.5], [140.5, 30.5], [140.5, 29.5]]]
    # 180度線で分けた切り口（経度 180 度の辺）と、極の上をたどる辺（緯度 90 度の辺）を持つ区域
    cut = [[[179.5, 10], [180, 10], [180, 11], [179.5, 11], [179.5, 10]]]
    polar = [[[0, 89], [10, 89], [10, 90], [0, 90], [0, 89]]]
    zones = tmp_path / "zones.geojson"
    features = [zone(rings) for rings in (west, east, cut, polar)]
    zones.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    maritime.boundary_lines(zones, LAND, tmp_path / "lines.geojson")
    lines = [shape(f["geometry"]) for f in geo.load(tmp_path / "lines.geojson")["features"]]
    # 西と東の外側の限界（6 度）と共有する辺（1 度）を1本ずつ、切り口の区域の 3 辺（2 度）、極の区域の 3 辺（12 度）。
    # 島の海岸、経度 180 度の辺、緯度 90 度の辺は含まない
    assert sum(line.length for line in lines) == pytest.approx(21)
    assert all(line.distance(Polygon(ISLAND)) > 0.3 for line in lines)
    assert not any(
        max(abs(x) for x, _ in line.coords) == 180 and min(abs(x) for x, _ in line.coords) == 180 for line in lines
    )


@pytest.mark.skipif(not HAS_MAPSHAPER, reason="mapshaper が無い（make setup で入れる）")
def test_a_held_maritime_layer_stays_out_of_data_even_when_built(tmp_path):
    """公開しないレイヤー（いまは基線）は、作っても data/ に詰めず、古いファイルと空のフォルダーも消す。"""
    reg = registry.load()
    eez = replace(reg.layer("world/eez"), publish=False, hold="検査のために止める")
    dist, data = tmp_path / "dist", tmp_path / "data"
    metadata.write(maritime.build_from_geojson(eez, FIXTURES / "eez.geojson", LAND, tmp_path, dist), reg, dist)
    stale = data / "world" / "eez" / "50m.topojson"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    written = package.package(registry.Registry(layers=(eez,), sources=reg.sources), dist, data)
    assert written == []
    assert not (data / "world").exists()


SYNTHETIC_LAW = (
    "別表第一（第二条関係）一次に掲げるイの点からハの点までを順次結んだ線"
    "イ　北緯三〇度〇分〇秒東経一四〇度〇分〇秒の点（架空岬東端）"
    "ロ　北緯三〇度三〇分東経一四〇度一五分の点"
    "ハ　北緯三一度〇分〇秒東経一四〇度三〇分〇秒の点（架空埼南端）"
    "二次に掲げるイの点からロの点までを順次結んだ線"
    "イ　北緯三二度〇分〇秒東経一四一度〇分〇秒の点ロ　北緯三二度〇分〇秒東経一四一度一〇分〇秒の点"
)


def test_straight_baselines_are_read_from_the_annexed_table():
    first, second = maritime.straight_baselines(SYNTHETIC_LAW)
    assert first["properties"] == {"kind": "straight", "iso_a3": "JPN", "name_ja": "架空岬東端〜架空埼南端"}
    assert first["geometry"]["coordinates"] == [[140.0, 30.0], [140.25, 30.5], [140.5, 31.0]]
    assert second["geometry"]["coordinates"] == [[141.0, 32.0], [141 + 10 / 60, 32.0]]


@pytest.mark.skipif(not LAW.exists(), reason="施行令の元データがまだ取得されていない")
def test_the_enforcement_order_has_fifteen_straight_baselines():
    lines = maritime.straight_baselines(maritime.law_text(LAW))
    assert len(lines) == 15
    assert sum(len(f["geometry"]["coordinates"]) for f in lines) == 194
    assert lines[0]["geometry"]["coordinates"][0] == pytest.approx([145 + 49 / 60 + 6 / 3600, 43 + 23 / 60 + 10 / 3600])
    for f in lines:
        for lon, lat in f["geometry"]["coordinates"]:
            assert 122 < lon < 154 and 20 < lat < 46
