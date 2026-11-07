"""国の州・省（us/states など）を、Natural Earth 10m の州・省（admin 1）から作る。"""

from __future__ import annotations

import json
from pathlib import Path

from boundaries import countries, tools
from boundaries.layer_build import Built, IslandRule, simplify_and_write
from boundaries.registry import Layer

SOURCE = "natural-earth-admin1-10m"
SHAPEFILE = "ne_10m_admin_1_states_provinces.shp"
SOURCE_FIELDS = "adm0_a3,iso_3166_2,name_ja,name_en"
# レイヤーごとに取り出す国（Natural Earth の adm0_a3）
COUNTRY = {"us/states": "USA"}
# 元データの名前を直すもの。iso_3166_2 で引く
NAME_FIXES = {"US-DC": {"name_en": "District of Columbia"}}
# 国境と同じ間隔で簡略化し、同じ決まりで島を残す。変えると、州・省の外側の線が国境の線からずれる
ISLANDS = IslandRule(min_km2=countries.ISLANDS.min_km2)


def select(fc: dict, adm0_a3: str) -> tuple[dict, list[str]]:
    """国の州・省を取り出し、属性を iso_3166_2・name_ja・name_en にする。直した名前の記録も返す。"""
    features, notes = [], []
    for f in fc["features"]:
        p = f["properties"]
        if p["adm0_a3"] != adm0_a3:
            continue
        code = p["iso_3166_2"]
        props = {"iso_3166_2": code, "name_ja": p["name_ja"], "name_en": p["name_en"]}
        for key, value in NAME_FIXES.get(code, {}).items():
            notes.append(f"{code} の {key} を「{props[key]}」から「{value}」に直した")
            props[key] = value
        features.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
    return {"type": "FeatureCollection", "features": features}, notes


def build(layer: Layer, sources: dict[str, list[Path]], work: Path, dist: Path) -> Built:
    [archive] = sources[SOURCE]
    raw = tools.unzip(archive, work / "natural-earth") / SHAPEFILE
    source_geojson = work / "admin1-source.geojson"
    tools.mapshaper("-i", raw, "encoding=utf8", "-filter-fields", SOURCE_FIELDS, "-o", "format=geojson", source_geojson)
    adm0_a3 = COUNTRY[layer.id]
    selected, notes = select(json.loads(source_geojson.read_text()), adm0_a3)
    attributed = work / f"{layer.slug}-attributed.geojson"
    attributed.write_text(json.dumps(selected, ensure_ascii=False))
    return simplify_and_write(
        layer,
        source=attributed,
        dist=dist,
        simplify_args={
            r.id: ["-simplify", f"interval={countries.INTERVAL_M[r.id]}", "keep-shapes"] for r in layer.resolutions
        },
        islands=ISLANDS,
        work=work,
        processing=[
            f"Natural Earth 10m の州・省（ne_10m_admin_1_states_provinces）から、"
            f"adm0_a3 が {adm0_a3} の地物を取り出した",
            *notes,
            "属性を iso_3166_2・name_ja・name_en に絞った",
        ],
    )
