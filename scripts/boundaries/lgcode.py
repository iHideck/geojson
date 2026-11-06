"""全国地方公共団体コードと、総務省の「都道府県コード及び市区町村コード」の一覧を扱う。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import openpyxl

# 総務省「全国地方公共団体コード」仕様の 11（検査数字）: 各桁に掛ける数
WEIGHTS = (6, 5, 4, 3, 2)


def check_digit(code5: str) -> str:
    """第1〜5桁に 6・5・4・3・2 を掛けた和を 11 で割り、11 から余りを引いた数の下1桁。"""
    if len(code5) != 5 or not code5.isdigit():
        raise ValueError(f"5桁の数字ではない: {code5!r}")
    remainder = sum(int(d) * w for d, w in zip(code5, WEIGHTS, strict=True)) % 11
    return str((11 - remainder) % 10)


def lg_code(code5: str) -> str:
    return code5 + check_digit(code5)


@dataclass(frozen=True)
class Entry:
    code: str
    pref_ja: str
    name_ja: str | None
    pref_kana: str
    name_kana: str | None


def load(xlsx: Path) -> dict[str, Entry]:
    """団体コード（6桁）から、名前と読みを引ける表を作る。政令指定都市の区も含む。"""
    entries: dict[str, Entry] = {}
    workbook = openpyxl.load_workbook(xlsx, read_only=True)
    for sheet in workbook.worksheets:
        for row in list(sheet.iter_rows(values_only=True))[1:]:
            if not row or row[0] is None:
                continue
            code = str(row[0]).strip().zfill(6)
            entries[code] = Entry(code, row[1], row[2], row[3], row[4])
    return entries


def designated_city(entries: dict[str, Entry], ward: Entry) -> Entry | None:
    """政令指定都市の区（例: 札幌市中央区）なら、同じ都道府県で名前が区の頭に付く市（札幌市）を返す。"""
    if ward.name_ja is None or not ward.name_ja.endswith("区") or "市" not in ward.name_ja:
        return None
    cities = [
        e
        for e in entries.values()
        if e.code[:2] == ward.code[:2]
        and e.code != ward.code
        and e.name_ja
        and e.name_ja.endswith("市")
        and ward.name_ja.startswith(e.name_ja)
    ]
    return max(cities, key=lambda e: len(e.name_ja), default=None)
