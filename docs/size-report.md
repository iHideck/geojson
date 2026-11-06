# サイズの報告

`make build` が書き出す報告です。手で直さないでください。

## 簡略化の前後

面積は WGS84 の楕円体の上で測った値です。

| レイヤー | 解像度 | 地物数（前→後） | 頂点数（前→後） | 面積の変化 | 面積が10%を超えて変わった地物 | 公開 |
| --- | --- | --- | --- | --- | --- | --- |
| `world/countries` | 50m | 250→250 | 547,478→107,693 | +0.012% | 47 | する |
| `world/countries` | 110m | 250→250 | 547,478→19,852 | -0.101% | 81 | する |
| `japan/prefectures` | medium | 47→47 | 15,722,602→58,788 | -0.041% | 0 | する |
| `japan/prefectures` | low | 47→47 | 15,722,602→11,368 | -0.282% | 0 | する |
| `japan/municipalities` | medium | 1,905→1,905 | 15,722,602→184,741 | -0.041% | 5 | する |
| `japan/municipalities` | low | 1,905→1,905 | 15,722,602→38,412 | -0.282% | 212 | する |
| `japan/islands` | medium | 340→337 | 340→337 | — | 0 | する |
| `world/eez` | 50m | 285→285 | 10,187,935→99,573 | +0.050% | 5 | する |
| `world/eez` | 110m | 285→285 | 10,187,935→21,240 | +0.168% | 32 | する |
| `world/territorial-seas` | 50m | 230→230 | 4,438,257→54,635 | -0.500% | 5 | する |
| `world/territorial-seas` | 110m | 230→230 | 4,438,257→14,701 | -4.019% | 87 | する |
| `world/contiguous-zones` | 50m | 220→220 | 3,895,934→49,655 | -0.057% | 0 | する |
| `world/contiguous-zones` | 110m | 220→220 | 3,895,934→13,206 | -0.748% | 53 | する |
| `world/high-seas` | 50m | 1→1 | 503,184→14,090 | +0.020% | 0 | する |
| `world/high-seas` | 110m | 1→1 | 503,184→3,456 | +0.183% | 0 | する |

## ファイルの大きさ

GeoJSON と TopoJSON は、目標が 5MB で、上限が 10MB です。

