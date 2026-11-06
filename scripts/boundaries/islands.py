"""japan/islands を、国土地理院の面積調の島の表と、Wikidata の座標から作る。

名前・読み・面積・所属は面積調の表による。位置は台帳（sources/wikidata-islands.yml）で版を固定した
Wikidata の項目の座標を使う。国土数値情報は、座標が所属市区町村の中にあるかを確かめるためだけに使い、
配布物には入れない。
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from shapely import STRtree
from shapely.geometry import shape

from boundaries import geo, gsi_islands, japan_admin, lgcode, registry, romaji
from boundaries.layer_build import Built, Metrics, Output, topojson_from
from boundaries.registry import Layer
from boundaries.wikidata_islands import LEDGER, SOURCE_ID, island_key, municipality_shapes, position

GSI = "gsi-mencho-2026"
# 都道府県からなる5島。Wikidata の座標は、この都道府県の中にあるかで確かめる
MAIN_ISLANDS = {
    "北海道": [1],
    "本州": list(range(2, 36)),
    "四国": list(range(36, 40)),
    "九州": list(range(40, 47)),
    "沖縄島": [47],
}
# 1km² 未満で面積調の表に無いが、面積調の注記に名前がある島。読みは面積調に無いので空にする
EXTRA = (
    gsi_islands.Island("竹島", "", 0.20, "島根県", (("隠岐の島町", None, None),), False),
    gsi_islands.Island("沖ノ鳥島", "", None, "東京都", (("小笠原村", None, None),), False),
)
SHORT_PREFS = {"北海道": "北海道", "東京": "東京都", "大阪": "大阪府", "京都": "京都府"}


def read_table(reg: registry.Registry, cache: Path) -> list[gsi_islands.Island]:
    [pdf] = [cache / "sources" / GSI / f.name for f in reg.sources[GSI].files]
    return [*gsi_islands.parse(pdf), *EXTRA]


def codes_for(island: gsi_islands.Island, entries: dict[str, lgcode.Entry]) -> list[str]:
    """所属市区町村の団体コード。本州などの5島はその都道府県の全市区町村、所属の無い島は都道府県の所属未定地。"""
    if island.pref_ja is None:
        prefs = {f"{p:02d}" for p in MAIN_ISLANDS[island.name_ja]}
        return sorted(e.code for e in entries.values() if e.name_ja and e.code[:2] in prefs)
    index = {(e.pref_ja, e.name_ja): e.code for e in entries.values() if e.name_ja}
    if not island.municipalities:
        pref = next(e.code[:2] for e in entries.values() if e.name_ja is None and e.pref_ja == island.pref_ja)
        return [lgcode.lg_code(pref + "000")]
    codes = []
    for name, short_pref, _ in island.municipalities:
        pref = SHORT_PREFS.get(short_pref, f"{short_pref}県") if short_pref else island.pref_ja
        code = index.get((pref, name))
        if code is None:
            raise ValueError(f"{island.name_ja}: 所属の {pref}{name} が総務省の一覧に無い")
        codes.append(code)
    return codes


def island_name_en(name_ja: str, kana: str) -> str:
    """例: 佐渡島・さどしま → Sado-shima、大根島・江島 → Daikon-jima, E-shima、対馬 → Tsushima"""
    words = []
    for name, reading in zip(name_ja.split("・"), kana.split("・"), strict=True):
        for suffix_kana, suffix in (("じま", "jima"), ("しま", "shima"), ("とう", "to")):
            if name.endswith("島") and reading.endswith(suffix_kana) and len(reading) > len(suffix_kana):
                words.append(f"{romaji.hepburn(reading[: -len(suffix_kana)]).capitalize()}-{suffix}")
                break
        else:
            words.append(romaji.hepburn(reading).capitalize())
    return ", ".join(words)


def _ledger() -> dict[str, tuple[str, float]]:
    """面積調の島（island_key）から、Wikidata の項目のファイル名と、座標を認める距離を引く。"""
    files = yaml.safe_load(LEDGER.read_text())["files"]
    return {f["island"]: (f["name"], float(f["within"])) for f in files}


def build(layer: Layer, sources: dict[str, list[Path]], work: Path, dist: Path) -> Built:
    reg = registry.load()
    cache = registry.cache_dir()
    [precision] = [r.precision for r in layer.resolutions]
    entries = lgcode.load(sources[japan_admin.SOUMU][0])
    shp = japan_admin._unzip(sources, work.parent / japan_admin.N03)
    ledger = _ledger()
    table = read_table(reg, cache)
    targets = [(island, codes_for(island, entries)) for island in table]
    shapes = municipality_shapes(shp, {c[:5] for island, codes in targets if island.pref_ja for c in codes})
    prefectures = {
        f["properties"]["pref_code"]: shape(f["geometry"])
        for f in geo.load(dist / "japan" / "prefectures" / "low.geojson")["features"]
    }
    features, unplaced = [], []
    for island, codes in targets:
        key = island_key(island)
        if key not in ledger:
            unplaced.append(f"{island.name_ja}（{island.pref_ja or '複数の都道府県'}）")
            continue
        entity, near = ledger[key]
        if island.pref_ja is None:
            # 本州などは都道府県の簡略化した形で確かめるので、少し離れていても認める
            outline = [prefectures[f"{p:02d}"] for p in MAIN_ISLANDS[island.name_ja]]
            near = max(near, 0.05)
        else:
            outline = [g for c in codes for g in shapes.get(c[:5], [])]
        found = position(cache / "sources" / SOURCE_ID / entity, STRtree(outline), near)
        if found is None:
            raise ValueError(f"{key}: Wikidata の座標が所属市区町村の中に無い。台帳を作り直す")
        x, y = found
        prefs = MAIN_ISLANDS.get(island.name_ja) if island.pref_ja is None else None
        pref_code = (f"{prefs[0]:02d}" if len(prefs) == 1 else None) if prefs else codes[0][:2]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "name_ja": island.name_ja,
                    "name_kana": island.name_kana or None,
                    "name_en": island_name_en(island.name_ja, island.name_kana) if island.name_kana else None,
                    "area_km2": island.area_km2,
                    "pref_code": pref_code,
                    "lg_codes": ",".join(codes) if island.pref_ja and island.municipalities else None,
                },
                "geometry": {"type": "Point", "coordinates": [round(x, precision), round(y, precision)]},
            }
        )
    out_dir = dist / layer.id
    out_dir.mkdir(parents=True, exist_ok=True)
    geojson = out_dir / "medium.geojson"
    geojson.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False))
    topojson = topojson_from(geojson, out_dir / "medium.topojson", "islands", precision)
    built = Built(layer=layer)
    n = len(features)
    built.metrics.append(Metrics("medium", len(table), n, len(table), n, 0.0, 0.0, 0, geojson.stat().st_size))
    for fmt, path in (("geojson", geojson), ("topojson", topojson)):
        built.outputs.append(Output("medium", fmt, path, path.stat().st_size))
    built.processing = [
        "国土地理院「令和8年全国都道府県市区町村別面積調」付3「島面積」の 1km² 以上の島を使った",
        "竹島と沖ノ鳥島は、面積調の注記にある名前で足した。読みは面積調に無いので空にした",
        "所属市区町村は、総務省の一覧で全国地方公共団体コードにした",
        "位置は、版を固定した Wikidata の項目の座標を使った。座標が所属市区町村の中にあることを、"
        "国土数値情報の行政区域で確かめた（国土数値情報は配布物に入れていない）",
        "Wikidata で項目を選べなかった島は、収録しなかった: " + ("、".join(unplaced) or "無し"),
        "英語名は、面積調の読みを長音記号を使わないヘボン式のローマ字にした",
        f"座標を小数点以下 {precision} 桁に丸めた",
    ]
    return built
