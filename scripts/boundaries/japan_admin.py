"""japan/municipalities と japan/prefectures を、国土数値情報の行政区域（N03）から作る。

市区町村を簡略化してから都道府県に融合するので、都道府県境は市区町村境とぴったり重なる。
国土数値情報は 12 万の島ごとのポリゴンを持つので、形は Python に読み込まず mapshaper で扱い、
島を残すかどうかは、面積と重心だけを CSV に書き出して判定する。
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
import shapefile
from pyproj import Geod

from boundaries import geo, lgcode, romaji, tools
from boundaries.countries import PROTECTED_ISLANDS
from boundaries.layer_build import Built, Metrics, Output, topojson_from
from boundaries.registry import Layer

N03 = "ksj-n03-2026"
SOUMU = "soumu-dantai-code-2024"
SHP = "N03-20260101"
# 簡略化の間隔（メートル）。medium は全国の市区町村を1ファイルにして GeoJSON の目標 5MB に収まる
INTERVAL_M = {"medium": 200, "low": 1000}
MIN_KM2 = {"medium": 0.01, "low": 1.0}
PROTECTED = (*PROTECTED_ISLANDS, ("沖ノ鳥島", 136.0819, 20.4227), ("波照間島", 123.7856, 24.0565))
NEAR_DEGREES = 0.05
GEOD = Geod(ellps="WGS84")


@dataclass(frozen=True)
class Before:
    """簡略化の前の値。市区町村コード（5桁）ごとの面積と、全体の頂点数。"""

    area_km2: dict[str, float]
    vertices: int
    bytes: int


def _unzip(sources: dict[str, list[Path]], work: Path) -> Path:
    [archive] = sources[N03]
    members = [f"{SHP}.{ext}" for ext in ("shp", "shx", "dbf", "prj", "cpg")]
    return tools.unzip(archive, work / "n03", members) / f"{SHP}.shp"


def _measure_source(shp: Path, work: Path) -> Before:
    cached = work / "before.json"
    if cached.exists():
        data = json.loads(cached.read_text())
        return Before(data["area_km2"], data["vertices"], data["bytes"])
    reader = shapefile.Reader(str(shp), encoding="utf-8")
    areas: dict[str, float] = defaultdict(float)
    vertices = 0
    for item in reader.iterShapeRecords(fields=["N03_007"]):
        points = np.asarray(item.shape.points)
        bounds = [*item.shape.parts, len(points)]
        vertices += len(points)
        rings = zip(bounds, bounds[1:], strict=False)
        signed = sum(GEOD.polygon_area_perimeter(points[s:e, 0], points[s:e, 1])[0] for s, e in rings)
        # Shapefile の外周は時計回りなので、面積は負になる
        areas[item.record[0]] += -signed / 1e6
    before = Before(dict(areas), vertices, shp.stat().st_size)
    cached.write_text(json.dumps({"area_km2": before.area_km2, "vertices": vertices, "bytes": before.bytes}))
    return before


def _keep_flags(shp: Path, work: Path) -> Path:
    """島（ポリゴン）ごとに、解像度ごとに残すかを決めた CSV を作る。"""
    keep = work / "keep.csv"
    if keep.exists():
        return keep
    records = work / "records.csv"
    tools.mapshaper(
        "-i", shp, "encoding=utf8", "-each", "rid=this.id, a=this.area, cx=this.centroidX, cy=this.centroidY",
        "-filter-fields", "rid,N03_007,a,cx,cy", "-o", "format=csv", records,
    )  # fmt: skip
    rows = list(csv.DictReader(records.open()))
    largest: dict[str, tuple[str, float]] = {}
    for r in rows:
        area = float(r["a"])
        if area > largest.get(r["N03_007"], ("", -1.0))[1]:
            largest[r["N03_007"]] = (r["rid"], area)
    biggest = {rid for rid, _ in largest.values()}
    with keep.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rid", *(f"k_{res}" for res in MIN_KM2)])
        for r in rows:
            x, y, km2 = float(r["cx"]), float(r["cy"]), float(r["a"]) / 1e6
            protect = any(abs(x - px) < NEAR_DEGREES and abs(y - py) < NEAR_DEGREES for _, px, py in PROTECTED)
            always = r["rid"] in biggest or protect
            writer.writerow([r["rid"], *(int(always or km2 >= limit) for limit in MIN_KM2.values())])
    return keep


@cache
def _soumu(path: Path) -> dict[str, lgcode.Entry]:
    return lgcode.load(path)


UNASSIGNED = "所属未定地"
# 国土数値情報と総務省の一覧で字体だけが違う名前。name_ja は総務省の一覧に合わせる
GLYPH_VARIANTS = {"394050": ("檮原町", "梼原町")}


def municipality_properties(p: dict, entries: dict[str, lgcode.Entry]) -> dict:
    if p["N03_004"] == UNASSIGNED:
        if not p["N03_007"].endswith("000"):
            raise ValueError(f"所属未定地に市区町村のコードが付いている: {p}")
        pref = p["N03_007"][:2]
        return {"lg_code": None, "pref_code": pref, "pref_ja": p["N03_001"], "name_ja": UNASSIGNED, "name_en": None}
    code = lgcode.lg_code(p["N03_007"])
    entry = entries.get(code)
    if entry is None:
        raise ValueError(f"総務省の一覧に無い団体コード {code}（{p}）")
    name_ja = p["N03_004"] + (p.get("N03_005") or "")
    if entry.name_ja != name_ja and GLYPH_VARIANTS.get(code) != (name_ja, entry.name_ja):
        raise ValueError(f"団体コード {code} の名前が違う: 国土数値情報 {name_ja}、総務省 {entry.name_ja}")
    name_ja = entry.name_ja
    city = lgcode.designated_city(entries, entry)
    name_en = romaji.municipality_name_en(entry.name_ja, entry.name_kana, city and (city.name_ja, city.name_kana))
    return {"lg_code": code, "pref_code": code[:2], "pref_ja": p["N03_001"], "name_ja": name_ja, "name_en": name_en}


def prefecture_properties(pref_code: str, entries: dict[str, lgcode.Entry]) -> dict:
    entry = entries[lgcode.lg_code(pref_code + "000")]
    return {
        "pref_code": pref_code,
        "iso_3166_2": f"JP-{pref_code}",
        "name_ja": entry.pref_ja,
        "name_en": romaji.prefecture_name_en(entry.pref_kana),
    }


def _simplify(shp: Path, keep: Path, res: str, precision: int, out: Path) -> Path:
    tools.mapshaper(
        "-i", shp, "encoding=utf8", "-each", "rid=this.id",
        "-join", keep, "keys=rid,rid", f"fields=k_{res}", f"field-types=rid:number,k_{res}:number",
        "-filter", f"k_{res} == 1",
        "-simplify", f"interval={INTERVAL_M[res]}", "keep-shapes",
        "-dissolve", "N03_007", "copy-fields=N03_001,N03_004,N03_005", "-clean",
        "-o", "format=geojson", "rfc7946", f"precision={10**-precision:.{precision}f}", out,
    )  # fmt: skip
    return out


def _clean_rounded(raw: Path, precision: int, out: Path) -> Path:
    """丸めた座標で、隣と接する輪が自分に触れることがあるので、トポロジーを見ながらもう一度直す。"""
    tools.mapshaper(
        "-i", raw, "-clean", "-o", "format=geojson", "rfc7946", f"precision={10**-precision:.{precision}f}", out
    )
    return out


def _write(fc: dict, path: Path) -> None:
    path.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")))


def _metrics(
    res: str, before_areas: dict[str, float], before: Before, after: dict[str, float], vertices: int
) -> Metrics:
    changes = [abs(after[k] - b) / b * 100 for k, b in before_areas.items() if b > 0 and k in after]
    return Metrics(
        resolution=res,
        features_before=len(before_areas),
        features_after=len(after),
        vertices_before=before.vertices,
        vertices_after=vertices,
        area_before_km2=round(sum(before_areas.values()), 1),
        area_after_km2=round(sum(after.values()), 1),
        features_area_over_10pct=sum(1 for c in changes if c > 10),
        bytes_before=before.bytes,
    )


def _processing(res: str) -> list[str]:
    names = "・".join(name for name, _, _ in PROTECTED)
    return [
        f"{res}: 島ごとのポリゴンのうち、{MIN_KM2[res]:g}km² 以上のもの、各市区町村で一番大きなもの、"
        f"次の島を残した: {names}",
        f"{res}: mapshaper -simplify interval={INTERVAL_M[res]} keep-shapes でトポロジーを保って簡略化した",
    ]


COMMON_PROCESSING = [
    "国土数値情報 行政区域データ 2026年版（2026年1月1日時点）を使った",
    "座標系は JGD2011 の経緯度で、WGS84 の経緯度（EPSG:4326）として扱った。この縮尺では差は無視できる",
    "全国地方公共団体コードの検査数字は、総務省「全国地方公共団体コード」仕様の方式で付け、総務省の一覧と照合した",
    "名前は総務省の一覧に合わせた。国土数値情報と字体が違うのは、梼原町（国土数値情報では檮原町）だけだった",
    "どの市区町村にも属さない所属未定地は、団体コードを空にして残した",
    "英語名は、総務省の一覧の読み（カナ）を、長音記号を使わないヘボン式のローマ字にして作った",
]


def _build(layer: Layer, sources: dict[str, list[Path]], work: Path, dist: Path, kind: str) -> Built:
    shared = work.parent / N03
    shared.mkdir(parents=True, exist_ok=True)
    shp = _unzip(sources, shared)
    before = _measure_source(shp, shared)
    keep = _keep_flags(shp, shared)
    entries = _soumu(sources[SOUMU][0])
    out_dir = dist / layer.id
    out_dir.mkdir(parents=True, exist_ok=True)
    built = Built(layer=layer, processing=list(COMMON_PROCESSING))
    if kind == "prefectures":
        built.processing.append("市区町村を簡略化してから都道府県ごとに融合した。都道府県境は市区町村境と重なる")
        before_areas: dict[str, float] = defaultdict(float)
        for code, km2 in before.area_km2.items():
            before_areas[code[:2]] += km2
    else:
        before_areas = before.area_km2
    for res in layer.resolutions:
        precision = f"precision={10**-res.precision:.{res.precision}f}"
        raw = shared / f"municipalities-{res.id}.geojson"
        if not raw.exists():
            simplified = _simplify(shp, keep, res.id, res.precision, shared / f"municipalities-{res.id}-raw.geojson")
            cleaned, fixed = geo.repaired(geo.load(_clean_rounded(simplified, res.precision, raw)), res.precision)
            _write(cleaned, raw)
            (shared / f"repaired-{res.id}.json").write_text(json.dumps(fixed, ensure_ascii=False))
        repaired_names = json.loads((shared / f"repaired-{res.id}.json").read_text())
        if kind == "municipalities":
            fc = geo.load(raw)
            for f in fc["features"]:
                f["id_n03"] = f["properties"]["N03_007"]
                f["properties"] = municipality_properties(f["properties"], entries)
            fc["features"].sort(key=lambda f: f["id_n03"])
            ids = [f.pop("id_n03") for f in fc["features"]]
        else:
            dissolved = shared / f"prefectures-{res.id}.geojson"
            tools.mapshaper(
                "-i", raw, "-each", "pref=N03_007.slice(0, 2)", "-dissolve", "pref",
                "-o", "format=geojson", "rfc7946", precision, dissolved,
            )  # fmt: skip
            fc, _ = geo.repaired(geo.load(dissolved), res.precision)
            for f in fc["features"]:
                f["properties"] = prefecture_properties(f["properties"]["pref"], entries)
            fc["features"].sort(key=lambda f: f["properties"]["pref_code"])
            ids = [f["properties"]["pref_code"] for f in fc["features"]]
        geojson = out_dir / f"{res.id}.geojson"
        _write(fc, geojson)
        topojson = topojson_from(geojson, out_dir / f"{res.id}.topojson", layer.id.split("/")[-1], res.precision)
        after = {i: geo.geodesic_area_km2(f["geometry"]) for i, f in zip(ids, fc["features"], strict=True)}
        built.metrics.append(_metrics(res.id, dict(before_areas), before, after, geo.vertex_count(fc)))
        for fmt, path in (("geojson", geojson), ("topojson", topojson)):
            built.outputs.append(Output(res.id, fmt, path, path.stat().st_size))
        built.processing.extend(_processing(res.id))
        built.processing.append(
            f"{res.id}: 座標を小数点以下 {res.precision} 桁に丸め、丸めたあとにもう一度 mapshaper -clean で直した"
        )
        if repaired_names:
            built.processing.append(
                f"{res.id}: 丸めで自分に触れた輪を、座標の格子を保ったまま分けた（{len(repaired_names)} 件の地物）"
            )
    return built


def build_municipalities(layer: Layer, sources: dict[str, list[Path]], work: Path, dist: Path) -> Built:
    return _build(layer, sources, work, dist, "municipalities")


def build_prefectures(layer: Layer, sources: dict[str, list[Path]], work: Path, dist: Path) -> Built:
    return _build(layer, sources, work, dist, "prefectures")
