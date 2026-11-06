# データのライセンス

このリポジトリのコードは [MIT](LICENSE) です。データには、元データの条件が及びます。元データの条件の確認結果は [docs/license-review.md](docs/license-review.md) にあります。

## レイヤーごとの条件

| レイヤー | 元データ | 元データの条件 | このリポジトリが加工したデータの条件 |
| --- | --- | --- | --- |
| `world/countries` | [Natural Earth](https://www.naturalearthdata.com/) | パブリックドメイン | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.ja) |
| `japan/prefectures`, `japan/municipalities` | [国土数値情報（行政区域データ）](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html)（国土交通省）、[都道府県コード及び市区町村コード](https://www.soumu.go.jp/denshijiti/code.html)（総務省） | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ja)、[公共データ利用規約（第1.0版）](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0) | CC BY 4.0 |
| `japan/islands` | [全国都道府県市区町村別面積調](https://www.gsi.go.jp/KOKUJYOHO/MENCHO-title.htm)（国土地理院）、[Wikidata](https://www.wikidata.org/)、都道府県コード及び市区町村コード（総務省） | [公共データ利用規約（第1.0版）](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)、CC0 | CC BY 4.0 |

都道府県境・市区町村境は、国土地理院に測量法の手続きを確かめるまで配布していません。海域（EEZ・領海・接続水域・基線・公海）のレイヤーは、利用の許可を確かめるまで配布していません。

## クレジットの書き方

データを使うときは、使ったレイヤーのクレジットを書いてください。

```text
国境: Made with Natural Earth.
都道府県境・市区町村境: 「国土数値情報（行政区域データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html）を加工して作成。名前と英語名は、総務省「都道府県コード及び市区町村コード」（https://www.soumu.go.jp/denshijiti/code.html）をもとに作成
島: 国土地理院「全国都道府県市区町村別面積調」（https://www.gsi.go.jp/KOKUJYOHO/MENCHO-title.htm）を加工して作成。位置は Wikidata（CC0）、所属の団体コードは総務省「都道府県コード及び市区町村コード」（https://www.soumu.go.jp/denshijiti/code.html）による
```

各ファイルの `metadata.json` に、出典・取得日・ライセンス・クレジット・加工の内容を書いています。

## 注意

境界は法的な境界を示しません。航海など、安全に関わる用途には使えません。

## English summary

The code is MIT-licensed. Each data layer keeps the terms of its source. `world/countries` is derived from Natural Earth (public domain) and released under CC0 1.0. `japan/prefectures` and `japan/municipalities` are derived from the National Land Numerical Information (MLIT, CC BY 4.0) and released under CC BY 4.0. `japan/islands` is derived from the GSI Area Survey (PDL 1.0) with positions from Wikidata (CC0), and released under CC BY 4.0. Maritime layers are not distributed. The boundaries have no legal status and must not be used for navigation.
