import pytest

from boundaries.release_notes import notes

CHANGELOG = """# 変更履歴

## [Unreleased]

## [0.2.0] - 2026-12-01

### 追加

- 都道府県境

## [0.1.0] - 2026-11-20

### 追加

- 国境
"""


def test_the_notes_take_the_section_of_the_tagged_version():
    text = notes("v0.2.0", CHANGELOG)
    assert text.startswith("### 追加\n\n- 都道府県境")
    assert "国境" not in text
    assert "releases/download/v0.2.0/" in text
    assert "DATA_LICENSE.md" in text


@pytest.mark.parametrize("tag", ["0.2.0", "v0.2", "v0.3.0"])
def test_a_wrong_tag_or_a_missing_section_stops_the_release(tag):
    with pytest.raises(ValueError):
        notes(tag, CHANGELOG)
