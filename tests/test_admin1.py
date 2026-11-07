from boundaries import admin1


def feature(adm0: str, code: str, ja: str = "名", en: str = "Name") -> dict:
    props = {"adm0_a3": adm0, "iso_3166_2": code, "name_ja": ja, "name_en": en, "type_en": "State"}
    return {"type": "Feature", "properties": props, "geometry": {"type": "Point", "coordinates": [0, 0]}}


def test_only_the_layer_country_is_kept_with_the_registered_attributes():
    fc, notes = admin1.select(
        {"features": [feature("USA", "US-CA", "カリフォルニア州", "California"), feature("CAN", "CA-BC")]}, "USA"
    )
    assert [f["properties"] for f in fc["features"]] == [
        {"iso_3166_2": "US-CA", "name_ja": "カリフォルニア州", "name_en": "California"}
    ]
    assert notes == []


def test_the_capital_district_does_not_share_the_name_of_washington_state():
    fc, notes = admin1.select(
        {"features": [feature("USA", "US-WA", en="Washington"), feature("USA", "US-DC", en="Washington")]}, "USA"
    )
    assert [f["properties"]["name_en"] for f in fc["features"]] == ["Washington", "District of Columbia"]
    assert notes == ["US-DC の name_en を「Washington」から「District of Columbia」に直した"]


def test_an_area_without_a_shape_in_the_countries_layer_is_left_out():
    fc, notes = admin1.select(
        {"features": [feature("CHN", "CN-GD", "広東省"), feature("CHN", "CN-X01~", "パラセル諸島")]}, "CHN"
    )
    assert [f["properties"]["iso_3166_2"] for f in fc["features"]] == ["CN-GD"]
    assert notes == ["CN-X01~（パラセル諸島）を除いた。国境のレイヤーに形が無い"]
