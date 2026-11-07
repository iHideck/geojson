"""git に入っている data/ を確かめる。CI の軽い検査でも動く。"""

import json

import jsonschema
import pycountry
import pytest
from shapely.geometry import Point, shape

from boundaries import admin1, distribution, geo, registry
from boundaries.countries import PROTECTED_ISLANDS
from boundaries.limits import CSV_LIMIT, FILE_LIMITS

DATA = registry.ROOT / "data"
REG = registry.load()
SCHEMA = json.loads((registry.ROOT / "schemas" / "metadata.schema.json").read_text())
PUBLISHED = [layer for layer in REG.layers if layer.publish]
RESOLUTIONS = [(layer, res) for layer in PUBLISHED for res in layer.resolutions]


def test_data_holds_only_the_published_layers():
    present = {str(p.parent.relative_to(DATA)) for p in DATA.rglob("metadata.json")}
    assert present == {layer.id for layer in PUBLISHED}
    strays = [p for p in DATA.rglob("*") if p.is_file() and str(p.parent.relative_to(DATA)) not in present]
    assert strays == []


@pytest.mark.parametrize("layer", PUBLISHED, ids=lambda layer: layer.id)
def test_metadata_follows_the_schema_and_the_registry(layer):
    meta = json.loads((DATA / layer.id / "metadata.json").read_text())
    jsonschema.validate(meta, SCHEMA, format_checker=jsonschema.FormatChecker())
    assert meta["credit"] == {"ja": layer.credit_ja, "en": layer.credit_en}
    assert meta["license"] == layer.license
    assert [a["name"] for a in meta["attributes"]] == [a.name for a in layer.attributes]
    assert [r["id"] for r in meta["resolutions"]] == [r.id for r in layer.resolutions]
    for res in meta["resolutions"]:
        files = {f["format"]: f for f in res["files"]}
        assert set(files) == set(distribution.FORMATS), res["id"]
        assert (DATA / layer.id / f"{res['id']}.topojson").stat().st_size == files["topojson"]["bytes"]
        for fmt, f in files.items():
            assert f == distribution.file_entry(layer, res["id"], fmt, f["bytes"])


@pytest.mark.parametrize(("layer", "res"), RESOLUTIONS, ids=lambda x: getattr(x, "id", ""))
def test_topojson_decodes_with_the_registered_attributes(layer, res):
    path = DATA / layer.id / f"{res.id}.topojson"
    assert path.stat().st_size <= FILE_LIMITS["topojson"]
    features = geo.topojson_features(json.loads(path.read_text()))
    assert features
    for f in features:
        assert f["geometry"] is not None
        props = f["properties"]
        for a in layer.attributes:
            value = props.get(a.name)
            if value is None:
                assert a.nullable, f"{a.name} が空"
            else:
                assert isinstance(value, str if a.type == "string" else (int, float)), a.name
        assert set(props) <= {a.name for a in layer.attributes}


@pytest.mark.parametrize("layer", PUBLISHED, ids=lambda layer: layer.id)
def test_the_attribute_table_is_small(layer):
    path = DATA / layer.id / "attributes.csv"
    if path.exists():
        assert path.stat().st_size <= CSV_LIMIT


def test_country_codes_are_iso_3166_1_and_unique():
    path = DATA / "world" / "countries" / "50m.topojson"
    features = geo.topojson_features(json.loads(path.read_text()))
    codes = [f["properties"]["iso_a2"] for f in features if f["properties"].get("iso_a2")]
    assert len(codes) == len(set(codes))
    for f in features:
        p = f["properties"]
        if p.get("iso_a2"):
            country = pycountry.countries.get(alpha_2=p["iso_a2"])
            assert country is not None, p
            assert (country.alpha_3, country.numeric) == (p["iso_a3"], p["iso_n3"]), p


@pytest.mark.parametrize(("res", "tolerance"), [("50m", 0.06), ("110m", 0.25)])
def test_islands_that_matter_for_japan_survive_simplification(res, tolerance):
    topo = json.loads((DATA / "world" / "countries" / f"{res}.topojson").read_text())
    japan = next(f for f in geo.topojson_features(topo) if f["properties"].get("iso_a3") == "JPN")
    outline = shape(japan["geometry"])
    missing = [name for name, lon, lat in PROTECTED_ISLANDS if outline.distance(Point(lon, lat)) > tolerance]
    assert missing == []


# 州・省のレイヤーに入るはずの地物の数
SUBDIVISIONS = {"us/states": 51}


@pytest.mark.parametrize(
    ("layer", "res"),
    [(layer, res) for layer, res in RESOLUTIONS if layer.id in admin1.COUNTRY],
    ids=lambda x: getattr(x, "id", ""),
)
def test_subdivisions_are_complete_with_iso_3166_2_codes_of_the_country(layer, res):
    features = geo.topojson_features(json.loads((DATA / layer.id / f"{res.id}.topojson").read_text()))
    codes = [f["properties"]["iso_3166_2"] for f in features]
    assert len(codes) == len(set(codes)) == SUBDIVISIONS[layer.id]
    alpha_2 = pycountry.countries.get(alpha_3=admin1.COUNTRY[layer.id]).alpha_2
    for code in codes:
        subdivision = pycountry.subdivisions.get(code=code)
        assert subdivision is not None and subdivision.country_code == alpha_2, code
