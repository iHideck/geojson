"""島の位置に使う Wikidata の項目を選び、版を固定した URL の台帳（sources/wikidata-islands.yml）を作る。

台帳を作り直すとき（面積調の版を上げたときなど）だけ使う:
    python -m boundaries.wikidata_islands

面積調の島ごとに、所属市区町村の中（国土数値情報の行政区域から 0.003 度以内）に座標があり、
日本語の名前か別名が島名と同じ（無ければ島名を含む）項目を選ぶ。候補が複数あるときは、
面積が面積調の値に最も近いものにする。選べなかった島は台帳に載せない。
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import shapefile
from shapely import STRtree
from shapely.geometry import Point, shape

from boundaries import gsi_islands, lgcode, registry

SOURCE_ID = "wikidata-islands"
LEDGER = registry.ROOT / "sources" / f"{SOURCE_ID}.yml"
USER_AGENT = "geojson-boundaries-build/0.1 (https://github.com/iHideck/geojson)"
ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json?revision={rev}"
WITHIN_DEGREES = 0.003
# 名前が一致する項目は、座標が少し島から外れていても使う（約 2km まで）
LOOSE_DEGREES = 0.02
QUERY = """
SELECT ?item ?label ?alias ?coord ?rev ?area WHERE {
  SERVICE wikibase:box {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:cornerSouthWest "Point(122 20)"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerNorthEast "Point(154 46)"^^geo:wktLiteral .
  }
  VALUES ?class { wd:Q23442 wd:Q33837 }
  ?item wdt:P31/wdt:P279? ?class .
  ?item schema:version ?rev .
  OPTIONAL { ?item rdfs:label ?label FILTER(lang(?label) = "ja") }
  OPTIONAL { ?item skos:altLabel ?alias FILTER(lang(?alias) = "ja") }
  OPTIONAL { ?item p:P2046/psn:P2046/wikibase:quantityAmount ?area }
}
"""


@dataclass
class Item:
    qid: str
    rev: str
    points: list[tuple[float, float]] = field(default_factory=list)
    names: set[str] = field(default_factory=set)
    km2: float | None = None


def tolerance(island: gsi_islands.Island) -> float:
    """座標が所属市区町村のポリゴンからどれだけ離れてよいか（度）。小さな島は、項目の座標が岩礁の中心にあることがある。"""
    return WITHIN_DEGREES if island.area_km2 and island.area_km2 >= 1 else 0.02


def name_variants(name: str) -> list[str]:
    """例: 厳島(宮島) → 厳島(宮島)・厳島・宮島、新城島<上地> → 新城島<上地>・上地島・上地・新城島"""
    variants = [name]
    if m := re.fullmatch(r"(?P<base>[^(<]+)\((?P<inner>[^)]+)\)", name):
        variants += [m["base"], m["inner"]]
    if m := re.fullmatch(r"(?P<base>[^(<]+)<(?P<inner>[^>]+)>", name):
        variants += [m["inner"] + "島", m["inner"], m["base"]]
    return variants


def island_key(island: gsi_islands.Island) -> str:
    """台帳で面積調の島を指す名前。同じ都道府県に同名の島があるので、所属市区町村も入れる。"""
    municipalities = "・".join(name for name, _, _ in island.municipalities)
    return f"{island.pref_ja or ''}|{municipalities}|{island.name_ja}"


def coordinates(entity: Path) -> list[tuple[float, float]]:
    """項目の座標（P625）の並び。推奨の順位のものを先にする。"""
    data = json.loads(entity.read_text())
    claims = next(iter(data["entities"].values()))["claims"].get("P625", [])
    ordered = [c for c in claims if c["rank"] == "preferred"] + [c for c in claims if c["rank"] == "normal"]
    return [
        (c["mainsnak"]["datavalue"]["value"]["longitude"], c["mainsnak"]["datavalue"]["value"]["latitude"])
        for c in ordered
    ]


def position(entity: Path, tree: STRtree, near: float) -> tuple[float, float] | None:
    """座標のうち、所属市区町村のポリゴンから near 度以内にある最初のもの。

    項目に座標が複数あり、島から外れたものが先に来ることがある。
    """
    for x, y in coordinates(entity):
        if len(tree.query(Point(x, y), predicate="dwithin", distance=near)):
            return x, y
    return None


def _query() -> list[Item]:
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY})
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                rows = json.load(response)["results"]["bindings"]
            break
        except urllib.error.HTTPError as error:
            # 検索の窓口は混むと 504 を返す。時間を置いて試し直す
            if error.code not in (429, 502, 503, 504) or attempt == 2:
                raise
            time.sleep(30 * (attempt + 1))
    items: dict[str, Item] = {}
    for r in rows:
        qid = r["item"]["value"].rsplit("/", 1)[1]
        lon, lat = map(float, re.match(r"Point\(([-\d.e]+) ([-\d.e]+)\)", r["coord"]["value"]).groups())
        item = items.setdefault(qid, Item(qid, r["rev"]["value"]))
        if (lon, lat) not in item.points:
            item.points.append((lon, lat))
        for key in ("label", "alias"):
            if key in r:
                item.names.add(r[key]["value"])
        if "area" in r and item.km2 is None:
            item.km2 = float(r["area"]["value"]) / 1e6
    return list(items.values())


def municipality_shapes(shp: Path, code5s: set[str]) -> dict[str, list]:
    reader = shapefile.Reader(str(shp), encoding="utf-8")
    shapes: dict[str, list] = {}
    for record in reader.iterShapeRecords(fields=["N03_007"]):
        code = record.record[0]
        if code in code5s:
            shapes.setdefault(code, []).append(shape(record.shape.__geo_interface__))
    return shapes


def candidates(island: gsi_islands.Island, items: list[Item], tree: STRtree) -> list[tuple[Item, float]]:
    """名前が合い、座標が所属市区町村に近い項目を、（項目, 認める距離）の組でよさそうな順に並べる。

    名前が一致するものを、名前を含むもの（例: 大島 に対する 奄美大島）より先にする。名前を含むだけのものは
    別の島のこと（宝島 に対する 小宝島）があるので、名前が一致する項目は少し離れていても先に使う。
    """
    tight = tolerance(island)
    loose = max(tight, LOOSE_DEGREES)

    def within(it: Item, near: float) -> bool:
        return any(len(tree.query(Point(x, y), predicate="dwithin", distance=near)) for x, y in it.points)

    def by_area(pool: list[Item]) -> list[Item]:
        area = island.area_km2
        return sorted(pool, key=lambda it: abs(math.log(it.km2 / area)) if it.km2 and area else math.inf)

    for name in name_variants(island.name_ja.split("・")[0]):
        exact = [it for it in items if name in it.names]
        partial = [it for it in items if name not in it.names and any(name in n for n in it.names)]
        for pool in (exact, partial):
            for near in (tight, loose):
                found = by_area([it for it in pool if within(it, near)])
                if found:
                    return [(it, near) for it in found]
    return []


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def update() -> list[str]:
    reg = registry.load()
    cache = registry.cache_dir()
    shp = cache / "work" / "ksj-n03-2026" / "n03" / "N03-20260101.shp"
    entries = lgcode.load(cache / "sources" / "soumu-dantai-code-2024" / "000925835.xlsx")
    from boundaries import islands

    table = islands.read_table(reg, cache)
    targets = [(island, islands.codes_for(island, entries)) for island in table]
    shapes = municipality_shapes(shp, {c[:5] for _, codes in targets for c in codes})
    items = _query()
    files, missing = [], []
    scratch = cache / "work" / "wikidata-islands"
    scratch.mkdir(parents=True, exist_ok=True)
    for island, codes in targets:
        polygons = [g for c in codes for g in shapes.get(c[:5], [])]
        tree = STRtree(polygons) if polygons else None
        found = None
        for item, near in candidates(island, items, tree) if tree else []:
            url = ENTITY_URL.format(qid=item.qid, rev=item.rev)
            body = _download(url)
            entity = scratch / f"{item.qid}.json"
            entity.write_bytes(body)
            time.sleep(0.2)
            # ビルドと同じ決め方で座標を選べるかを確かめる
            if position(entity, tree, near) is not None:
                found = (island_key(island), url, f"{item.qid}.json", hashlib.sha256(body).hexdigest(), len(body), near)
                break
        if found is None:
            missing.append(island_key(island))
        else:
            files.append(found)
    lines = [
        f"id: {SOURCE_ID}",
        "title: Wikidata の島の項目（版を固定した JSON）",
        "publisher: Wikidata（Wikimedia Foundation）",
        f"version: {time.strftime('%Y-%m-%d')}",
        f"retrieved: {time.strftime('%Y-%m-%d')}",
        "license: CC0-1.0",
        "license_url: https://www.wikidata.org/wiki/Wikidata:Licensing",
        "page_url: https://www.wikidata.org/",
        "# python -m boundaries.wikidata_islands が作る。island は面積調の島（都道府県|所属市区町村|島名）、"
        "within は座標を認めた所属市区町村からの距離（度）",
        "files:",
    ]
    for key, url, name, sha, size, near in files:
        lines += [
            f"  - island: {json.dumps(key, ensure_ascii=False)}",
            f"    within: {near}",
            f"    url: {url}",
            f"    name: {name}",
            f"    sha256: {sha}",
            f"    bytes: {size}",
        ]
    LEDGER.write_text("\n".join(lines) + "\n")
    return missing


def main() -> int:
    missing = update()
    print(f"台帳を書いた: {LEDGER.relative_to(registry.ROOT)}")
    print("選べなかった島:", "、".join(missing) or "無し")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
