import re

import pytest

from boundaries import registry

ROOT = registry.ROOT
DOCS = [ROOT / "README.md", ROOT / "DATA_LICENSE.md", ROOT / "CHANGELOG.md", *sorted((ROOT / "docs").glob("*.md"))]
LINK = re.compile(r"\]\(([^)\s]+)\)")


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_point_at_files_in_the_repository(doc):
    broken = []
    for target in LINK.findall(doc.read_text()):
        if re.match(r"[a-z]+:", target) or target.startswith("#"):
            continue
        if not (doc.parent / target.split("#")[0]).exists():
            broken.append(target)
    assert broken == []


def test_data_license_carries_the_credit_of_every_published_layer():
    text = (ROOT / "DATA_LICENSE.md").read_text()
    missing = [layer.id for layer in registry.load().layers if layer.publish and layer.credit_ja not in text]
    assert missing == []
