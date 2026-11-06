import json
from pathlib import Path

import pytest
from shapely import STRtree
from shapely.geometry import Point, box, shape

from boundaries import geo, gsi_islands, islands, registry, wikidata_islands

DATA = registry.ROOT / "data" / "japan" / "islands"
DIST = registry.ROOT / "dist" / "japan"
PAGES = [
    "付3　島面積\n"
    "[北海道]\n"
    "  利尻島         りしりとう            182.08  (宗谷)利尻富士町105.59 利尻町76.49\n"
    "[岡山県]\n"
    "  井島          いしま                2.61  境界未定(玉野市[岡山]・直島町[香川])\n"
    "[島根県]\n"
    "  大根島・江島      だいこんじま・            6.71  松江市\n"
    "               えしま\n"
    "[鹿児島県]\n"
    "  大島          おおしま              712.42  奄美市308.08 瀬戸内町137.12\n"
    "                                         大和村88.22 龍郷町81.79\n"
    "[広島県]\n"
    "  厳島(宮島)      いつくしま             30.20  廿日市市\n",
    "付4　次の表\n",
]


def test_the_island_table_is_read_with_its_continuation_lines():
    rishiri, ijima, daikon, amami, miyajima = gsi_islands.parse_pages(PAGES)
    assert rishiri.municipalities == (("利尻富士町", None, 105.59), ("利尻町", None, 76.49))
    assert ijima.municipalities == (("玉野市", "岡山", None), ("直島町", "香川", None)) and ijima.undetermined
    assert (daikon.name_ja, daikon.name_kana) == ("大根島・江島", "だいこんじま・えしま")
    assert [m[0] for m in amami.municipalities] == ["奄美市", "瀬戸内町", "大和村", "龍郷町"]
    assert miyajima.municipalities == (("廿日市市", None, None),)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("厳島(宮島)", ["厳島(宮島)", "厳島", "宮島"]),
        ("新城島<上地>", ["新城島<上地>", "上地島", "上地", "新城島"]),
        ("佐渡島", ["佐渡島"]),
    ],
)
def test_names_with_aliases_are_also_searched_by_their_parts(name, expected):
    assert wikidata_islands.name_variants(name) == expected


@pytest.mark.parametrize(
    ("name", "kana", "expected"),
    [
        ("佐渡島", "さどしま", "Sado-shima"),
        ("択捉島", "えとろふとう", "Etorofu-to"),
        ("対馬", "つしま", "Tsushima"),
        ("大根島・江島", "だいこんじま・えしま", "Daikon-jima, E-shima"),
        ("本州", "ほんしゅう", "Honshu"),
    ],
)
def test_island_english_names(name, kana, expected):
    assert islands.island_name_en(name, kana) == expected


def entity(tmp_path: Path, claims: list[tuple[float, float, str]]) -> Path:
    path = tmp_path / "Q1.json"
    p625 = [
        {"rank": rank, "mainsnak": {"datavalue": {"value": {"longitude": x, "latitude": y}}}} for x, y, rank in claims
    ]
    path.write_text(json.dumps({"entities": {"Q1": {"claims": {"P625": p625}}}}))
    return path


def test_the_first_coordinate_on_the_island_is_used_and_preferred_comes_first(tmp_path):
    tree = STRtree([box(0, 0, 1, 1)])
    off_island = entity(tmp_path, [(5, 5, "normal"), (0.5, 0.5, "normal")])
    assert wikidata_islands.position(off_island, tree, 0.003) == (0.5, 0.5)
    preferred = entity(tmp_path, [(0.2, 0.2, "normal"), (0.8, 0.8, "preferred")])
    assert wikidata_islands.position(preferred, tree, 0.003) == (0.8, 0.8)
    assert wikidata_islands.position(entity(tmp_path, [(5, 5, "normal")]), tree, 0.003) is None


def published() -> list[dict]:
    path = DATA / "medium.topojson"
    if not path.exists():
        pytest.skip("data/japan/islands がまだ無い")
    return geo.topojson_features(json.loads(path.read_text()))


def test_the_islands_that_matter_for_boundaries_are_present():
    names = {f["properties"]["name_ja"] for f in published()}
    expected = {"北海道", "本州", "四国", "九州", "沖縄島", "択捉島", "国後島", "色丹島", "竹島", "魚釣島"}
    expected |= {"沖ノ鳥島", "南鳥島", "与那国島", "波照間島", "佐渡島", "対馬"}
    assert expected <= names
    assert len(names) >= 280


def test_each_island_is_listed_once():
    keys = [
        (f["properties"]["name_ja"], f["properties"]["pref_code"], f["properties"]["lg_codes"]) for f in published()
    ]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("res", ["medium", "low"])
def test_every_island_point_lies_on_its_municipality_after_simplification(res):
    path = DIST / "municipalities" / f"{res}.geojson"
    if not path.exists():
        pytest.skip("dist/japan/municipalities がまだ作られていない")
    shapes = {}
    for f in geo.load(path)["features"]:
        if f["properties"]["lg_code"]:
            shapes.setdefault(f["properties"]["lg_code"], []).append(shape(f["geometry"]))
    lost = []
    for f in published():
        codes = (f["properties"]["lg_codes"] or "").split(",")
        polygons = [g for c in codes if c for g in shapes.get(c, [])]
        if not polygons:
            continue
        tree = STRtree(polygons)
        x, y = f["geometry"]["coordinates"]
        if not len(tree.query(Point(x, y), predicate="dwithin", distance=0.03)):
            lost.append(f["properties"]["name_ja"])
    assert lost == [], "簡略化で島の形が消えた"
