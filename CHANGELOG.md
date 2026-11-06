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
