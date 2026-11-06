# サイズの報告

`make build` が書き出す報告です。手で直さないでください。

## 簡略化の前後

面積は WGS84 の楕円体の上で測った値です。

| レイヤー | 解像度 | 地物数（前→後） | 頂点数（前→後） | 面積の変化 | 面積が10%を超えて変わった地物 | 公開 |
| --- | --- | --- | --- | --- | --- | --- |
| `world/countries` | 50m | 250→250 | 547,478→107,693 | +0.012% | 47 | する |
| `world/countries` | 110m | 250→250 | 547,478→19,852 | -0.101% | 81 | する |
| `japan/prefectures` | medium | 47→47 | 15,722,602→58,788 | -0.041% | 0 | 保留（測量法の承認申請の要否を、国土地理院に確かめている） |
| `japan/prefectures` | low | 47→47 | 15,722,602→11,368 | -0.282% | 0 | 保留（測量法の承認申請の要否を、国土地理院に確かめている） |
| `japan/municipalities` | medium | 1,905→1,905 | 15,722,602→184,741 | -0.041% | 5 | 保留（測量法の承認申請の要否を、国土地理院に確かめている） |
| `japan/municipalities` | low | 1,905→1,905 | 15,722,602→38,412 | -0.282% | 212 | 保留（測量法の承認申請の要否を、国土地理院に確かめている） |
| `japan/islands` | medium | 340→337 | 340→337 | — | 0 | する |

## ファイルの大きさ

GeoJSON と TopoJSON は、目標が 5MB で、上限が 10MB です。

| レイヤー | 解像度 | 形式 | 大きさ | 上限 | 判定 |
| --- | --- | --- | --- | --- | --- |
| `world/countries` | 50m | geojson | 2.16 MB | 10.00 MB | OK |
| `world/countries` | 50m | topojson | 1.30 MB | 10.00 MB | OK |
| `world/countries` | 50m | fgb | 1.76 MB | 100.00 MB | OK |
| `world/countries` | 50m | parquet | 793 KB | 100.00 MB | OK |
| `world/countries` | 50m | shp | 995 KB | 100.00 MB | OK |
| `world/countries` | 50m | pmtiles | 1.54 MB | 50.00 MB | OK |
| `world/countries` | 110m | geojson | 407 KB | 10.00 MB | OK |
| `world/countries` | 110m | topojson | 278 KB | 10.00 MB | OK |
| `world/countries` | 110m | fgb | 386 KB | 100.00 MB | OK |
| `world/countries` | 110m | parquet | 152 KB | 100.00 MB | OK |
| `world/countries` | 110m | shp | 162 KB | 100.00 MB | OK |
| `world/countries` | 110m | pmtiles | 230 KB | 50.00 MB | OK |
| `japan/prefectures` | medium | geojson | 1.18 MB | 10.00 MB | OK |
| `japan/prefectures` | medium | topojson | 568 KB | 10.00 MB | OK |
| `japan/prefectures` | low | geojson | 218 KB | 10.00 MB | OK |
| `japan/prefectures` | low | topojson | 109 KB | 10.00 MB | OK |
| `japan/municipalities` | medium | geojson | 4.02 MB | 10.00 MB | OK |
| `japan/municipalities` | medium | topojson | 1.65 MB | 10.00 MB | OK |
| `japan/municipalities` | low | geojson | 1.03 MB | 10.00 MB | OK |
| `japan/municipalities` | low | topojson | 665 KB | 10.00 MB | OK |
| `japan/islands` | medium | geojson | 81 KB | 10.00 MB | OK |
| `japan/islands` | medium | topojson | 63 KB | 10.00 MB | OK |
| `japan/islands` | medium | fgb | 66 KB | 100.00 MB | OK |
| `japan/islands` | medium | parquet | 23 KB | 100.00 MB | OK |
| `japan/islands` | medium | shp | 17 KB | 100.00 MB | OK |
| `japan/islands` | medium | pmtiles | 119 KB | 50.00 MB | OK |
