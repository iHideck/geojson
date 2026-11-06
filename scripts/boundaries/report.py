"""dist/reports/*.json と作ったファイルから docs/size-report.md を書く。"""

from __future__ import annotations

import json
from pathlib import Path

from boundaries import registry
from boundaries.limits import FILE_LIMITS, JSON_TARGET, MB

DIST = registry.ROOT / "dist"
REPORT = registry.ROOT / "docs" / "size-report.md"


def _size(n: int) -> str:
    return f"{n / MB:.2f} MB" if n >= MB else f"{n / 1024:.0f} KB"


def _judge(fmt: str, n: int) -> str:
    if n > FILE_LIMITS[fmt]:
        return "上限超え"
    if fmt in ("geojson", "topojson") and n > JSON_TARGET:
        return "目標超え"
    return "OK"


def render(reg: registry.Registry, dist: Path = DIST) -> str:
    lines = [
        "# サイズの報告",
        "",
        "`make build` が書き出す報告です。手で直さないでください。",
        "",
        "## 簡略化の前後",
        "",
        "面積は WGS84 の楕円体の上で測った値です。",
        "",
        "| レイヤー | 解像度 | 地物数（前→後） | 頂点数（前→後） | 面積の変化 | 面積が10%を超えて変わった地物 | 公開 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    files = []
    for layer in reg.layers:
        path = dist / "reports" / f"{layer.slug}.json"
        if not path.exists():
            continue
        published = "する" if layer.publish else f"保留（{layer.hold}）"
        for m in json.loads(path.read_text())["metrics"]:
            before = m["area_before_km2"]
            change = f"{(m['area_after_km2'] - before) / before * 100:+.3f}%" if before else "—"
            lines.append(
                f"| `{layer.id}` | {m['resolution']} | {m['features_before']:,}→{m['features_after']:,} "
                f"| {m['vertices_before']:,}→{m['vertices_after']:,} | {change} "
                f"| {m['features_area_over_10pct']:,} | {published} |"
            )
        meta = dist / layer.id / "metadata.json"
        for res in json.loads(meta.read_text())["resolutions"]:
            files.extend((layer.id, res["id"], f) for f in res["files"])
    lines += [
        "",
        "## ファイルの大きさ",
        "",
        "GeoJSON と TopoJSON は、目標が 5MB で、上限が 10MB です。",
        "",
        "| レイヤー | 解像度 | 形式 | 大きさ | 上限 | 判定 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for layer_id, res_id, f in files:
        lines.append(
            f"| `{layer_id}` | {res_id} | {f['format']} | {_size(f['bytes'])} | {_size(FILE_LIMITS[f['format']])} "
            f"| {_judge(f['format'], f['bytes'])} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    REPORT.write_text(render(registry.load()))
    print(f"書いた: {REPORT.relative_to(registry.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
