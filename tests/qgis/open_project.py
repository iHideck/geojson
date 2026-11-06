"""リリースの QGIS の zip を展開してプロジェクトを開き、全レイヤーをスタイル付きで描けるかを確かめる。

QGIS の Python で動かす（CI では QGIS の Docker イメージの中）。QGIS のイメージには日本語のフォントが無いので、
描いた絵のラベルは□になる。
使い方: python3 open_project.py <geojson-boundaries-qgis.zip> <描いた画像の出力先.png>
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qgis.core import (  # noqa: E402
    QgsApplication,
    QgsMapRendererParallelJob,
    QgsMapSettings,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QSize  # noqa: E402
from qgis.PyQt.QtGui import QColor  # noqa: E402

WHITE = QColor(255, 255, 255)


def colors(layer: QgsVectorLayer) -> list[str]:
    symbol = layer.renderer().symbol()
    # QColor の書式の列挙型は Qt5 と Qt6 で書き方が違うので、RGBA の値から作る
    return [
        "#{:02x}{:02x}{:02x}{:02x}".format(*symbol.symbolLayer(i).color().getRgb())
        for i in range(symbol.symbolLayerCount())
    ]


def check(folder: Path, image: Path) -> list[str]:
    problems = []
    project = QgsProject.instance()
    if not project.read(str(next(folder.glob("*.qgz")))):
        return [f"プロジェクトを読めない: {project.error()}"]
    visible = []
    for node in project.layerTreeRoot().findLayers():
        layer = node.layer()
        if layer is None or not layer.isValid():
            problems.append(f"{node.name()}: データを読めない（{layer.source() if layer else '無し'}）")
            continue
        if layer.featureCount() <= 0:
            problems.append(f"{node.name()}: 地物が無い")
        # GeoPackage を直接開いたときのスタイル（layer_styles）と、プロジェクトのスタイルが同じか
        direct = QgsVectorLayer(layer.source(), "direct", "ogr")
        if colors(direct) != colors(layer):
            problems.append(
                f"{node.name()}: プロジェクトと GeoPackage のスタイルが違う {colors(layer)} {colors(direct)}"
            )
        shown = "表示" if node.isVisible() else "非表示"
        print(f"{node.name()}: 地物 {layer.featureCount()}、色 {colors(layer)}、{shown}")
        if node.isVisible():
            visible.append(layer)
    settings = QgsMapSettings()
    settings.setLayers(visible)
    settings.setBackgroundColor(WHITE)
    settings.setOutputSize(QSize(800, 600))
    settings.setExtent(QgsRectangle(122, 20, 154, 46))
    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()
    rendered = job.renderedImage()
    rendered.save(str(image))
    painted = sum(
        rendered.pixelColor(x, y) != WHITE
        for x in range(0, rendered.width(), 4)
        for y in range(0, rendered.height(), 4)
    )
    share = painted / ((rendered.width() // 4) * (rendered.height() // 4))
    print(f"描いた画素の割合: {share:.1%}")
    if share < 0.05:
        problems.append(f"ほとんど何も描かれていない（{share:.1%}）")
    return problems


def main() -> int:
    archive, image = Path(sys.argv[1]), Path(sys.argv[2])
    app = QgsApplication([], False)
    app.initQgis()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(archive) as z:
                z.extractall(tmp)
            problems = check(Path(tmp), image)
    finally:
        QgsProject.instance().clear()
        app.exitQgis()
    for p in problems:
        print(f"問題: {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
