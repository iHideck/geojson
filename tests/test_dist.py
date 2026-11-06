"""make build で作った dist/ を確かめる。dist/ が無いとき（CI の軽い検査）は飛ばす。"""

import pytest

from boundaries import geo, registry, report
from boundaries.limits import FILE_LIMITS

DIST = registry.ROOT / "dist"
REG = registry.load()
BUILT = [
    (layer, res)
    for layer in REG.enabled_layers()
    for res in layer.resolutions
    if (DIST / layer.id / f"{res.id}.geojson").exists()
]


@pytest.mark.parametrize(("layer", "res"), BUILT, ids=lambda x: getattr(x, "id", ""))
def test_built_geojson_follows_rfc7946_and_the_precision(layer, res):
    path = DIST / layer.id / f"{res.id}.geojson"
    assert path.stat().st_size <= FILE_LIMITS["geojson"]
    assert geo.problems(geo.load(path), res.precision) == []


@pytest.mark.skipif(not (DIST / "reports").exists(), reason="dist/ がまだ作られていない")
def test_disabled_layers_leave_no_files_in_dist():
    leaked = [layer.id for layer in REG.layers if not layer.enabled and (DIST / layer.id).exists()]
    assert leaked == []


@pytest.mark.skipif(not (DIST / "reports").exists(), reason="dist/ がまだ作られていない")
def test_the_size_report_is_up_to_date():
    assert report.REPORT.read_text() == report.render(REG), "make package-data で docs/size-report.md を書き直す"
