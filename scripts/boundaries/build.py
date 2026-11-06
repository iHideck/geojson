"""有効なレイヤーを作り、dist/ に形・metadata.json・測った値を書く。

使い方:
    python -m boundaries.build            # 有効なレイヤーをすべて作る
    python -m boundaries.build ID [ID]    # 指定したレイヤーだけ作る
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from boundaries import countries, japan_admin, metadata, registry
from boundaries.layer_build import Built

DIST = registry.ROOT / "dist"
Builder = Callable[[registry.Layer, dict[str, list[Path]], Path, Path], Built]
BUILDERS: dict[str, Builder] = {
    "world/countries": countries.build,
    "japan/prefectures": japan_admin.build_prefectures,
    "japan/municipalities": japan_admin.build_municipalities,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layers", nargs="*")
    args = parser.parse_args(argv)
    reg = registry.load()
    cache = registry.cache_dir()
    targets = [reg.layer(i) for i in args.layers] or reg.enabled_layers()
    for layer in targets:
        builder = BUILDERS.get(layer.id)
        if builder is None:
            print(f"まだ作り方が無い: {layer.id}", file=sys.stderr)
            continue
        sources = {s.id: [cache / "sources" / s.id / f.name for f in s.files] for s in reg.sources_for([layer])}
        built = builder(layer, sources, cache / "work" / layer.slug, DIST)
        metadata.write(built, reg, DIST)
        reports = DIST / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / f"{layer.slug}.json").write_text(json.dumps(built.report(), ensure_ascii=False, indent=2) + "\n")
        print(f"作った: {layer.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
