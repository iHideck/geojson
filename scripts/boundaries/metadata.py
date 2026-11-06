"""レイヤーごとの metadata.json を作る。形は schemas/metadata.schema.json。"""

from __future__ import annotations

import json
from pathlib import Path

from boundaries import distribution
from boundaries.layer_build import Built
from boundaries.registry import Registry

DISCLAIMER = {
    "ja": "境界は法的な境界を示しません。測量や航海など、位置の精度や安全に関わる用途には使えません。",
    "en": (
        "The boundaries have no legal status and must not be used for surveying, navigation or other purposes"
        " that need positional accuracy or safety."
    ),
}


def build_metadata(built: Built, reg: Registry) -> dict:
    layer = built.layer
    metrics = {m.resolution: m for m in built.metrics}
    resolutions = []
    for res in layer.resolutions:
        m = metrics[res.id]
        files = [
            distribution.file_entry(layer, res.id, o.format, o.bytes) for o in built.outputs if o.resolution == res.id
        ]
        resolutions.append(
            {
                "id": res.id,
                "precision": res.precision,
                "features": m.features_after,
                "vertices": m.vertices_after,
                "files": files,
            }
        )
    return {
        "id": layer.id,
        "title": {"ja": layer.title_ja, "en": layer.title_en},
        "geometry": layer.geometry,
        "crs": "EPSG:4326",
        "license": layer.license,
        "credit": {"ja": layer.credit_ja, "en": layer.credit_en},
        "disclaimer": DISCLAIMER,
        "sources": [
            {
                "id": s.id,
                "title": s.title,
                "publisher": s.publisher,
                "version": s.version,
                "retrieved": s.retrieved.isoformat() if s.retrieved else None,
                "urls": [f.url for f in s.files],
                "page_url": s.page_url,
                "license": s.license,
                "license_url": s.license_url,
            }
            for s in reg.sources_for([layer])
        ],
        "processing": built.processing,
        "attributes": [
            {"name": a.name, "type": a.type, "nullable": a.nullable, "description": a.description}
            for a in layer.attributes
        ],
        "resolutions": resolutions,
    }


def write(built: Built, reg: Registry, dist: Path) -> Path:
    path = dist / built.layer.id / "metadata.json"
    path.write_text(json.dumps(build_metadata(built, reg), ensure_ascii=False, indent=2) + "\n")
    return path
