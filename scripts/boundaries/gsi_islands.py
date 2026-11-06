"""国土地理院「全国都道府県市区町村別面積調」の付3「島面積」の表を読む。

表は、島名・読み・面積・所属市区町村の行が並ぶ。次の形の続きの行がある。
- 2つの島をまとめた行（例: 大根島・江島）は、読みの残りが次の行に続く
- 所属市区町村が長いときは、次の行に続く
- 県をまたぐ島は、市区町村の後ろに [岡山] のように県が付く
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

TITLE = "付3　島面積"
ROW = re.compile(r"^\s*(?P<name>[^\s\d][^\s]*)\s+(?P<kana>[ぁ-ゖー・]+)\s+(?P<area>[\d,]+\.\d+)\s*(?P<rest>.*)$")
KANA_CONTINUES = re.compile(r"^\s+(?P<kana>[ぁ-ゖー・]+)\s*$")
REST_CONTINUES = re.compile(r"^\s{20,}(?P<rest>\S.*)$")
PREFECTURE = re.compile(r"^\s*\[(?P<pref>[^\]]+)\]\s*$")
# 北海道の振興局や東京都の支庁の名前（例: (根室)）。市区町村の名前は入らない
BRANCH = re.compile(r"^\((?P<branch>[^)市区町村]*)\)")
# 名前は「市・区・町・村」の後ろに数字・空白・括弧などが来るところで終わる（廿日市市を「廿日市」で切らない）
PART = re.compile(
    r"(?P<name>[^\s\d.()（）\[\]・]+?[市区町村])(?=[\d\s\[\]・()（）]|$)"
    r"(?:\[(?P<pref>[^\]]+)\])?(?P<area>[\d,]*\.\d+)?"
)


@dataclass(frozen=True)
class Island:
    name_ja: str
    name_kana: str
    area_km2: float
    pref_ja: str | None
    municipalities: tuple[tuple[str, str | None, float | None], ...]
    undetermined: bool


def _municipalities(rest: str) -> tuple[tuple[tuple[str, str | None, float | None], ...], bool]:
    """所属市区町村の (名前, 県の略称, その市区町村の部分の面積) の並びと、境界未定かどうか。"""
    undetermined = "境界未定" in rest
    rest = BRANCH.sub("", rest.strip()).replace("境界未定", "")
    parts = []
    for m in PART.finditer(rest):
        area = float(m.group("area").replace(",", "")) if m.group("area") else None
        parts.append((m.group("name"), m.group("pref"), area))
    return tuple(parts), undetermined


def parse(pdf: Path) -> list[Island]:
    return parse_pages([p.extract_text(extraction_mode="layout") or "" for p in PdfReader(pdf).pages])


def parse_pages(pages: list[str]) -> list[Island]:
    start = next(i for i, text in enumerate(pages) if TITLE in text)
    rows: list[dict] = []
    pref: str | None = None
    for text in pages[start:]:
        lines = text.splitlines()
        if rows and not any(ROW.match(line) for line in lines):
            break
        for line in lines:
            if m := PREFECTURE.match(line):
                pref = m.group("pref")
            elif m := ROW.match(line):
                rows.append({**m.groupdict(), "pref": pref})
            elif rows and rows[-1]["kana"].endswith("・") and (m := KANA_CONTINUES.match(line)):
                rows[-1]["kana"] += m.group("kana")
            elif rows and (m := REST_CONTINUES.match(line)) and PART.search(m.group("rest")):
                rows[-1]["rest"] += " " + m.group("rest")
    islands = []
    for r in rows:
        municipalities, undetermined = _municipalities(r["rest"])
        islands.append(
            Island(
                name_ja=r["name"],
                name_kana=r["kana"],
                area_km2=float(r["area"].replace(",", "")),
                pref_ja=r["pref"],
                municipalities=municipalities,
                undetermined=undetermined,
            )
        )
    return islands
