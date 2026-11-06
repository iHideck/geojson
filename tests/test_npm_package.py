import json
import shutil
import subprocess

import pytest

from boundaries import npm_package, registry

REG = registry.load()
PUBLISHED = [layer for layer in REG.layers if layer.enabled and layer.publish]
# npm のパッケージは、展開して 20MB まで
UNPACKED_LIMIT = 20 * 1024 * 1024


def test_the_package_holds_only_light_files_of_the_published_layers():
    files = npm_package.files_for(REG)
    assert {path.split("/")[0] + "/" + path.split("/")[1] for path in files} == {layer.id for layer in PUBLISHED}
    for layer in PUBLISHED:
        geojson = [p for p in files if p.startswith(f"{layer.id}/") and p.endswith(".geojson")]
        assert geojson == [f"{layer.id}/{layer.resolutions[-1].id}.geojson"], layer.id
        assert f"{layer.id}/metadata.json" in files


def test_the_manifest_names_the_package_and_the_data_licenses():
    manifest = npm_package.manifest(REG, list(npm_package.files_for(REG)))
    assert manifest["name"] == "japan-world-boundaries"
    for layer in PUBLISHED:
        assert layer.license in manifest["license"]
    assert "DATA_LICENSE.md" in manifest["files"]


@pytest.mark.skipif(shutil.which("npm") is None, reason="npm が無い")
def test_npm_pack_lists_exactly_the_built_files():
    out = npm_package.OUT
    if not (out / "package.json").exists():
        pytest.skip("dist/npm がまだ作られていない（make build で作る）")
    result = subprocess.run(["npm", "pack", "--dry-run", "--json"], cwd=out, capture_output=True, text=True, check=True)
    [report] = json.loads(result.stdout)
    packed = {f["path"] for f in report["files"]}
    expected = set(npm_package.files_for(REG)) | {"DATA_LICENSE.md", "README.md", "package.json"}
    assert packed == expected
    assert report["unpackedSize"] <= UNPACKED_LIMIT
