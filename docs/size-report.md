# サイズの報告

`make build` が書き出す報告です。手で直さないでください。

## 簡略化の前後

面積は WGS84 の楕円体の上で測った値です。

| レイヤー | 解像度 | 地物数（前→後） | 頂点数（前→後） | 面積の変化 | 面積が10%を超えて変わった地物 | 公開 |
| --- | --- | --- | --- | --- | --- | --- |
| `world/countries` | 50m | 250→250 | 547,478→107,693 | +0.012% | 47 | する |
| `world/countries` | 110m | 250→250 | 547,478→19,852 | -0.101% | 81 | する |
| `japan/prefectures` | medium | 47→47 | 15,722,602→58,787 | -0.041% | 0 | 保留（測量法の承認申請の要否を、国土地理院に確かめている） |
| `japan/prefectures` | low | 47→47 | 15,722,602→11,138 | -0.282% | 0 | 保留（測量法の承認申請の要否を、国土地理院に確かめている） |
| `japan/municipalities` | medium | 1,905→1,905 | 15,722,602→184,740 | -0.041% | 5 | 保留（測量法の承認申請の要否を、国土地理院に確かめている） |
| `japan/municipalities` | low | 1,905→1,905 | 15,722,602→38,164 | -0.282% | 213 | 保留（測量法の承認申請の要否を、国土地理院に確かめている） |

## ファイルの大きさ

GeoJSON と TopoJSON は、目標が 5MB で、上限が 10MB です。

| レイヤー | 解像度 | 形式 | 大きさ | 上限 | 判定 |
| --- | --- | --- | --- | --- | --- |
| `world/countries` | 50m | geojson | 2.16 MB | 10.00 MB | OK |
| `world/countries` | 50m | topojson | 1.30 MB | 10.00 MB | OK |
| `world/countries` | 110m | geojson | 407 KB | 10.00 MB | OK |
| `world/countries` | 110m | topojson | 278 KB | 10.00 MB | OK |
| `japan/prefectures` | medium | geojson | 1.18 MB | 10.00 MB | OK |
| `japan/prefectures` | medium | topojson | 568 KB | 10.00 MB | OK |
| `japan/prefectures` | low | geojson | 214 KB | 10.00 MB | OK |
| `japan/prefectures` | low | topojson | 106 KB | 10.00 MB | OK |
| `japan/municipalities` | medium | geojson | 4.02 MB | 10.00 MB | OK |
| `japan/municipalities` | medium | topojson | 1.65 MB | 10.00 MB | OK |
| `japan/municipalities` | low | geojson | 1.03 MB | 10.00 MB | OK |
| `japan/municipalities` | low | topojson | 661 KB | 10.00 MB | OK |
