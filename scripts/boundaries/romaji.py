"""カナの読みを、長音記号を使わないヘボン式のローマ字にする。英語名の name_en に使う。"""

from __future__ import annotations

import unicodedata

_DIGRAPHS = {
    "キャ": "kya", "キュ": "kyu", "キョ": "kyo", "シャ": "sha", "シュ": "shu", "ショ": "sho",
    "チャ": "cha", "チュ": "chu", "チョ": "cho", "ニャ": "nya", "ニュ": "nyu", "ニョ": "nyo",
    "ヒャ": "hya", "ヒュ": "hyu", "ヒョ": "hyo", "ミャ": "mya", "ミュ": "myu", "ミョ": "myo",
    "リャ": "rya", "リュ": "ryu", "リョ": "ryo", "ギャ": "gya", "ギュ": "gyu", "ギョ": "gyo",
    "ジャ": "ja", "ジュ": "ju", "ジョ": "jo", "ビャ": "bya", "ビュ": "byu", "ビョ": "byo",
    "ピャ": "pya", "ピュ": "pyu", "ピョ": "pyo", "ヂャ": "ja", "ヂュ": "ju", "ヂョ": "jo",
}  # fmt: skip
_KANA = {
    "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o",
    "カ": "ka", "キ": "ki", "ク": "ku", "ケ": "ke", "コ": "ko",
    "サ": "sa", "シ": "shi", "ス": "su", "セ": "se", "ソ": "so",
    "タ": "ta", "チ": "chi", "ツ": "tsu", "テ": "te", "ト": "to",
    "ナ": "na", "ニ": "ni", "ヌ": "nu", "ネ": "ne", "ノ": "no",
    "ハ": "ha", "ヒ": "hi", "フ": "fu", "ヘ": "he", "ホ": "ho",
    "マ": "ma", "ミ": "mi", "ム": "mu", "メ": "me", "モ": "mo",
    "ヤ": "ya", "ユ": "yu", "ヨ": "yo",
    "ラ": "ra", "リ": "ri", "ル": "ru", "レ": "re", "ロ": "ro",
    "ワ": "wa", "ヰ": "i", "ヱ": "e", "ヲ": "o", "ン": "n",
    "ガ": "ga", "ギ": "gi", "グ": "gu", "ゲ": "ge", "ゴ": "go",
    "ザ": "za", "ジ": "ji", "ズ": "zu", "ゼ": "ze", "ゾ": "zo",
    "ダ": "da", "ヂ": "ji", "ヅ": "zu", "デ": "de", "ド": "do",
    "バ": "ba", "ビ": "bi", "ブ": "bu", "ベ": "be", "ボ": "bo",
    "パ": "pa", "ピ": "pi", "プ": "pu", "ペ": "pe", "ポ": "po",
    "ヴ": "vu", "ァ": "a", "ィ": "i", "ゥ": "u", "ェ": "e", "ォ": "o",
}  # fmt: skip


def katakana(text: str) -> str:
    """半角カナもひらがなも、全角のカタカナにそろえる。"""
    text = unicodedata.normalize("NFKC", text)
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in text)


def hepburn(kana: str) -> str:
    kana = katakana(kana)
    syllables: list[str] = []
    i = 0
    while i < len(kana):
        pair = kana[i : i + 2]
        if pair in _DIGRAPHS:
            syllables.append(_DIGRAPHS[pair])
            i += 2
            continue
        c = kana[i]
        if c == "ッ":
            syllables.append("")
        elif c == "ー":
            pass
        elif c in _KANA:
            syllables.append(_KANA[c])
        else:
            raise ValueError(f"ローマ字にできない文字: {c!r}（{kana}）")
        i += 1
    out = ""
    for prev, cur in zip([None, *syllables], syllables, strict=False):
        if prev == "":
            cur = ("t" + cur) if cur.startswith("ch") else (cur[0] + cur)
        out += cur
    for long_vowel, short in (("ou", "o"), ("oo", "o"), ("uu", "u")):
        out = out.replace(long_vowel, short)
    return out


# 市区町村名の最後の漢字と、その読みのローマ字の付け方
_SUFFIXES = (
    ("区", "ク", "ku"),
    ("市", "シ", "shi"),
    ("町", "チョウ", "cho"),
    ("町", "マチ", "machi"),
    ("村", "ムラ", "mura"),
    ("村", "ソン", "son"),
)


def _with_suffix(name: str, reading: str) -> str:
    for kanji, yomi, suffix in _SUFFIXES:
        if name.endswith(kanji) and reading.endswith(yomi):
            return f"{hepburn(reading[: -len(yomi)]).capitalize()}-{suffix}"
    raise ValueError(f"市区町村名の終わりが分からない: {name}（{reading}）")


def municipality_name_en(name_ja: str, kana: str, city: tuple[str, str] | None = None) -> str:
    """例: 千代田区・ﾁﾖﾀﾞｸ → Chiyoda-ku。政令指定都市の区は市の名前と読みを city に渡す。

    札幌市中央区・ｻｯﾎﾟﾛｼﾁｭｳｵｳｸ と city=("札幌市", "ｻｯﾎﾟﾛｼ") → Sapporo-shi Chuo-ku
    """
    reading = katakana(kana)
    if city is None:
        return _with_suffix(name_ja, reading)
    city_name, city_reading = city[0], katakana(city[1])
    if not (name_ja.startswith(city_name) and reading.startswith(city_reading)):
        raise ValueError(f"{name_ja}（{reading}）は {city_name}（{city_reading}）の区ではない")
    ward = _with_suffix(name_ja[len(city_name) :], reading[len(city_reading) :])
    return f"{_with_suffix(city_name, city_reading)} {ward}"


def prefecture_name_en(kana: str) -> str:
    """例: ﾄｳｷｮｳﾄ → Tokyo、ﾎｯｶｲﾄﾞｳ → Hokkaido、ｵｵｻｶﾌ → Osaka"""
    reading = katakana(kana)
    if reading == "ホッカイドウ":
        return "Hokkaido"
    for suffix in ("ケン", "フ", "ト"):
        if reading.endswith(suffix):
            return hepburn(reading[: -len(suffix)]).capitalize()
    raise ValueError(f"都道府県の読みが分からない: {kana}")
