# データのライセンス

このリポジトリのコードは [MIT](LICENSE) です。データには、元データの条件が及びます。元データの条件の確認結果は [docs/license-review.md](docs/license-review.md) にあります。

## レイヤーごとの条件

| レイヤー | 元データ | 元データの条件 | このリポジトリが加工したデータの条件 |
| --- | --- | --- | --- |
| `world/countries`, `us/states`, `china/provinces` | [Natural Earth](https://www.naturalearthdata.com/) | パブリックドメイン | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.ja) |
| `japan/prefectures`, `japan/municipalities` | [国土数値情報（行政区域データ）](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html)（国土交通省）、[都道府県コード及び市区町村コード](https://www.soumu.go.jp/denshijiti/code.html)（総務省） | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ja)、[公共データ利用規約（第1.0版）](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0) | CC BY 4.0 |
| `japan/islands` | [全国都道府県市区町村別面積調](https://www.gsi.go.jp/KOKUJYOHO/MENCHO-title.htm)（国土地理院）、[Wikidata](https://www.wikidata.org/)、都道府県コード及び市区町村コード（総務省） | [公共データ利用規約（第1.0版）](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)、CC0 | CC BY 4.0 |
| `world/eez`, `world/territorial-seas`, `world/contiguous-zones`, `world/high-seas` | [Marine Regions](https://www.marineregions.org/)（Flanders Marine Institute、VLIZ） | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ja)。VLIZ の許可を得て、簡略化版を配る | CC BY 4.0 |

基線（`world/baselines`）は、施行令の基点の測地系を確かめるまで配布していません。

Marine Regions の海域は、法的・経済的・航海の用途に使えません。細かい形が要るときは、[marineregions.org](https://www.marineregions.org/) から取得してください。

## クレジットの書き方

データを使うときは、使ったレイヤーのクレジットを書いてください。

```text
国境・アメリカの州境・中国の省境: Made with Natural Earth.
都道府県境・市区町村境: 「国土数値情報（行政区域データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html）を加工して作成（測量法に基づく国土地理院長承認（複製）R 7JHf 351）。名前と英語名は、総務省「都道府県コード及び市区町村コード」（https://www.soumu.go.jp/denshijiti/code.html）をもとに作成
島: 国土地理院「全国都道府県市区町村別面積調」（https://www.gsi.go.jp/KOKUJYOHO/MENCHO-title.htm）を加工して作成。位置は Wikidata（CC0）、所属の団体コードは総務省「都道府県コード及び市区町村コード」（https://www.soumu.go.jp/denshijiti/code.html）による
排他的経済水域: Flanders Marine Institute (2023). Maritime Boundaries Geodatabase: Maritime Boundaries and Exclusive Economic Zones (200NM), version 12. Available online at https://www.marineregions.org/. https://doi.org/10.14284/632 （geojson が簡略化して作成）
領海: Flanders Marine Institute (2023). Maritime Boundaries Geodatabase: Territorial Seas (12NM), version 4. Available online at https://www.marineregions.org/. https://doi.org/10.14284/633 （geojson が簡略化して作成）
接続水域: Flanders Marine Institute (2023). Maritime Boundaries Geodatabase: Contiguous Zones (24NM), version 4. Available online at https://www.marineregions.org/. https://doi.org/10.14284/630 （geojson が簡略化して作成）
公海: Flanders Marine Institute (2024). Maritime Boundaries Geodatabase: High Seas, version 2. Available online at https://www.marineregions.org/. https://doi.org/10.14284/696 （geojson が簡略化して作成）
```

各ファイルの `metadata.json` に、出典・取得日・ライセンス・クレジット・加工の内容を書いています。

## 注意

境界は法的な境界を示しません。測量や航海など、位置の精度や安全に関わる用途には使えません。

## English summary

The code is MIT-licensed. Each data layer keeps the terms of its source. `world/countries`, `us/states` and `china/provinces` are derived from Natural Earth (public domain) and released under CC0 1.0. `japan/prefectures` and `japan/municipalities` are derived from the National Land Numerical Information (MLIT, CC BY 4.0) and released under CC BY 4.0. `japan/islands` is derived from the GSI Area Survey (PDL 1.0) with positions from Wikidata (CC0), and released under CC BY 4.0. The maritime layers (`world/eez`, `world/territorial-seas`, `world/contiguous-zones`, `world/high-seas`) are simplified from Marine Regions (Flanders Marine Institute, CC BY 4.0) with the permission of VLIZ, and released under CC BY 4.0. They must not be used for legal, economic or navigational purposes. Japan's straight baselines (`world/baselines`) are not distributed. The boundaries have no legal status and must not be used for surveying, navigation or other purposes that need positional accuracy or safety.
