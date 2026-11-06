import pytest

from boundaries import geo

SQUARE = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]


def fc(geometry: dict) -> dict:
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": geometry}]}


def test_a_counterclockwise_square_passes():
    assert geo.problems(fc({"type": "Polygon", "coordinates": [SQUARE]}), precision=5) == []


@pytest.mark.parametrize(
    ("geometry", "message"),
    [
        ({"type": "Polygon", "coordinates": [SQUARE[::-1]]}, "右手の法則"),
        ({"type": "Polygon", "coordinates": [[[0, 0], [1.123456, 0], [1, 1], [0, 1], [0, 0]]]}, "5 桁を超える"),
        ({"type": "LineString", "coordinates": [[179.5, 0], [-179.5, 0]]}, "180度線"),
        ({"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]}, "妥当でない"),
        ({"type": "Point", "coordinates": [181, 0]}, "範囲外"),
    ],
)
def test_each_rule_violation_is_reported(geometry, message):
    found = geo.problems(fc(geometry), precision=5)
    assert any(message in p for p in found), found


def test_a_crs_member_is_reported():
    data = fc({"type": "Point", "coordinates": [0, 0]}) | {"crs": {"type": "name"}}
    assert any("crs" in p for p in geo.problems(data, precision=5))


def test_topojson_with_a_transform_decodes_to_the_original_square():
    topo = {
        "type": "Topology",
        "transform": {"scale": [0.5, 0.5], "translate": [10, 20]},
        "arcs": [[[0, 0], [2, 0], [0, 2], [-2, 0], [0, -2]]],
        "objects": {
            "x": {
                "type": "GeometryCollection",
                "geometries": [{"type": "Polygon", "arcs": [[0]], "properties": {"a": 1}}],
            }
        },
    }
    [feature] = geo.topojson_features(topo)
    assert feature["properties"] == {"a": 1}
    assert feature["geometry"]["coordinates"] == [[[10, 20], [11, 20], [11, 21], [10, 21], [10, 20]]]


def test_a_reversed_arc_index_walks_the_arc_backwards():
    topo = {"type": "Topology", "arcs": [[[0, 0], [1, 0]]], "objects": {"x": {"type": "LineString", "arcs": [~0]}}}
    [feature] = geo.topojson_features(topo)
    assert feature["geometry"]["coordinates"] == [[1, 0], [0, 0]]
