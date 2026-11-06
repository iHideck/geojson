"""styles/styles.yml から、QGIS の QML と SLD を書き出す。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

from boundaries.registry import ROOT, Layer

STYLES = ROOT / "styles" / "styles.yml"
# SLD の長さはピクセル。QGIS の書き出しと同じく、1mm を約 3.78 ピクセル（96dpi）にする
PX_PER_MM = 96 / 25.4


@dataclass(frozen=True)
class Style:
    layer_id: str
    geometry: str
    stroke: str
    width_mm: float = 0.3
    dash: tuple[float, ...] | None = None
    fill: str | None = None
    fill_opacity: float = 1.0
    size_mm: float = 2.0
    label: str | None = None


def load(path: Path = STYLES) -> dict[str, Style]:
    raw = yaml.safe_load(path.read_text())["layers"]
    return {
        layer_id: Style(layer_id, **{**s, "dash": tuple(s["dash"]) if s.get("dash") else None})
        for layer_id, s in raw.items()
    }


def _rgba(color: str, opacity: float = 1.0) -> str:
    r, g, b = (int(color[i : i + 2], 16) for i in (1, 3, 5))
    return f"{r},{g},{b},{round(opacity * 255)}"


def _options(values: dict[str, str]) -> str:
    rows = "".join(f'<Option name="{k}" type="QString" value="{escape(v)}"/>' for k, v in values.items())
    return f'<Option type="Map">{rows}</Option>'


def _line_layer(s: Style) -> str:
    options = {
        "line_color": _rgba(s.stroke),
        "line_width": f"{s.width_mm:g}",
        "line_width_unit": "MM",
        "line_style": "solid",
        "joinstyle": "round",
        "capstyle": "round",
        "use_custom_dash": "1" if s.dash else "0",
        "customdash": ";".join(f"{d:g}" for d in s.dash) if s.dash else "5;2",
        "customdash_unit": "MM",
    }
    return f'<layer class="SimpleLine" enabled="1" locked="0" pass="0">{_options(options)}</layer>'


def qml(s: Style) -> str:
    """QGIS のレイヤーのスタイル（QML）。描き方とラベルだけを持つ。"""
    if s.geometry == "polygon":
        fill = {
            "color": _rgba(s.fill, s.fill_opacity) if s.fill else "0,0,0,0",
            "style": "solid" if s.fill else "no",
            "outline_style": "no",
        }
        layers = f'<layer class="SimpleFill" enabled="1" locked="0" pass="0">{_options(fill)}</layer>{_line_layer(s)}'
        symbol = f'<symbol type="fill" name="0" alpha="1" clip_to_extent="1" force_rhr="0">{layers}</symbol>'
    elif s.geometry == "line":
        symbol = f'<symbol type="line" name="0" alpha="1" clip_to_extent="1" force_rhr="0">{_line_layer(s)}</symbol>'
    else:
        marker = {
            "name": "circle",
            "color": _rgba(s.stroke),
            "outline_color": "255,255,255,255",
            "outline_width": "0.3",
            "outline_width_unit": "MM",
            "size": f"{s.size_mm:g}",
            "size_unit": "MM",
        }
        layers = f'<layer class="SimpleMarker" enabled="1" locked="0" pass="0">{_options(marker)}</layer>'
        symbol = f'<symbol type="marker" name="0" alpha="1" clip_to_extent="1" force_rhr="0">{layers}</symbol>'
    renderer = (
        '<renderer-v2 type="singleSymbol" forceraster="0" symbollevels="0" enableorderby="0">'
        f"<symbols>{symbol}</symbols><rotation/><sizescale/></renderer-v2>"
    )
    labeling = ""
    if s.label:
        labeling = (
            '<labeling type="simple"><settings calloutType="simple">'
            f'<text-style fieldName="{s.label}" fontSize="9" fontSizeUnit="Point" textColor="20,20,20,255" '
            'isExpression="0"><text-buffer bufferDraw="1" bufferSize="0.8" bufferSizeUnits="MM" '
            'bufferColor="255,255,255,255"/></text-style>'
            '<placement placement="0" dist="1.2" distUnits="MM"/><rendering scaleVisibility="0"/>'
            "</settings></labeling>"
        )
    enabled = "1" if s.label else "0"
    return (
        "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"
        f'<qgis version="3.30.1" styleCategories="Symbology|Labeling" labelsEnabled="{enabled}">'
        f"{renderer}{labeling}</qgis>\n"
    )


def _stroke_sld(s: Style) -> str:
    parts = [
        f'<se:SvgParameter name="stroke">{s.stroke.lower()}</se:SvgParameter>',
        f'<se:SvgParameter name="stroke-width">{s.width_mm * PX_PER_MM:.2f}</se:SvgParameter>',
        '<se:SvgParameter name="stroke-linejoin">round</se:SvgParameter>',
    ]
    if s.dash:
        dash = " ".join(f"{d * PX_PER_MM:.2f}" for d in s.dash)
        parts.append(f'<se:SvgParameter name="stroke-dasharray">{dash}</se:SvgParameter>')
    return f"<se:Stroke>{''.join(parts)}</se:Stroke>"


def sld(s: Style, title: str) -> str:
    """OGC の SLD 1.1。QGIS 以外の GIS でも読める。"""
    if s.geometry == "polygon":
        fill = ""
        if s.fill:
            fill = (
                f'<se:Fill><se:SvgParameter name="fill">{s.fill.lower()}</se:SvgParameter>'
                f'<se:SvgParameter name="fill-opacity">{s.fill_opacity:g}</se:SvgParameter></se:Fill>'
            )
        symbolizer = f"<se:PolygonSymbolizer>{fill}{_stroke_sld(s)}</se:PolygonSymbolizer>"
    elif s.geometry == "line":
        symbolizer = f"<se:LineSymbolizer>{_stroke_sld(s)}</se:LineSymbolizer>"
    else:
        symbolizer = (
            "<se:PointSymbolizer><se:Graphic><se:Mark><se:WellKnownName>circle</se:WellKnownName>"
            f'<se:Fill><se:SvgParameter name="fill">{s.stroke.lower()}</se:SvgParameter></se:Fill>'
            '<se:Stroke><se:SvgParameter name="stroke">#ffffff</se:SvgParameter></se:Stroke></se:Mark>'
            f"<se:Size>{s.size_mm * PX_PER_MM:.1f}</se:Size></se:Graphic></se:PointSymbolizer>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:se="http://www.opengis.net/se" '
        'xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.1.0" '
        'xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">'
        f"<NamedLayer><se:Name>{escape(title)}</se:Name><UserStyle><se:Name>{escape(title)}</se:Name>"
        f"<se:FeatureTypeStyle><se:Rule><se:Name>{escape(title)}</se:Name>{symbolizer}</se:Rule>"
        "</se:FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>\n"
    )


def write(layer: Layer, style: Style, folder: Path) -> list[Path]:
    qml_path, sld_path = folder / f"{layer.slug}.qml", folder / f"{layer.slug}.sld"
    qml_path.write_text(qml(style))
    sld_path.write_text(sld(style, layer.title_ja))
    return [qml_path, sld_path]
