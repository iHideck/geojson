"""海域のレイヤー。Marine Regions（VLIZ の WFS の GeoJSON）と、領海法施行令の別表第一から作る。

基線（領海法施行令から作る）は、基点の測地系を確かめるまで、GEOJSON_ENABLE_MARITIME=1 のときだけ作る。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import antimeridian
from shapely.geometry import mapping, shape

from boundaries import geo
from boundaries.layer_build import Built, IslandRule, Metrics, Output, simplify_and_write, topojson_from
from boundaries.registry import Layer

# 1:50m と 1:110m に近い簡略化の間隔（メートル）。国境と同じにする
INTERVAL_M = {"50m": 2500, "110m": 15000}
# 海域は島ごとに分けず、各地物で一番大きな部分だけは必ず残す
PARTS = IslandRule(min_km2={"50m": 1, "110m": 100})


def attributes(props: dict) -> dict:
    """Marine Regions の列（大文字でも小文字でもよい）を、このリポジトリの属性にする。"""
    p = {k.lower(): v for k, v in props.items()}
    mrgid = p.get("mrgid")
    return {
        "mrgid": None if mrgid in (None, "") else str(int(float(mrgid))),
        "iso_a3": p.get("iso_sov1") or None,
        "name_en": p.get("geoname") or p.get("name") or "",
        "name_ja": None,
        "pol_type": p.get("pol_type") or None,
    }


def split_antimeridian(geometry: dict) -> dict:
    """180度線をまたぐ面を、180度線で分ける。またがないものはそのまま返す。"""
    crosses = any(abs(b[0] - a[0]) > 180 for ring in geo.rings(geometry) for a, b in zip(ring, ring[1:], strict=False))
    if not crosses:
        return geometry
    # 地図では経緯度を直線として描くので、180度線との交点も経緯度の上の直線で求める
    # 外側の輪が時計回りのもの（公海など）は、反時計回りにそろえる（fix_winding）。面積は変わらない
    fixed = antimeridian.fix_shape(shape(geometry), great_circle=False, fix_winding=True)
    return dict(fixed) if isinstance(fixed, dict) else mapping(fixed)


def prepare(fc: dict) -> dict:
    features = []
    for f in fc["features"]:
        if not f.get("geometry"):
            continue
        features.append(
            {
                "type": "Feature",
                "properties": attributes(f["properties"]),
                "geometry": split_antimeridian(f["geometry"]),
            }
        )
    return {"type": "FeatureCollection", "features": features}


def build_marine_regions(layer: Layer, sources: dict[str, list[Path]], work: Path, dist: Path) -> Built:
    work.mkdir(parents=True, exist_ok=True)
    [source] = sources[layer.sources[0]]
    return build_from_geojson(layer, source, work, dist)


def build_from_geojson(layer: Layer, source: Path, work: Path, dist: Path) -> Built:
    prepared = work / "prepared.geojson"
    prepared.write_text(json.dumps(prepare(geo.load(source)), ensure_ascii=False))
    return simplify_and_write(
        layer,
        source=prepared,
        dist=dist,
        simplify_args={r.id: ["-simplify", f"interval={INTERVAL_M[r.id]}", "keep-shapes"] for r in layer.resolutions},
        islands=PARTS,
        work=work,
        processing=[
            f"Marine Regions の {layer.sources[0]} を使った",
            "属性を mrgid・iso_a3（主権国 ISO_SOV1）・name_en（GEONAME）・pol_type にした",
            "180度線をまたぐ面は、180度線で分けた",
        ],
    )


# 漢数字の一字ずつを数字にする（施行令の別表は「四三度二三分一〇秒」のように位取りで書く）
KANJI_DIGITS = str.maketrans("〇一二三四五六七八九", "0123456789")
POINT = re.compile(
    r"(?P<label>[ア-ン]+)　北緯(?P<lat_d>[〇一二三四五六七八九]+)度(?:(?P<lat_m>[〇一二三四五六七八九]+)分)?"
    r"(?:(?P<lat_s>[〇一二三四五六七八九]+)秒)?東経(?P<lon_d>[〇一二三四五六七八九]+)度"
    r"(?:(?P<lon_m>[〇一二三四五六七八九]+)分)?(?:(?P<lon_s>[〇一二三四五六七八九]+)秒)?の点(?:（(?P<name>[^）]+)）)?"
)
SECTION = re.compile(r"(?P<no>[一二三四五六七八九十]+)次に掲げる")


def _degrees(d: str, m: str | None, s: str | None) -> float:
    def n(x: str | None) -> int:
        return int(x.translate(KANJI_DIGITS)) if x else 0

    return n(d) + n(m) / 60 + n(s) / 3600


def straight_baselines(text: str) -> list[dict]:
    """別表第一の各号（点を順に結んだ線）を、LineString の地物にする。"""
    starts = [m.start() for m in SECTION.finditer(text)] + [len(text)]
    features = []
    for start, end in zip(starts, starts[1:], strict=False):
        section = text[start:end]
        points = [
            (
                _degrees(m["lon_d"], m["lon_m"], m["lon_s"]),
                _degrees(m["lat_d"], m["lat_m"], m["lat_s"]),
                m["name"],
            )
            for m in POINT.finditer(section)
        ]
        if len(points) < 2:
            continue
        named = [p[2] for p in points if p[2]]
        title = f"{named[0]}〜{named[-1]}" if len(named) >= 2 else None
        features.append(
            {
                "type": "Feature",
                "properties": {"kind": "straight", "iso_a3": "JPN", "name_ja": title},
                "geometry": {"type": "LineString", "coordinates": [[x, y] for x, y, _ in points]},
            }
        )
    return features


def law_text(path: Path) -> str:
    """e-Gov の法令の JSON から、本文の文字だけをつなげる。"""
    parts: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, str):
            parts.append(node)
        elif isinstance(node, dict):
            for child in node.get("children", []):
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(json.loads(path.read_text())["law_full_text"])
    text = "".join(parts)
    start = text.index("別表第一（")
    end = text.find("別表第二", start)
    return text[start : end if end != -1 else len(text)]


def build_baselines(layer: Layer, sources: dict[str, list[Path]], work: Path, dist: Path) -> Built:
    [law] = sources["egov-ryokai-sekorei"]
    lines = straight_baselines(law_text(law))
    out_dir = dist / layer.id
    out_dir.mkdir(parents=True, exist_ok=True)
    built = Built(layer=layer)
    for res in layer.resolutions:
        fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    **f,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [round(x, res.precision), round(y, res.precision)] for x, y in f["geometry"]["coordinates"]
                        ],
                    },
                }
                for f in lines
            ],
        }
        geojson = out_dir / f"{res.id}.geojson"
        geojson.write_text(json.dumps(fc, ensure_ascii=False))
        topojson = topojson_from(geojson, out_dir / f"{res.id}.topojson", "baselines", res.precision)
        n = geo.vertex_count(fc)
        built.metrics.append(Metrics(res.id, len(lines), len(lines), n, n, 0.0, 0.0, 0, law.stat().st_size))
        for fmt, path in (("geojson", geojson), ("topojson", topojson)):
            built.outputs.append(Output(res.id, fmt, path, path.stat().st_size))
    built.processing = [
        "「領海及び接続水域に関する法律施行令」別表第一の各号の点を、順に結んだ線にした（日本の直線基線）",
        "点の緯度経度は度・分・秒を十進の度にした。測地系は条文に書かれていないため要確認",
        "世界の基線は含めていない",
    ]
    return built
