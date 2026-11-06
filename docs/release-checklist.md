# リリース前の確認

版を出す前に、上から順に確かめます。

## 1. 公開してよいデータか

1. `layers.yml` で `publish: true` のレイヤーが、利用条件を確かめたものだけかを見ます。
   - 都道府県境・市区町村境は、国土地理院から測量法の手続きの回答を得るまで `false` のままにします。
   - 海域（EEZ・領海・接続水域・基線・公海）は、VLIZ の許可を得るまで `enabled: false` と `publish: false` のままにします。
2. `docs/license-review.md` と `DATA_LICENSE.md` が、公開するレイヤーと合っているかを見ます。

## 2. データ

1. Mac の端末で、次を打ちます。

   ```sh
   cd ~/ghq/github.com/iHideck/geojson
   make build
   ```

2. テストがすべて通り、`git status` で `data/`・`docs/size-report.md`・`styles/` に差分が無いことを確かめます。
3. `docs/size-report.md` で、どのファイルも上限を超えていないことを確かめます。

## 3. QGIS

1. `make check-qgis` を打ち、QGIS の長期版と最新版の両方で通ることを確かめます。
2. 手元の QGIS で、`dist/release/geojson-boundaries-qgis.zip` を展開し、`geojson-boundaries.qgz` を開きます。次を確かめます。
   - 全レイヤーが表示され、色・線の太さ・破線が `styles/styles.yml` のとおりか
   - 島のラベルが日本語で出るか
   - レイヤーのプロパティの「情報」で、ソースが `./geojson-boundaries.gpkg` の相対パスか
3. `dist/release/geojson-boundaries.gpkg` を直接開き、既定のスタイルで表示されるかを確かめます。
4. Shapefile の zip を「ベクタレイヤを追加」で開き、日本語の属性が文字化けしないかを確かめます。

## 4. ビューア

1. `make serve-site` を打ちます（止めるときは Ctrl+C）。
2. `http://localhost:5173/geojson/` を、PC の幅とスマートフォンの幅で開き、次を確かめます。
   - 地球全体から日本へ移る演出と、「演出をスキップ」
   - 凡例の表示・不透明度・解像度の切り替え
   - 検索・地物の詳細カード・URL のコピー
   - 日本語と英語の切り替え
   - メニューの「データ」の、ダウンロードのリンク

## 5. 版を出す

1. `CHANGELOG.md` の `[Unreleased]` の中身を、`## [1.2.3] - 2026-12-01` のような版の節に移して、main に入れます。
2. main の先頭に `v1.2.3` の形のタグを打って push します。

   ```sh
   cd ~/ghq/github.com/iHideck/geojson
   git switch main && git pull
   git tag v1.2.3
   git push origin v1.2.3
   ```

3. GitHub の Actions の「リリース」が、データを作り直して GitHub Release を作り、GitHub Pages に出し、公開した後を確かめます。
4. Slack の #geojson-deploy に、成功の知らせが届くことを確かめます（シークレット `SLACK_WEBHOOK_URL_DEPLOY` を置いたとき）。

ビューアだけを直したときは、Actions の「GitHub Pages に出す（リリースなし）」を main で動かします。

## 初めて公開するとき

1. リポジトリの Settings → Pages で、Source を「GitHub Actions」にします。
2. Settings → Secrets and variables → Actions に、`SLACK_WEBHOOK_URL_DEPLOY` を置きます。
3. npm の `japan-world-boundaries` は、`make build` が `dist/npm` に組みます。公開するときは、中身を確かめてから `cd dist/npm && npm publish` を打ちます。

## QGIS の検査のイメージの版を上げる

`mk/check.mk` の `QGIS_IMAGES` の、タグと digest の両方を書き換えます。digest は次で調べます。

```sh
docker buildx imagetools inspect qgis/qgis:3.44.15
```
