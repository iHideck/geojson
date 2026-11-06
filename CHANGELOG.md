# 変更履歴

版ごとの変更を書きます。形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に、版の付け方は [Semantic Versioning](https://semver.org/lang/ja/) に従います。

## [Unreleased]

### 追加

- データ元の利用条件の確認結果（`docs/license-review.md`）と、VLIZ への確認メールの下書き（`docs/vliz-permission-request.md`）
- コードのライセンス（`LICENSE`、MIT）とデータのライセンス（`DATA_LICENSE.md`）
- データを作る道具の Docker イメージと、`make` のコマンド
- 元データの台帳（`sources/`）とレイヤーの登録表（`layers.yml`）、取得と SHA256 の照合（`make fetch`）
- 世界の国境 `world/countries`（50m・110m）。Natural Earth の日本の視点版から作り、北方領土・竹島・尖閣諸島などの島を残す
- `metadata.json` の JSON Schema、サイズの報告（`docs/size-report.md`）、係争地の扱い（`docs/disputed-areas.md`）
- 都道府県境 `japan/prefectures` と市区町村境 `japan/municipalities`（medium・low）。国土数値情報から作り、全国地方公共団体コード（検査数字付き）と英語名を付ける。測量法の手続きの確認が済むまで公開しない
- 主な島 `japan/islands`。国土地理院の面積調の 1km² 以上の島と竹島・沖ノ鳥島を、Wikidata の座標で点にする
- 海域（EEZ・領海・接続水域・公海・基線）の処理。既定は無効で、`GEOJSON_ENABLE_MARITIME=1` のときだけ作る。日本の直線基線は領海法施行令の別表第一から作る
- 配布形式。リリースには GeoPackage（QGIS のスタイル入り）・QGIS プロジェクト・Shapefile（UTF-8）・FlatGeobuf・GeoParquet・PMTiles・属性の CSV・QML と SLD のスタイル・`SHA256SUMS` を、GitHub Pages には PMTiles・FlatGeobuf・GeoJSON・`metadata.json`・STAC のカタログを置く
- ビューアが読む目録（`latest/catalog.json`）と検索の索引（`latest/search.json`）。PMTiles の地物に、索引の行と同じ番号を付ける
- ビューア Midnight Chart の地図。MapLibre GL JS と PMTiles で、GitHub Pages の上だけで動く。ズームに応じて解像度を切り替え、手動でも選べる
- リリースと GitHub Pages のデプロイのワークフロー。v で始まるタグで GitHub Release を作って GitHub Pages に出し、公開した後に Range 要求と CORS を確かめる。リリース前の確認の手順（`docs/release-checklist.md`）
