from collections import defaultdict

import pytest
from shapely.geometry import Point, shape
from shapely.ops import unary_union

from boundaries import geo, japan_admin, lgcode, registry

DIST = registry.ROOT / "dist"
RESOLUTIONS = ("medium", "low")


def built(layer: str, res: str) -> dict:
    path = DIST / "japan" / layer / f"{res}.geojson"
    if not path.exists():
        pytest.skip("dist/ の日本のレイヤーがまだ作られていない（make build で作る）")
    return geo.load(path)


@pytest.mark.parametrize(
    ("code5", "expected"),
    [("13101", "131016"), ("01101", "011011"), ("27100", "271004"), ("01695", "016951"), ("01000", "010006")],
)
def test_check_digits_follow_the_ministry_rule(code5, expected):
    assert lgcode.lg_code(code5) == expected


def test_a_code_that_is_not_five_digits_is_rejected():
    with pytest.raises(ValueError, match="5桁"):
        lgcode.check_digit("1310")


def entry(code: str, name: str, kana: str) -> lgcode.Entry:
    return lgcode.Entry(code, "高知県", name, "ｺｳﾁｹﾝ", kana)


def test_an_unassigned_area_keeps_its_prefecture_but_gets_no_code():
    p = {"N03_001": "千葉県", "N03_004": "所属未定地", "N03_005": "", "N03_007": "12000"}
    props = japan_admin.municipality_properties(p, {})
    assert props == {"lg_code": None, "pref_code": "12", "pref_ja": "千葉県", "name_ja": "所属未定地", "name_en": None}


def test_only_the_listed_glyph_variant_may_differ_from_the_ministry_list():
    entries = {"394050": entry("394050", "梼原町", "ﾕｽﾊﾗﾁｮｳ"), "394068": entry("394068", "日高村", "ﾋﾀﾞｶﾑﾗ")}
    yusuhara = {"N03_001": "高知県", "N03_004": "檮原町", "N03_005": "", "N03_007": "39405"}
    assert japan_admin.municipality_properties(yusuhara, entries)["name_ja"] == "梼原町"
    other = {"N03_001": "高知県", "N03_004": "日高町", "N03_005": "", "N03_007": "39406"}
    with pytest.raises(ValueError, match="名前が違う"):
        japan_admin.municipality_properties(other, entries)


@pytest.mark.parametrize("res", RESOLUTIONS)
def test_every_code_is_valid_and_unique(res):
    municipalities = built("municipalities", res)["features"]
    codes = [f["properties"]["lg_code"] for f in municipalities if f["properties"]["lg_code"]]
    assert len(codes) == len(set(codes))
    assert all(c == lgcode.lg_code(c[:5]) for c in codes)
    prefectures = built("prefectures", res)["features"]
    assert [f["properties"]["pref_code"] for f in prefectures] == [f"{i:02d}" for i in range(1, 48)]
    assert all(f["properties"]["iso_3166_2"] == f"JP-{f['properties']['pref_code']}" for f in prefectures)


@pytest.mark.parametrize("res", RESOLUTIONS)
def test_municipalities_do_not_overlap(res):
    shapes = [shape(f["geometry"]) for f in built("municipalities", res)["features"]]
    total = sum(s.area for s in shapes)
    assert unary_union(shapes).area == pytest.approx(total, rel=1e-6)


@pytest.mark.parametrize("res", RESOLUTIONS)
def test_each_prefecture_is_exactly_its_municipalities(res):
    by_pref = defaultdict(float)
    for f in built("municipalities", res)["features"]:
        by_pref[f["properties"]["pref_code"]] += shape(f["geometry"]).area
    for f in built("prefectures", res)["features"]:
        assert shape(f["geometry"]).area == pytest.approx(by_pref[f["properties"]["pref_code"]], rel=1e-9)


# 地域の中の点と、その点が入っているはずの市区町村
TERRITORIES = [
    ("択捉島", 147.9, 45.0, {"016985", "016993", "017001"}),
    ("国後島", 145.9, 44.1, {"016969", "016977"}),
    ("色丹島", 146.75, 43.8, {"016951"}),
    ("竹島", 131.8668, 37.2412, {"325287"}),
    ("尖閣諸島（魚釣島）", 123.476, 25.745, {"472077"}),
]


@pytest.mark.parametrize("res", RESOLUTIONS)
@pytest.mark.parametrize(("name", "lon", "lat", "codes"), TERRITORIES, ids=[t[0] for t in TERRITORIES])
def test_territories_belong_to_the_japanese_municipalities(res, name, lon, lat, codes):
    point = Point(lon, lat)
    nearest = min(built("municipalities", res)["features"], key=lambda f: shape(f["geometry"]).distance(point))
    assert shape(nearest["geometry"]).distance(point) < 0.05, name
    assert nearest["properties"]["lg_code"] in codes, (name, nearest["properties"])
