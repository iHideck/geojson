import pytest

from boundaries import romaji


@pytest.mark.parametrize(
    ("kana", "expected"),
    [
        ("ﾄｳｷｮｳ", "tokyo"),
        ("ｻｯﾎﾟﾛ", "sapporo"),
        ("ﾍﾞｯﾌﾟ", "beppu"),
        ("ﾆｲｶﾞﾀ", "niigata"),
        ("ﾁｭｳｵｳ", "chuo"),
        ("ｲﾁﾉﾐﾔ", "ichinomiya"),
        ("ﾏｯﾁｬ", "matcha"),
        ("おおさか", "osaka"),
    ],
)
def test_hepburn_without_long_vowel_marks(kana, expected):
    assert romaji.hepburn(kana) == expected


@pytest.mark.parametrize(
    ("name", "kana", "city", "expected"),
    [
        ("千代田区", "ﾁﾖﾀﾞｸ", None, "Chiyoda-ku"),
        ("七飯町", "ﾅﾅｴﾁｮｳ", None, "Nanae-cho"),
        ("美郷町", "ﾐｻﾄﾏﾁ", None, "Misato-machi"),
        ("色丹村", "ｼｺﾀﾝﾑﾗ", None, "Shikotan-mura"),
        ("読谷村", "ﾖﾐﾀﾝｿﾝ", None, "Yomitan-son"),
        ("八戸市", "ﾊﾁﾉﾍｼ", None, "Hachinohe-shi"),
        ("札幌市中央区", "ｻｯﾎﾟﾛｼﾁｭｳｵｳｸ", ("札幌市", "ｻｯﾎﾟﾛｼ"), "Sapporo-shi Chuo-ku"),
        ("浜松市中央区", "ﾊﾏﾏﾂｼﾁｭｳｵｳｸ", ("浜松市", "ﾊﾏﾏﾂｼ"), "Hamamatsu-shi Chuo-ku"),
    ],
)
def test_municipality_names(name, kana, city, expected):
    assert romaji.municipality_name_en(name, kana, city) == expected


@pytest.mark.parametrize(
    ("kana", "expected"),
    [("ﾎｯｶｲﾄﾞｳ", "Hokkaido"), ("ﾄｳｷｮｳﾄ", "Tokyo"), ("ｵｵｻｶﾌ", "Osaka"), ("ｷｮｳﾄﾌ", "Kyoto"), ("ﾄｯﾄﾘｹﾝ", "Tottori")],
)
def test_prefecture_names_drop_the_suffix(kana, expected):
    assert romaji.prefecture_name_en(kana) == expected


def test_a_ward_that_does_not_belong_to_the_city_is_rejected():
    with pytest.raises(ValueError, match="区ではない"):
        romaji.municipality_name_en("札幌市中央区", "ｻｯﾎﾟﾛｼﾁｭｳｵｳｸ", ("仙台市", "ｾﾝﾀﾞｲｼ"))


def test_an_unknown_character_is_rejected():
    with pytest.raises(ValueError, match="ローマ字にできない"):
        romaji.hepburn("ﾄｳｷｮｳ1")
