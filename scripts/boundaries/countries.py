"""world/countries を Natural Earth 10m の日本の視点版から作る。"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from boundaries import tools
from boundaries.layer_build import Built, IslandRule, simplify_and_write
from boundaries.registry import Layer

# 1:50m と 1:110m に近い頂点数になる間隔（メートル）。公式の 50m は 99,613 点、110m は 10,654 点
INTERVAL_M = {"50m": 2500, "110m": 15000}

# Natural Earth の日本語名と英語名を直すもの。理由は docs/disputed-areas.md
NAME_FIXES = {
    "PGA": {"name_ja": "南沙諸島", "name_en": "Spratly Islands"},
    "TWN": {"name_ja": "台湾"},
}
NOT_ISO = {"XK"}
SOURCE_FIELDS = "ADM0_A3,ISO_A2_EH,ISO_A3_EH,ISO_N3_EH,NAME_EN,NAME_JA"
# 小さくても、日本の境界を読むのに要る島。点の近くの島は、どの解像度でも残す。
# 沖ノ鳥島と波照間島は Natural Earth 10m に形が無いので、japan/islands の点で示す
PROTECTED_ISLANDS = (
    ("択捉島", 147.9, 45.0),
    ("国後島", 145.9, 44.1),
    ("色丹島", 146.75, 43.8),
    ("歯舞群島", 146.2, 43.47),
    ("竹島", 131.8668, 37.2412),
    ("尖閣諸島（魚釣島）", 123.476, 25.745),
    ("与那国島", 122.99, 24.46),
    ("南鳥島", 153.98, 24.29),
)
ISLANDS = IslandRule(min_km2={"50m": 1, "110m": 100}, protected=PROTECTED_ISLANDS, near_degrees=0.05)


def _iso_codes(features: list[dict]) -> dict[int, tuple[str | None, str | None, str | None]]:
    """ISO_*_EH を使う。同じコードを持つ属領などは、本国（ADM0_A3 がコードと同じ地物）にだけ付ける。"""
    groups = defaultdict(list)
    for i, f in enumerate(features):
        groups[f["properties"]["ISO_A3_EH"]].append(i)
    codes = {}
    for a3, members in groups.items():
        for i in members:
            p = features[i]["properties"]
            primary = len(members) == 1 or p["ADM0_A3"] == a3
            if a3 == "-99" or p["ISO_A2_EH"] in NOT_ISO or not primary:
                codes[i] = (None, None, None)
            else:
                codes[i] = (p["ISO_A2_EH"], a3, p["ISO_N3_EH"])
    return codes


def with_attributes(fc: dict) -> dict:
    features = fc["features"]
    codes = _iso_codes(features)
    out = []
    for i, f in enumerate(features):
        p = f["properties"]
        iso_a2, iso_a3, iso_n3 = codes[i]
        props = {"iso_a2": iso_a2, "iso_a3": iso_a3, "iso_n3": iso_n3, "name_ja": p["NAME_JA"], "name_en": p["NAME_EN"]}
        props.update(NAME_FIXES.get(p["ADM0_A3"], {}))
        out.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
    return {"type": "FeatureCollection", "features": out}


def build(layer: Layer, sources: dict[str, list[Path]], work: Path, dist: Path) -> Built:
    [archive] = sources["natural-earth-admin0-jpn-10m"]
    raw = tools.unzip(archive, work / "natural-earth") / "ne_10m_admin_0_countries_jpn.shp"
    source_geojson = work / "countries-source.geojson"
    tools.mapshaper("-i", raw, "encoding=utf8", "-filter-fields", SOURCE_FIELDS, "-o", "format=geojson", source_geojson)
    attributed = work / "countries-attributed.geojson"
    attributed.write_text(json.dumps(with_attributes(json.loads(source_geojson.read_text())), ensure_ascii=False))
    return simplify_and_write(
        layer,
        source=attributed,
        dist=dist,
        simplify_args={r.id: ["-simplify", f"interval={INTERVAL_M[r.id]}", "keep-shapes"] for r in layer.resolutions},
        islands=ISLANDS,
        work=work,
        processing=[
            "Natural Earth 10m の日本の視点版（ne_10m_admin_0_countries_jpn）を使った",
            "ISO 3166-1 のコードは ISO_*_EH を使い、本国と同じコードを持つ属領などには付けなかった",
            "XK（コソボ）は ISO 3166-1 に無いので、コードを付けなかった",
            "日本語名と英語名を直した: 南沙諸島（元は「ウェーク島」）、台湾（元は「中華民国」）",
            "属性を iso_a2・iso_a3・iso_n3・name_ja・name_en に絞った",
        ],
    )
