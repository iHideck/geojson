# geojson — Japan & World Boundaries

日本と世界の陸と海の境界を、同じ基準で重ねて使える軽いオープンデータ集です。ブラウザですぐ見られて、QGIS などの GIS からすぐ使えます。

Lightweight GeoJSON boundaries for Japan and the world, with an interactive map viewer and GIS-ready downloads. [English](#english)

> 境界は法的な境界を示しません。測量や航海など、位置の精度や安全に関わる用途には使えません。

## 地図で見る

https://ihideck.github.io/geojson/ （ビューア Midnight Chart）

## レイヤー

| レイヤー | 内容 | 解像度 | 出典 | 配布 |
| --- | --- | --- | --- | --- |
| `world/countries` | 国境 | 50m・110m | Natural Earth（日本の視点の版） | 配布中 |
| `us/states` | アメリカの州境 | 50m・110m | Natural Earth | 配布中 |
| `japan/islands` | 主な島（点） | medium | 国土地理院「面積調」、Wikidata | 配布中 |
| `japan/prefectures` | 都道府県境 | medium・low | 国土数値情報（行政区域） | 配布中 |
| `japan/municipalities` | 市区町村境 | medium・low | 国土数値情報（行政区域） | 配布中 |
| `world/eez`・`world/territorial-seas`・`world/contiguous-zones`・`world/high-seas` | 排他的経済水域・領海・接続水域・公海 | 50m・110m | Marine Regions（VLIZ。許可を得て簡略化） | 配布中 |
| `world/baselines` | 日本の直線基線 | 50m・110m | 領海法施行令 | 準備中（基点の測地系を確認中） |

係争地の扱いは [docs/disputed-areas.md](docs/disputed-areas.md)、ファイルの大きさと簡略化の前後の値は [docs/size-report.md](docs/size-report.md) にあります。

## ファイル

| 置き場所 | 中身 | URL |
| --- | --- | --- |
| [`data/`](data/) | TopoJSON・`metadata.json`・属性の CSV。GitHub の上で地図として見られる | 版を固定: `https://cdn.jsdelivr.net/gh/iHideck/geojson@v1.2.3/data/world/countries/110m.topojson` |
| GitHub Pages | PMTiles・FlatGeobuf・GeoJSON・`metadata.json`・STAC のカタログ。ブラウザから CORS と Range 要求で読める | 最新: `https://ihideck.github.io/geojson/latest/world/countries/110m.pmtiles` |
| [GitHub Release](https://github.com/iHideck/geojson/releases) | 全形式（GeoJSON・TopoJSON・GeoPackage・Shapefile・FlatGeobuf・GeoParquet・PMTiles）、QGIS プロジェクト、QML と SLD のスタイル、`SHA256SUMS` | 最新: `https://github.com/iHideck/geojson/releases/latest/download/world-countries-110m.fgb`<br>版を固定: `.../releases/download/v1.2.3/...` |

ファイル名は `<レイヤー>-<解像度>.<形式>` です（例: `world-countries-50m.geojson`）。座標は WGS84（EPSG:4326）で、GeoJSON は RFC 7946 に従います。

## 使い方

QGIS では、リリースの `geojson-boundaries-qgis.zip` を展開し、`geojson-boundaries.qgz` を開きます。全レイヤーがスタイル付きで表示されます。`geojson-boundaries.gpkg` だけを開いても、同じスタイルが使われます。

GDAL では、GitHub Pages の FlatGeobuf を、ダウンロードせずに読めます。

```sh
ogrinfo -so -al /vsicurl/https://ihideck.github.io/geojson/latest/world/countries/110m.fgb
```

MapLibre GL JS では、PMTiles を [pmtiles](https://github.com/protomaps/PMTiles) のプロトコルで読みます。タイルのレイヤーは、面の `countries`、隣と接する境界の線の `borders`、名前を置く点の `labels` です。海域のレイヤーの `borders` は、隣の区域との境界と外側の限界の線で、海岸に沿う部分を含みません。

```js
import maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";

maplibregl.addProtocol("pmtiles", new Protocol().tile);
map.addSource("countries", {
  type: "vector",
  url: "pmtiles://https://ihideck.github.io/geojson/latest/world/countries/50m.pmtiles",
});
map.addLayer({ id: "borders", type: "line", source: "countries", "source-layer": "borders" });
```

## ライセンス

- データ: [DATA_LICENSE.md](DATA_LICENSE.md)（レイヤーごとの条件と、クレジットの書き方）
- コード: [MIT](LICENSE)

## English

Lightweight boundaries of Japan and the world, drawn to one standard so the layers line up.

- Viewer: https://ihideck.github.io/geojson/ (Midnight Chart)
- Published now: `world/countries` (Natural Earth, Japanese point of view), `us/states` (Natural Earth), `japan/prefectures`, `japan/municipalities` and `japan/islands`. Maritime zones (EEZ, territorial seas, contiguous zones, high seas) are simplified from Marine Regions (VLIZ) with permission.
- Formats: GeoJSON, TopoJSON, GeoPackage with QGIS styles, a QGIS project, Shapefile (UTF-8), FlatGeobuf, GeoParquet, PMTiles and a STAC catalog. See the table above for URLs.
- Credits and licenses: [DATA_LICENSE.md](DATA_LICENSE.md). The boundaries have no legal status and must not be used for surveying or navigation.

## 開発

必要なものは、Docker・make・[uv](https://docs.astral.sh/uv/)・Node.js 24 です。

| コマンド | すること |
| --- | --- |
| `make help` | コマンドの一覧を表示する |
| `make setup` | 手元で開発するための依存を入れる |
| `make build` | 元データの取得から、配布形式・`data/`・npm パッケージまでを、Docker のイメージの中で作って検査する |
| `make lint` | Python のコードの書き方を検査する |
| `make test` | 単体テストと、リポジトリの決まりの検査を動かす |
| `make check-qgis` | リリースの QGIS プロジェクトを、QGIS の長期版と最新版で開いて描く |
| `make serve-site` | ビューアを手元で開く（`make build` の後） |
| `make check-site` | ビューアの型と単体テストを確かめる |

- `data/`・`docs/size-report.md`・`styles/` は、`make build` で作ったものをコミットします。簡略化の結果は CPU の種類で少し変わるので、`make build` は linux/amd64 のイメージで動きます。CI は、作り直した結果がコミットしたものと同じかを確かめます。
- レイヤーの出典・解像度・属性・クレジットは [`layers.yml`](layers.yml)、元データの URL と SHA256 は [`sources/`](sources/) に書きます。
- リリースの手順は [docs/release-checklist.md](docs/release-checklist.md) にあります。
