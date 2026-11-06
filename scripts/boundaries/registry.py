"""layers.yml と sources/*.yml を読み、検査済みの型にして返す。"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import yaml

ROOT = Path(__file__).resolve().parents[2]
ATTRIBUTE_NAME = re.compile(r"^[a-z][a-z0-9_]{0,9}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
LICENSES = {"PDM-1.0", "CC0-1.0", "CC-BY-4.0", "PDL-1.0", "JP-COPYRIGHT-ACT-13"}
Geometry = Literal["polygon", "line", "point"]


def cache_dir() -> Path:
    return Path(os.environ.get("GEOJSON_CACHE", ROOT / ".cache"))


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class SourceFile:
    url: str
    name: str
    sha256: str | None
    bytes: int | None


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    publisher: str
    version: str
    retrieved: date | None
    license: str
    license_url: str
    page_url: str
    manual: bool
    files: tuple[SourceFile, ...]


@dataclass(frozen=True)
class Resolution:
    id: str
    precision: int


@dataclass(frozen=True)
class Attribute:
    name: str
    type: Literal["string", "number"]
    nullable: bool
    description: str


@dataclass(frozen=True)
class Layer:
    id: str
    title_ja: str
    title_en: str
    geometry: Geometry
    sources: tuple[str, ...]
    resolutions: tuple[Resolution, ...]
    attributes: tuple[Attribute, ...]
    license: str
    credit_ja: str
    credit_en: str
    enabled_by_default: bool
    feature_flag: str | None
    publish: bool
    hold: str | None

    @property
    def enabled(self) -> bool:
        return self.enabled_by_default or (self.feature_flag is not None and os.environ.get(self.feature_flag) == "1")

    @property
    def slug(self) -> str:
        return self.id.replace("/", "-")


@dataclass(frozen=True)
class Registry:
    layers: tuple[Layer, ...]
    sources: dict[str, Source]

    def layer(self, layer_id: str) -> Layer:
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        raise KeyError(layer_id)

    def enabled_layers(self) -> list[Layer]:
        return [layer for layer in self.layers if layer.enabled]

    def sources_for(self, layers: list[Layer]) -> list[Source]:
        ids = dict.fromkeys(sid for layer in layers for sid in layer.sources)
        return [self.sources[sid] for sid in ids]


def _require(data: dict, key: str, where: str):
    if key not in data:
        raise RegistryError(f"{where}: {key} がない")
    return data[key]


def _parse_source(path: Path) -> Source:
    data = yaml.safe_load(path.read_text())
    where = path.name
    sid = _require(data, "id", where)
    if path.stem != sid:
        raise RegistryError(f"{where}: ファイル名と id が違う")
    license_ = _require(data, "license", where)
    if license_ not in LICENSES:
        raise RegistryError(f"{where}: 知らないライセンス {license_}")
    manual = bool(data.get("manual", False))
    files = []
    for f in _require(data, "files", where):
        sha = f.get("sha256")
        if sha is not None and not SHA256.match(sha):
            raise RegistryError(f"{where}: sha256 の形が違う")
        if sha is None and not manual:
            raise RegistryError(f"{where}: 自動で取るファイルには sha256 が要る")
        files.append(SourceFile(url=f["url"], name=f["name"], sha256=sha, bytes=f.get("bytes")))
    return Source(
        id=sid,
        title=_require(data, "title", where),
        publisher=_require(data, "publisher", where),
        version=str(_require(data, "version", where)),
        retrieved=data.get("retrieved"),
        license=license_,
        license_url=_require(data, "license_url", where),
        page_url=_require(data, "page_url", where),
        manual=manual,
        files=tuple(files),
    )


def _parse_layer(data: dict, sources: dict[str, Source]) -> Layer:
    lid = _require(data, "id", "layers.yml")
    where = f"layers.yml {lid}"
    for sid in _require(data, "sources", where):
        if sid not in sources:
            raise RegistryError(f"{where}: sources/{sid}.yml がない")
    attributes = []
    for a in _require(data, "attributes", where):
        if not ATTRIBUTE_NAME.match(a["name"]):
            raise RegistryError(f"{where}: 属性名 {a['name']} は小文字のスネークケースで10文字以内にする")
        attributes.append(Attribute(a["name"], a["type"], bool(a.get("nullable", False)), a["description"]))
    if len({a.name for a in attributes}) != len(attributes):
        raise RegistryError(f"{where}: 属性名が重なっている")
    license_ = _require(data, "license", where)
    if license_ not in LICENSES:
        raise RegistryError(f"{where}: 知らないライセンス {license_}")
    publish = bool(_require(data, "publish", where))
    hold = data.get("hold")
    if not publish and not hold:
        raise RegistryError(f"{where}: publish: false には hold（理由）が要る")
    title = _require(data, "title", where)
    credit = _require(data, "credit", where)
    return Layer(
        id=lid,
        title_ja=title["ja"],
        title_en=title["en"],
        geometry=_require(data, "geometry", where),
        sources=tuple(data["sources"]),
        resolutions=tuple(Resolution(r["id"], int(r["precision"])) for r in _require(data, "resolutions", where)),
        attributes=tuple(attributes),
        license=license_,
        credit_ja=credit["ja"],
        credit_en=credit["en"],
        enabled_by_default=bool(_require(data, "enabled", where)),
        feature_flag=data.get("feature_flag"),
        publish=publish,
        hold=hold,
    )


def load(root: Path = ROOT) -> Registry:
    sources = {s.id: s for s in (_parse_source(p) for p in sorted((root / "sources").glob("*.yml")))}
    raw = yaml.safe_load((root / "layers.yml").read_text())
    layers = tuple(_parse_layer(item, sources) for item in raw["layers"])
    if len({layer.id for layer in layers}) != len(layers):
        raise RegistryError("layers.yml: レイヤーの id が重なっている")
    return Registry(layers=layers, sources=sources)
