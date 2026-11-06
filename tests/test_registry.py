import shutil
from pathlib import Path

import pytest

from boundaries import registry

MARITIME = {"world/eez", "world/territorial-seas", "world/contiguous-zones", "world/baselines", "world/high-seas"}
MARINE_REGIONS = {"world/eez", "world/territorial-seas", "world/contiguous-zones", "world/high-seas"}
PUBLISHED_NOW = {"world/countries", "japan/prefectures", "japan/municipalities", "japan/islands"} | MARINE_REGIONS


def copy_registry(tmp_path: Path) -> Path:
    shutil.copy(registry.ROOT / "layers.yml", tmp_path / "layers.yml")
    shutil.copytree(registry.ROOT / "sources", tmp_path / "sources")
    return tmp_path


def test_the_committed_registry_loads():
    reg = registry.load()
    assert {layer.id for layer in reg.layers} >= MARITIME | PUBLISHED_NOW


def test_baselines_are_off_unless_the_flag_is_set(monkeypatch):
    """基線は、施行令の基点の測地系を確かめるまで作らない。Marine Regions の海域は、いつも作る。"""
    monkeypatch.delenv("GEOJSON_ENABLE_MARITIME", raising=False)
    enabled = {layer.id for layer in registry.load().enabled_layers()}
    assert "world/baselines" not in enabled
    assert enabled >= MARINE_REGIONS
    monkeypatch.setenv("GEOJSON_ENABLE_MARITIME", "1")
    enabled = {layer.id for layer in registry.load().enabled_layers()}
    assert enabled >= MARITIME


def test_only_cleared_layers_are_published():
    published = {layer.id for layer in registry.load().layers if layer.publish}
    assert published == PUBLISHED_NOW


def test_marine_regions_is_fetched_from_the_vliz_wfs_with_the_timestamp_fixed():
    """VLIZ が認めた取り方（VLIZ の WFS）だけで取り、応答の時刻を固定してから SHA256 で照合する。"""
    sources = [s for s in registry.load().sources.values() if "marineregions" in s.license_url]
    assert len(sources) == 4
    for source in sources:
        assert not source.manual and source.geoserver, source.id
        assert all(f.url.startswith("https://geo.vliz.be/geoserver/MarineRegions/wfs?") for f in source.files), (
            source.id
        )


def test_resolutions_use_the_agreed_precision():
    expected = {"50m": 5, "medium": 5, "110m": 4, "low": 4}
    for layer in registry.load().layers:
        for res in layer.resolutions:
            assert res.precision == expected[res.id], f"{layer.id} {res.id}"


@pytest.mark.parametrize(
    ("before", "after", "message"),
    [
        ("{ name: iso_a2,", "{ name: ISO_A2,", "小文字のスネークケース"),
        (
            "{ name: name_en, type: string, description: 英語の名称 }\n    license: CC0-1.0",
            "{ name: name_english_x, type: string, description: x }\n    license: CC0-1.0",
            "10文字以内",
        ),
        ("sources: [natural-earth-admin0-jpn-10m]", "sources: [no-such-source]", "sources/no-such-source.yml がない"),
        ("    publish: true\n", "    publish: false\n", "hold（理由）が要る"),
        ("{ id: 110m, precision: 4, zoom: [0, 3] }", "{ id: 110m, precision: 4, zoom: [0, 1] }", "隙間がある"),
        ("{ id: 110m, precision: 4, zoom: [0, 3] }", "{ id: 110m, precision: 6, zoom: [0, 3] }", "細かい順"),
        ("{ id: 50m, precision: 5, zoom: [2, 6] }", "{ id: 50m, precision: 5, zoom: [6, 2] }", "0 以上 14 以下"),
    ],
)
def test_a_broken_registry_is_rejected(tmp_path, before, after, message):
    root = copy_registry(tmp_path)
    text = (root / "layers.yml").read_text()
    assert before in text
    (root / "layers.yml").write_text(text.replace(before, after, 1))
    with pytest.raises(registry.RegistryError, match=message):
        registry.load(root)


def test_an_automatic_source_without_a_checksum_is_rejected(tmp_path):
    root = copy_registry(tmp_path)
    ledger = root / "sources" / "gsi-mencho-2026.yml"
    text = ledger.read_text()
    ledger.write_text(
        text.replace("sha256: 9a08c47b208646f4d1387f065e80c563ec54282243d42d3f4ae73cae688987b5", "sha256: null")
    )
    with pytest.raises(registry.RegistryError, match="sha256 が要る"):
        registry.load(root)