| レイヤー | 解像度 | 形式 | 大きさ | 上限 | 判定 |
| --- | --- | --- | --- | --- | --- |
| `world/countries` | 50m | geojson | 2.16 MB | 10.00 MB | OK |
| `world/countries` | 50m | topojson | 1.30 MB | 10.00 MB | OK |
| `world/countries` | 50m | fgb | 1.76 MB | 100.00 MB | OK |
| `world/countries` | 50m | parquet | 793 KB | 100.00 MB | OK |
| `world/countries` | 50m | shp | 995 KB | 100.00 MB | OK |
| `world/countries` | 50m | pmtiles | 1.61 MB | 50.00 MB | OK |
| `world/countries` | 110m | geojson | 407 KB | 10.00 MB | OK |
| `world/countries` | 110m | topojson | 278 KB | 10.00 MB | OK |
| `world/countries` | 110m | fgb | 386 KB | 100.00 MB | OK |
| `world/countries` | 110m | parquet | 152 KB | 100.00 MB | OK |
| `world/countries` | 110m | shp | 162 KB | 100.00 MB | OK |
| `world/countries` | 110m | pmtiles | 267 KB | 50.00 MB | OK |
| `japan/prefectures` | medium | geojson | 1.18 MB | 10.00 MB | OK |
| `japan/prefectures` | medium | topojson | 568 KB | 10.00 MB | OK |
| `japan/prefectures` | medium | fgb | 983 KB | 100.00 MB | OK |
| `japan/prefectures` | medium | parquet | 385 KB | 100.00 MB | OK |
| `japan/prefectures` | medium | shp | 453 KB | 100.00 MB | OK |
| `japan/prefectures` | medium | pmtiles | 772 KB | 50.00 MB | OK |
| `japan/prefectures` | low | geojson | 218 KB | 10.00 MB | OK |
| `japan/prefectures` | low | topojson | 109 KB | 10.00 MB | OK |
| `japan/prefectures` | low | fgb | 201 KB | 100.00 MB | OK |
| `japan/prefectures` | low | parquet | 75 KB | 100.00 MB | OK |
| `japan/prefectures` | low | shp | 72 KB | 100.00 MB | OK |
| `japan/prefectures` | low | pmtiles | 114 KB | 50.00 MB | OK |
| `japan/municipalities` | medium | geojson | 4.02 MB | 10.00 MB | OK |
| `japan/municipalities` | medium | topojson | 1.65 MB | 10.00 MB | OK |
| `japan/municipalities` | medium | fgb | 3.23 MB | 100.00 MB | OK |
| `japan/municipalities` | medium | parquet | 1.04 MB | 100.00 MB | OK |
| `japan/municipalities` | medium | shp | 1.32 MB | 100.00 MB | OK |
| `japan/municipalities` | medium | pmtiles | 2.81 MB | 50.00 MB | OK |
| `japan/municipalities` | low | geojson | 1.03 MB | 10.00 MB | OK |
| `japan/municipalities` | low | topojson | 665 KB | 10.00 MB | OK |
| `japan/municipalities` | low | fgb | 962 KB | 100.00 MB | OK |
| `japan/municipalities` | low | parquet | 252 KB | 100.00 MB | OK |
| `japan/municipalities` | low | shp | 269 KB | 100.00 MB | OK |
| `japan/municipalities` | low | pmtiles | 1.08 MB | 50.00 MB | OK |
| `japan/islands` | medium | geojson | 81 KB | 10.00 MB | OK |
| `japan/islands` | medium | topojson | 63 KB | 10.00 MB | OK |
| `japan/islands` | medium | fgb | 66 KB | 100.00 MB | OK |
| `japan/islands` | medium | parquet | 23 KB | 100.00 MB | OK |
| `japan/islands` | medium | shp | 18 KB | 100.00 MB | OK |
| `japan/islands` | medium | pmtiles | 125 KB | 50.00 MB | OK |
| `world/eez` | 50m | geojson | 2.01 MB | 10.00 MB | OK |
| `world/eez` | 50m | topojson | 1.31 MB | 10.00 MB | OK |
| `world/eez` | 50m | fgb | 1.59 MB | 100.00 MB | OK |
| `world/eez` | 50m | parquet | 794 KB | 100.00 MB | OK |
| `world/eez` | 50m | shp | 961 KB | 100.00 MB | OK |
| `world/eez` | 50m | pmtiles | 1.61 MB | 50.00 MB | OK |
| `world/eez` | 110m | geojson | 439 KB | 10.00 MB | OK |
| `world/eez` | 110m | topojson | 266 KB | 10.00 MB | OK |
| `world/eez` | 110m | fgb | 391 KB | 100.00 MB | OK |
| `world/eez` | 110m | parquet | 153 KB | 100.00 MB | OK |
| `world/eez` | 110m | shp | 171 KB | 100.00 MB | OK |
| `world/eez` | 110m | pmtiles | 251 KB | 50.00 MB | OK |
| `world/territorial-seas` | 50m | geojson | 1.12 MB | 10.00 MB | OK |
| `world/territorial-seas` | 50m | topojson | 772 KB | 10.00 MB | OK |
| `world/territorial-seas` | 50m | fgb | 913 KB | 100.00 MB | OK |
| `world/territorial-seas` | 50m | parquet | 456 KB | 100.00 MB | OK |
| `world/territorial-seas` | 50m | shp | 540 KB | 100.00 MB | OK |
| `world/territorial-seas` | 50m | pmtiles | 1.00 MB | 50.00 MB | OK |
| `world/territorial-seas` | 110m | geojson | 308 KB | 10.00 MB | OK |
| `world/territorial-seas` | 110m | topojson | 214 KB | 10.00 MB | OK |
| `world/territorial-seas` | 110m | fgb | 283 KB | 100.00 MB | OK |
| `world/territorial-seas` | 110m | parquet | 118 KB | 100.00 MB | OK |
| `world/territorial-seas` | 110m | shp | 125 KB | 100.00 MB | OK |
| `world/territorial-seas` | 110m | pmtiles | 225 KB | 50.00 MB | OK |
| `world/contiguous-zones` | 50m | geojson | 1.03 MB | 10.00 MB | OK |
| `world/contiguous-zones` | 50m | topojson | 735 KB | 10.00 MB | OK |
| `world/contiguous-zones` | 50m | fgb | 831 KB | 100.00 MB | OK |
| `world/contiguous-zones` | 50m | parquet | 427 KB | 100.00 MB | OK |
| `world/contiguous-zones` | 50m | shp | 502 KB | 100.00 MB | OK |
| `world/contiguous-zones` | 50m | pmtiles | 1.01 MB | 50.00 MB | OK |
| `world/contiguous-zones` | 110m | geojson | 283 KB | 10.00 MB | OK |
| `world/contiguous-zones` | 110m | topojson | 217 KB | 10.00 MB | OK |
| `world/contiguous-zones` | 110m | fgb | 259 KB | 100.00 MB | OK |
| `world/contiguous-zones` | 110m | parquet | 112 KB | 100.00 MB | OK |
| `world/contiguous-zones` | 110m | shp | 117 KB | 100.00 MB | OK |
| `world/contiguous-zones` | 110m | pmtiles | 247 KB | 50.00 MB | OK |
| `world/high-seas` | 50m | geojson | 293 KB | 10.00 MB | OK |
| `world/high-seas` | 50m | topojson | 201 KB | 10.00 MB | OK |
| `world/high-seas` | 50m | fgb | 222 KB | 100.00 MB | OK |
| `world/high-seas` | 50m | parquet | 130 KB | 100.00 MB | OK |
| `world/high-seas` | 50m | shp | 145 KB | 100.00 MB | OK |
| `world/high-seas` | 50m | pmtiles | 402 KB | 50.00 MB | OK |
| `world/high-seas` | 110m | geojson | 65 KB | 10.00 MB | OK |
| `world/high-seas` | 110m | topojson | 47 KB | 10.00 MB | OK |
| `world/high-seas` | 110m | fgb | 56 KB | 100.00 MB | OK |
| `world/high-seas` | 110m | parquet | 33 KB | 100.00 MB | OK |
| `world/high-seas` | 110m | shp | 33 KB | 100.00 MB | OK |
| `world/high-seas` | 110m | pmtiles | 50 KB | 50.00 MB | OK |
