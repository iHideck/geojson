"""公開するレイヤーを data/ に詰める。data/ はこのスクリプトだけが書く。"""

from __future__ import annotations

import csv
import io
import shutil
from pathlib import Path

from boundaries import geo, registry, styles
from boundaries.limits import CSV_LIMIT

DIST = registry.ROOT / "dist"
DATA = registry.ROOT / "data"


def attributes_csv(geojson: Path, columns: list[str]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for f in geo.load(geojson)["features"]:
        writer.writerow(["" if f["properties"].get(c) is None else f["properties"][c] for c in columns])
    return buffer.getvalue()


def package(reg: registry.Registry, dist: Path = DIST, data: Path = DATA) -> list[Path]:
    written = []
    for layer in reg.layers:
        target = data / layer.id
        if target.exists():
            shutil.rmtree(target)
        if not (layer.enabled and layer.publish):
            continue
        source = dist / layer.id
        if not (source / "metadata.json").exists():
            raise FileNotFoundError(f"{layer.id} は公開するレイヤーなのに、{source} に作られていない")
        target.mkdir(parents=True)
        for res in layer.resolutions:
            written.append(Path(shutil.copy2(source / f"{res.id}.topojson", target / f"{res.id}.topojson")))
        written.append(Path(shutil.copy2(source / "metadata.json", target / "metadata.json")))
        table = attributes_csv(source / f"{layer.resolutions[0].id}.geojson", [a.name for a in layer.attributes])
        if len(table.encode()) <= CSV_LIMIT:
            path = target / "attributes.csv"
            path.write_text(table)
            written.append(path)
    for folder in sorted((p for p in data.rglob("*") if p.is_dir()), reverse=True):
        if not any(folder.iterdir()):
            folder.rmdir()
    return written


def write_styles(reg: registry.Registry, out: Path = registry.ROOT / "styles") -> list[Path]:
    """全レイヤーの QML と SLD を styles/ に書く。基線のように公開していないレイヤーの分も、スタイルは置く。"""
    return [path for layer_id, style in styles.load().items() for path in styles.write(reg.layer(layer_id), style, out)]


def main() -> int:
    reg = registry.load()
    for path in [*package(reg), *write_styles(reg)]:
        print(f"詰めた: {path.relative_to(registry.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
