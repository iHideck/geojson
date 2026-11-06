"""簡略化した形を解像度ごとに書き出し、前後の地物数・頂点数・面積・大きさを測る。"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

from shapely.geometry import Point, mapping, shape

from boundaries import geo, tools
from boundaries.registry import Layer


@dataclass(frozen=True)
class Output:
    resolution: str
    format: str
    path: Path
    bytes: int


@dataclass(frozen=True)
class Metrics:
    resolution: str
    features_before: int
    features_after: int
    vertices_before: int
    vertices_after: int
    area_before_km2: float
    area_after_km2: float
    features_area_over_10pct: int
    bytes_before: int


@dataclass
class Built:
    layer: Layer
    outputs: list[Output] = field(default_factory=list)
    metrics: list[Metrics] = field(default_factory=list)
    processing: list[str] = field(default_factory=list)

    def report(self) -> dict:
        return {"layer": self.layer.id, "metrics": [asdict(m) for m in self.metrics]}


@dataclass(frozen=True)
class IslandRule:
    """簡略化で島が消えないようにする決まり。

    mapshaper の keep-shapes は地物ごとに一番大きな環しか守らない。そこで地物を島ごとに分けてから簡略化し、
    min_km2 以上の島、各地物で一番大きな島、protected の点の近くの島を残す。
    """

    min_km2: dict[str, float]
    protected: tuple[tuple[str, float, float], ...] = ()
    near_degrees: float = 0.02


def outline_path(geojson: Path) -> Path:
    """outlined のレイヤーで、builder が解像度ごとに書く境界の線。PMTiles の borders になる。"""
    return geojson.with_suffix(".lines.geojson")


def regroup_parts(parts: Path, dest: Path) -> None:
    """島ごとに簡略化した部分を、元の地物（fid の順）に戻す。同じ地物の部分どうしは重ならないので、並べるだけでよい。"""
    groups: dict[int, tuple[dict, list]] = {}
    for f in geo.load(parts)["features"]:
        geometry = f.get("geometry")
        if not geometry:
            continue
        fid = f["properties"]["fid"]
        props = {k: v for k, v in f["properties"].items() if k != "fid" and not k.startswith("k_")}
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        groups.setdefault(fid, (props, []))[1].extend(polygons)
    features = [
        {
            "type": "Feature",
            "properties": props,
            "geometry": {"type": "MultiPolygon", "coordinates": polygons}
            if len(polygons) > 1
            else {"type": "Polygon", "coordinates": polygons[0]},
        }
        for _, (props, polygons) in sorted(groups.items())
    ]
    dest.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False))


def explode_for_islands(source: Path, rule: IslandRule, resolutions: list[str], dest: Path) -> list[str]:
    """島ごとの地物にし、解像度ごとに残すかどうかの列 k_<解像度> と、元の地物の番号 fid を付ける。属性名を返す。"""
    points = [Point(lon, lat) for _, lon, lat in rule.protected]
    features = []
    fields: list[str] = []
    for fid, f in enumerate(geo.load(source)["features"]):
        fields = fields or list(f["properties"])
        geometry = shape(f["geometry"])
        parts = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
        areas = [geo.geodesic_area_km2(mapping(part)) for part in parts]
        largest = max(range(len(parts)), key=areas.__getitem__)
        for i, (part, km2) in enumerate(zip(parts, areas, strict=True)):
            protect = any(part.distance(pt) < rule.near_degrees for pt in points)
            flags = {f"k_{r}": km2 >= rule.min_km2[r] or protect or i == largest for r in resolutions}
            props = {**f["properties"], "fid": fid, **flags}
            features.append({"type": "Feature", "properties": props, "geometry": mapping(part)})
    dest.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False))
    return fields


def _areas(fc: dict) -> list[float]:
    return [geo.geodesic_area_km2(f["geometry"]) for f in fc["features"]]


def _quantization(fc: dict, precision: int) -> int:
    xs, ys = [], []
    for f in fc["features"]:
        for ring in geo.rings(f["geometry"]):
            xs.extend(p[0] for p in ring)
            ys.extend(p[1] for p in ring)
    extent = max(max(xs) - min(xs), max(ys) - min(ys))
    return math.ceil(extent * 10**precision)


def topojson_from(geojson: Path, topojson: Path, name: str, precision: int) -> Path:
    """GeoJSON と同じ細かさの TopoJSON を作る。量子化の細かさは、範囲を座標の桁で割った数にする。"""
    quantization = _quantization(geo.load(geojson), precision)
    tools.mapshaper(
        "-i", geojson, "-rename-layers", name, "-o", "format=topojson", f"quantization={quantization}", topojson
    )
    return topojson


def simplify_and_write(
    layer: Layer,
    source: Path,
    dist: Path,
    simplify_args: dict[str, list[str]],
    processing: list[str],
    object_name: str | None = None,
    islands: IslandRule | None = None,
    work: Path | None = None,
    clean: bool = True,
) -> Built:
    out_dir = dist / layer.id
    out_dir.mkdir(parents=True, exist_ok=True)
    before = geo.load(source)
    before_areas = _areas(before)
    built = Built(layer=layer, processing=list(processing))
    name = object_name or layer.id.split("/")[-1]
    if islands is not None:
        exploded = (work or out_dir) / f"{layer.slug}-islands.geojson"
        fields = explode_for_islands(source, islands, [r.id for r in layer.resolutions], exploded)
    for res in layer.resolutions:
        args = simplify_args[res.id]
        geojson = out_dir / f"{res.id}.geojson"
        keep = ["-filter-fields", ",".join(a.name for a in layer.attributes)]
        precision = f"precision={10**-res.precision:.{res.precision}f}"
        output = [*keep, "-o", "format=geojson", "rfc7946", precision, geojson]
        fixed: list[str] = []
        if islands is None:
            tools.mapshaper("-i", source, *args, *output)
        elif clean:
            dissolve = ["-dissolve", "fid", f"copy-fields={','.join(fields)}", "-clean"]
            tools.mapshaper("-i", exploded, "-filter", f"k_{res.id}", *args, *dissolve, *output)
        else:
            # mapshaper の -dissolve と -clean は、地物どうしの重なりを片付けて、重なった地物を消す。
            # 重なりが元データの描き方そのもののときは、島ごとの部分を Python で元の地物に戻す
            parts = (work or out_dir) / f"{layer.slug}-{res.id}-parts.geojson"
            tools.mapshaper("-i", exploded, "-filter", f"k_{res.id}", *args, "-o", "format=geojson", parts)
            regrouped = (work or out_dir) / f"{layer.slug}-{res.id}-regrouped.geojson"
            regroup_parts(parts, regrouped)
            tools.mapshaper("-i", regrouped, *output)
            # -clean を通さないので、簡略化と丸めで妥当でなくなった形を、ここで直す
            fixed_fc, fixed = geo.repaired(geo.load(geojson), res.precision)
            if fixed:
                repaired = (work or out_dir) / f"{layer.slug}-{res.id}-repaired.geojson"
                repaired.write_text(json.dumps(fixed_fc, ensure_ascii=False))
                tools.mapshaper("-i", repaired, *output)
        after = geo.load(geojson)
        topojson = topojson_from(geojson, out_dir / f"{res.id}.topojson", name, res.precision)
        after_areas = _areas(after)
        same_order = len(after_areas) == len(before_areas)
        changes = [
            abs(a - b) / b * 100 for a, b in zip(after_areas, before_areas, strict=False) if same_order and b > 0
        ]
        over = sum(1 for c in changes if c > 10) if same_order else -1
        built.metrics.append(
            Metrics(
                resolution=res.id,
                features_before=len(before["features"]),
                features_after=len(after["features"]),
                vertices_before=geo.vertex_count(before),
                vertices_after=geo.vertex_count(after),
                area_before_km2=round(sum(before_areas), 1),
                area_after_km2=round(sum(after_areas), 1),
                features_area_over_10pct=over,
                bytes_before=source.stat().st_size,
            )
        )
        for fmt, path in (("geojson", geojson), ("topojson", topojson)):
            built.outputs.append(Output(res.id, fmt, path, path.stat().st_size))
        built.processing.append(
            f"{res.id}: mapshaper {' '.join(args)} で簡略化し、座標を小数点以下 {res.precision} 桁に丸めた"
        )
        if islands is not None:
            names = "・".join(n for n, _, _ in islands.protected)
            kept = f"{islands.min_km2[res.id]:g}km² 以上の島"
            kept += f"、各地物で一番大きな島、次の島を残した: {names}" if names else "と、各地物で一番大きな島を残した"
            built.processing.append(f"{res.id}: 島ごとに分けて簡略化し、{kept}")
        if fixed:
            built.processing.append(
                f"{res.id}: 簡略化と丸めで妥当でなくなった {len(fixed)} 件の形を、座標の格子を保ったまま直した"
            )
    return built
