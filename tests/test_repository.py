import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_BYTES = 10 * 1024 * 1024
MAKEFILES = [ROOT / "Makefile", *sorted((ROOT / "mk").glob("*.mk"))]
TARGET = re.compile(r"^([a-z][a-z0-9-]*):(?!=)")
VERBS = {
    "build",
    "capture",
    "check",
    "clean",
    "deploy",
    "fetch",
    "format",
    "help",
    "lint",
    "package",
    "release",
    "run",
    "serve",
    "setup",
    "test",
    "update",
}


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    except FileNotFoundError, subprocess.CalledProcessError:
        pytest.skip("git が使えない（worktree をイメージの中で開いたときなど）")
    return [ROOT / p for p in out.decode().split("\0") if p]


def make_targets() -> list[tuple[Path, int, str, list[str]]]:
    found = []
    for mk in MAKEFILES:
        lines = mk.read_text().splitlines()
        for i, line in enumerate(lines):
            if m := TARGET.match(line):
                found.append((mk, i, m.group(1), lines))
    return found


def test_tracked_files_are_at_most_10mb():
    large = [str(p.relative_to(ROOT)) for p in tracked_files() if p.is_file() and p.stat().st_size > MAX_TRACKED_BYTES]
    assert large == []


def test_each_make_target_has_its_phony_line_just_before_it():
    problems = []
    for mk, i, name, lines in make_targets():
        above = [line for line in lines[:i] if not line.startswith(".DEFAULT_GOAL")]
        if not above or above[-1] != f".PHONY: {name}":
            problems.append(f"{mk.name}:{i + 1} {name}")
    assert problems == []


def test_make_target_names_start_with_a_verb():
    bad = [f"{mk.name}:{i + 1} {name}" for mk, i, name, _ in make_targets() if name.split("-")[0] not in VERBS]
    assert bad == [], "ターゲット名は動詞から始める。新しい動詞なら VERBS に足す"
