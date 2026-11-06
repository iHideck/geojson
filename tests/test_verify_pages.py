import shutil

import pytest

from boundaries import registry, verify_pages
from range_server import serve

PAGES = registry.ROOT / "dist" / "pages"


@pytest.fixture
def site(tmp_path):
    if not (PAGES / "latest" / "catalog.json").exists():
        pytest.skip("dist/pages がまだ作られていない（make build で作る）")
    copy = tmp_path / "pages"
    shutil.copytree(PAGES, copy)
    return copy


def test_the_built_site_passes_the_checks_after_deploy(site):
    with serve(site) as base:
        assert verify_pages.check(base) == []


def test_a_file_of_an_unpublished_layer_is_reported(site):
    leaked = site / "latest" / "world" / "eez" / "50m.pmtiles"
    leaked.parent.mkdir(parents=True)
    leaked.write_bytes(b"x" * 32)
    with serve(site) as base:
        problems = verify_pages.check(base)
    assert any("latest/world/eez/50m.pmtiles" in p for p in problems)


def test_a_server_that_ignores_range_requests_is_reported(site, monkeypatch):
    real_get = verify_pages.get
    monkeypatch.setattr(verify_pages, "get", lambda url, range_=None: real_get(url))
    with serve(site) as base:
        problems = verify_pages.check(base)
    assert any("Range 要求に 200" in p for p in problems)
