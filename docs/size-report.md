# サイズの報告

`make build` が書き出す報告です。手で直さないでください。

## 簡略化の前後

面積は WGS84 の楕円体の上で測った値です。

| レイヤー | 解像度 | 地物数（前→後） | 頂点数（前→後） | 面積の変化 | 面積が10%を超えて変わった地物 | 公開 |
| --- | --- | --- | --- | --- | --- | --- |
| `world/countries` | 50m | 250→250 | 547,478→107,693 | +0.012% | 47 | する |
| `world/countries` | 110m | 250→250 | 547,478→19,852 | -0.101% | 81 | する |

## ファイルの大きさ

GeoJSON と TopoJSON は、目標が 5MB で、上限が 10MB です。

| レイヤー | 解像度 | 形式 | 大きさ | 上限 | 判定 |
| --- | --- | --- | --- | --- | --- |
| `world/countries` | 50m | geojson | 2.16 MB | 10.00 MB | OK |
| `world/countries` | 50m | topojson | 1.30 MB | 10.00 MB | OK |
| `world/countries` | 110m | geojson | 407 KB | 10.00 MB | OK |
| `world/countries` | 110m | topojson | 278 KB | 10.00 MB | OK |
