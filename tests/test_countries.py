from boundaries import countries


def feature(adm0: str, a2: str, a3: str, n3: str, ja: str = "名", en: str = "Name") -> dict:
    props = {"ADM0_A3": adm0, "ISO_A2_EH": a2, "ISO_A3_EH": a3, "ISO_N3_EH": n3, "NAME_JA": ja, "NAME_EN": en}
    return {"type": "Feature", "properties": props, "geometry": {"type": "Point", "coordinates": [0, 0]}}


def props(*features: dict) -> list[dict]:
    return [f["properties"] for f in countries.with_attributes({"features": list(features)})["features"]]


def test_a_dependency_sharing_the_parent_code_gets_no_code():
    australia, cocos = props(feature("AUS", "AU", "AUS", "036"), feature("IOA", "AU", "AUS", "036"))
    assert (australia["iso_a2"], australia["iso_a3"], australia["iso_n3"]) == ("AU", "AUS", "036")
    assert (cocos["iso_a2"], cocos["iso_a3"], cocos["iso_n3"]) == (None, None, None)


def test_a_country_whose_own_code_differs_from_the_iso_code_keeps_it():
    [palestine] = props(feature("PSX", "PS", "PSE", "275"))
    assert palestine["iso_a3"] == "PSE"


def test_kosovo_and_missing_codes_get_no_code():
    kosovo, somaliland = props(feature("KOS", "XK", "-99", "-99"), feature("SOL", "-99", "-99", "-99"))
    assert kosovo["iso_a2"] is None and somaliland["iso_a2"] is None


def test_wrong_and_official_names_are_fixed():
    spratly, taiwan = props(
        feature("PGA", "-99", "-99", "-99", ja="ウェーク島", en="Wake Island"),
        feature("TWN", "TW", "TWN", "158", ja="中華民国", en="Taiwan"),
    )
    assert (spratly["name_ja"], spratly["name_en"]) == ("南沙諸島", "Spratly Islands")
    assert (taiwan["name_ja"], taiwan["name_en"]) == ("台湾", "Taiwan")
