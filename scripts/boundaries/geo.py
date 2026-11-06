"""GeoJSON の形を数え、RFC 7946 とこのリポジトリの決まりに合うかを調べる。"""

from __future__ import annotations

import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import shapely
from pyproj import Geod
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.geometry.polygon import orient

GEOD = Geod(ellps="WGS84")


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def rings(geometry: dict) -> Iterator[list[list[float]]]:
    """Polygon と MultiPolygon は環を、LineString 系は線を、Point 系は点の並びを返す。"""
    kind, coords = geometry["type"], geometry["coordinates"]
    if kind == "Polygon":
        yield from coords
    elif kind == "MultiPolygon":
        for polygon in coords:
            yield from polygon
    elif kind in ("LineString", "MultiPoint"):
        yield coords
    elif kind == "MultiLineString":
        yield from coords
    elif kind == "Point":
        yield [coords]
    else:
        raise ValueError(f"扱わない形: {kind}")


def vertex_count(fc: dict) -> int:
    return sum(len(r) for f in fc["features"] for r in rings(f["geometry"]))


def geodesic_area_km2(geometry: dict) -> float:
    area, _ = GEOD.geometry_area_perimeter(shape(geometry))
    return abs(area) / 1e6


def _signed_area(ring: list[list[float]]) -> float:
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:], strict=False)) / 2


def _decimals(value: float) -> int:
    exponent = Decimal(repr(value)).normalize().as_tuple().exponent
    return max(0, -exponent) if isinstance(exponent, int) else 0


def problems(fc: dict, precision: int) -> list[str]:
    """RFC 7946 と座標の桁・180度線・形の妥当性の違反を、地物ごとに文で返す。"""
    found = []
    if fc.get("type") != "FeatureCollection":
        found.append("FeatureCollection ではない")
    if "crs" in fc:
        found.append("RFC 7946 では crs を書かない")
    for i, feature in enumerate(fc.get("features", [])):
        where = f"地物 {i}"
        geometry = feature.get("geometry")
        if not geometry:
            found.append(f"{where}: 形が無い")
            continue
        for ring in rings(geometry):
            for lon, lat, *rest in ring:
                if rest:
                    found.append(f"{where}: 座標が3次元")
                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    found.append(f"{where}: 経緯度の範囲外 {lon},{lat}")
                if _decimals(lon) > precision or _decimals(lat) > precision:
                    found.append(f"{where}: 小数点以下が {precision} 桁を超える {lon},{lat}")
                    break
            # 極（緯度 ±90）の上を通る辺は、地図の上端と下端をたどる線で、180度線をまたがない（北極海を含む公海など）
            crossing = (
                abs(b[0] - a[0]) > 180 and not (abs(a[1]) == 90 and a[1] == b[1])
                for a, b in zip(ring, ring[1:], strict=False)
            )
            if any(crossing):
                found.append(f"{where}: 180度線をまたぐ線分がある")
        if geometry["type"] in ("Polygon", "MultiPolygon"):
            polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
            for polygon in polygons:
                if _signed_area(polygon[0]) < 0:
                    found.append(f"{where}: 外側の環が反時計回りでない（RFC 7946 の右手の法則）")
                if any(_signed_area(hole) > 0 for hole in polygon[1:]):
                    found.append(f"{where}: 穴の環が時計回りでない（RFC 7946 の右手の法則）")
        if not shape(geometry).is_valid:
            found.append(f"{where}: 形が妥当でない")
    return found


def topojson_features(topo: dict) -> list[dict]:
    """TopoJSON を GeoJSON の地物の並びに戻す。検査で使う。"""
    transform = topo.get("transform")

    def point(p: list[float]) -> list[float]:
        if not transform:
            return p
        (sx, sy), (tx, ty) = transform["scale"], transform["translate"]
        return [p[0] * sx + tx, p[1] * sy + ty]

    def decode(arc: list[list[float]]) -> list[list[float]]:
        if not transform:
            return arc
        x = y = 0
        out = []
        for dx, dy in arc:
            x, y = x + dx, y + dy
            out.append(point([x, y]))
        return out

    arcs = [decode(a) for a in topo["arcs"]]

    def line(indices: list[int]) -> list[list[float]]:
        coords: list[list[float]] = []
        for i in indices:
            arc = arcs[i] if i >= 0 else arcs[~i][::-1]
            coords.extend(arc if not coords else arc[1:])
        return coords

    def geometry(g: dict) -> dict | None:
        kind = g.get("type")
        if kind is None:
            return None
        if kind == "Polygon":
            coords = [line(r) for r in g["arcs"]]
        elif kind == "MultiPolygon":
            coords = [[line(r) for r in polygon] for polygon in g["arcs"]]
        elif kind == "LineString":
            coords = line(g["arcs"])
        elif kind == "MultiLineString":
            coords = [line(r) for r in g["arcs"]]
        elif kind == "Point":
            coords = point(g["coordinates"])
        elif kind == "MultiPoint":
            coords = [point(p) for p in g["coordinates"]]
        else:
            raise ValueError(f"扱わない形: {kind}")
        return {"type": kind, "coordinates": coords}

    features = []
    for obj in topo["objects"].values():
        members = obj["geometries"] if obj["type"] == "GeometryCollection" else [obj]
        for g in members:
            features.append({"type": "Feature", "properties": g.get("properties", {}), "geometry": geometry(g)})
    return features


def _round_coords(coords, precision: int):
    if isinstance(coords[0], (int, float)):
        return [round(c, precision) for c in coords]
    return [_round_coords(c, precision) for c in coords]


def _polygons(geometry):
    """面だけを取り出し、外周を反時計回りにそろえて、1つの面か複数の面にする。"""
    polygons = [orient(p, sign=1.0) for p in shapely.get_parts(geometry) if p.geom_type == "Polygon" and not p.is_empty]
    if not polygons:
        return Polygon()
    return polygons[0] if len(polygons) == 1 else MultiPolygon(polygons)


def repaired(fc: dict, precision: int) -> tuple[dict, list[str]]:
    """丸めで妥当でなくなった面を、座標の格子を保ったまま直す。直した地物の説明を返す。

    自分に触れる輪は2つの面に分かれる。外周は反時計回り、穴は時計回りにそろえる（RFC 7946）。
    """
    fixed_names = []
    grid = 10**-precision
    for i, feature in enumerate(fc["features"]):
        geometry = shape(feature["geometry"])
        if geometry.is_valid:
            continue
        result = _polygons(shapely.set_precision(shapely.make_valid(geometry), grid))
        if not result.is_valid or result.is_empty:
            # 直した面どうしが辺を共有して、まとめると妥当でないとき（海域の大きな地物など）は、
            # 結合してから格子に合わせる
            parts = [
                p for p in shapely.get_parts(shapely.make_valid(geometry)) if p.geom_type in ("Polygon", "MultiPolygon")
            ]
            result = _polygons(shapely.set_precision(shapely.unary_union(parts), grid))
        if not result.is_valid or result.is_empty:
            raise ValueError(f"地物 {i} の形を直せなかった: {feature['properties']}")
        out = mapping(result)
        feature["geometry"] = {"type": out["type"], "coordinates": _round_coords(out["coordinates"], precision)}
        fixed_names.append(str(feature["properties"].get("name_ja") or i))
    return fc, fixed_names
