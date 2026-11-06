"""GeoJSON の形を数え、RFC 7946 とこのリポジトリの決まりに合うかを調べる。"""

from __future__ import annotations

import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

from pyproj import Geod
from shapely.geometry import shape

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
            if any(abs(b[0] - a[0]) > 180 for a, b in zip(ring, ring[1:], strict=False)):
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
