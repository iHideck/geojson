# データ元の利用条件

各データ元の利用条件を、公式ページで確かめた結果です。確認日は 2026-11-06 です。条件が確かめられないデータは、リポジトリにも配布物にも GitHub Pages にも含めません。

## 結論

| レイヤー | 出典 | 条件 | 再配布 | クレジット | 公開時 |
| --- | --- | --- | --- | --- | --- |
| `world/countries` | Natural Earth v5.1.2 | パブリックドメイン | できる | 不要（任意） | 有効 |
| `japan/prefectures`, `japan/municipalities` | 国土数値情報「行政区域」2026年版（N03） | オープンデータ（CC BY 4.0） | できる。測量法の承認申請は要らない（国土地理院に確認済み） | 必要 | 有効 |
| `japan/islands` | 国土地理院「全国都道府県市区町村別面積調」付3「島面積」、Wikidata、総務省の団体コードの一覧 | 国土地理院コンテンツ利用規約（PDL1.0）、CC0、PDL1.0 | できる | 国土地理院と総務省の出典が必要 | 有効 |
| `world/eez`, `world/territorial-seas`, `world/contiguous-zones`, `world/high-seas` | Marine Regions（VLIZ） | CC BY 4.0。ほかの場所でダウンロードできるようにしないよう依頼あり | できる（VLIZ の許可を得た） | 必要 | 有効 |
| `world/baselines` | 領海法施行令の別表第一（日本の直線基線） | 権利の目的にならない（法令） | 基点の測地系を確かめるまで含めない | 出典を書く | 無効 |

## Natural Earth

- 対象は admin 0 countries（50m と 110m）と、日本の視点版 `ne_10m_admin_0_countries_jpn` です。
- 最新版は v5.1.2 です（GitHub `nvkelso/natural-earth-vector` の最新リリース）。
- 利用規約の原文は次のとおりです。「All versions of Natural Earth raster + vector map data found on this website are in the public domain.」「No permission is needed to use Natural Earth. Crediting the authors is unnecessary.」
- 国名の多言語表記（`NAME_JA` など）は Wikidata（CC0）から取ったと、同じページに書かれています。
- 日本の視点版は 10m にしかありません。50m と 110m の既定版では、北方領土がロシアに含まれます。扱いは `docs/disputed-areas.md` に書きます。

出典: [Natural Earth Terms of Use](https://www.naturalearthdata.com/about/terms-of-use/)

## 国土数値情報「行政区域」（N03）

- 最新は 2026年（令和8年）版で、2026年1月1日時点の行政界です。全国の zip（`N03-20260101_GML.zip`）は 765.94MB です。都道府県ごとの zip もあります。
- 個別ページの「このデータの使用許諾条件」は「オープンデータ（CC_BY_4.0）」です。
- サイトの利用規約は、2026年3月23日から「公共データ利用規約（第1.0版）」（PDL1.0）が既定になりました。PDL1.0 も、個別ページが示す政府標準利用規約準拠版も、CC BY 4.0 と互換です。
- 守ることは次の3つです。
  - 出典を書く。
  - 加工したことと、加工した主体を書く。
  - 加工したデータを、国が作った未加工のデータのように見せない。
- FAQ は、加工したデータを出典と加工の事実を書いたうえで再配布・販売できるとしています。
- 原典は国土地理院の「数値地図（国土基本情報）」です。個別ページには「測量法に基づく国土地理院長承認（複製）R 7JHf 351」とあります。
- 一部の市区町村に境界未定の地域があり、暫定の境界線で描かれています（個別ページの注記と「暫定境界線一覧」）。

出典の書き方（加工して配布する場合）:

```text
「国土数値情報（行政区域データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html）を加工して作成
```

出典:

- [国土数値情報 行政区域データ 2026年版](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html)
- [国土数値情報ダウンロードサイト 利用規約](https://nlftp.mlit.go.jp/ksj/other/agreement.html)
- [国土数値情報ダウンロードサイトコンテンツ利用規約（政府標準利用規約準拠版）](https://nlftp.mlit.go.jp/ksj/other/agreement_01.html)
- [公共データ利用規約（第1.0版）](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)
- [国土数値情報 よくある質問](https://nlftp.mlit.go.jp/ksj/other/faq.html)

### 確認済み: 測量法の承認申請は要らない

国土地理院の承認申請 Q&A の Q1-24 には、次のように書かれています。

> 承認を得た成果品の利用については、前提として承認を得た者からの許諾が必要です。複製承認を得て複製した成果を更に複製・使用する場合は申請が必要な場合がありますので、地図の利用手続フローに従ってください。

N03 は「複製」の承認を得て作られていて、簡略化した境界を GIS 用のデータとして再配布する使い方が申請不要になるかを、公式資料だけでは決められませんでした。そこで、この文書の末尾の問い合わせ文で国土地理院に問い合わせ、承認申請は要らないとの回答を得ました。

公開では、問い合わせに書いたとおりにします。

- 出典に「「国土数値情報（行政区域データ）」（国土交通省）を加工して作成」と、承認番号（測量法に基づく国土地理院長承認（複製）R 7JHf 351）を書く。
- 測量や、位置の精度が求められる用途には使えないことを書く。

出典:

- [国土地理院 承認申請 Q&A](https://www.gsi.go.jp/LAW/2930-qa.html)
- [国土地理院 地図の利用手続パンフレット（利用手続フロー）](https://www.gsi.go.jp/common/000223838.pdf)
- [測量法に基づく基本測量成果の複製・使用に関する申請について](https://www.gsi.go.jp/LAW/2930-index.html)

## 総務省「都道府県コード及び市区町村コード」

- 都道府県と市区町村の名前・読み・全国地方公共団体コードの照合と、英語名（読みのローマ字）に使います。使うのは令和6年1月1日更新の Excel です。
- 総務省のサイトの利用規約は PDL1.0 です。出典を書き、加工したことを書きます。
- 検査数字の付け方は、総務省「全国地方公共団体コード」仕様の 11 によります。

出典の書き方:

```text
総務省「都道府県コード及び市区町村コード」（https://www.soumu.go.jp/denshijiti/code.html）をもとに作成
```

出典:

- [全国地方公共団体コード](https://www.soumu.go.jp/denshijiti/code.html)
- [総務省 著作権について](https://www.soumu.go.jp/menu_kyotsuu/policy/tyosaku.html)
- [「全国地方公共団体コード」仕様](https://www.soumu.go.jp/main_content/000137948.pdf)

## 島の名称と位置（japan/islands）

- 島の一覧には、国土地理院「令和8年全国都道府県市区町村別面積調（7月1日時点）」の付3「島面積」を使います。1km² 以上の島について、島名・読み・面積・所属市区町村が載っています。北方領土の島も含みます。
- 面積調は国土地理院技術資料で、ウェブサイトから入手できるものは「国土地理院コンテンツ利用規約に従ってください。商用利用も可能です。」とされています。この規約も PDL1.0 が既定です。
- 島の位置は、Wikidata の項目の座標を使います。Wikidata の構造化データは CC0 です。項目は、版を固定した URL と SHA256 を `sources/wikidata-islands.yml` に記録します。
- 座標が所属市区町村の中にあることを N03 のポリゴンで確かめますが、N03 の形も値も配布物には入れません。
- 1km² 未満の竹島と沖ノ鳥島は、面積調の注記（隠岐の島町の「竹島の面積 0.20km2を含む」と、小笠原村の注記）にある名前で足します。読みは面積調に無いので空にします。
- 英語名は、面積調の読みをローマ字にして作ります。
- 使わない候補とその理由は次のとおりです。
  - Natural Earth の地名点には、日本の島が八丈島と南鳥島の2つしかありません。
  - 国土地理院「日本の島の数」は都道府県別の数だけで、島ごとの一覧はありません。

出典の書き方:

```text
出典：国土地理院ウェブサイト（https://www.gsi.go.jp/KOKUJYOHO/MENCHO-title.htm）「全国都道府県市区町村別面積調」を加工して作成
```

出典:

- [全国都道府県市区町村の面積](https://www.gsi.go.jp/KOKUJYOHO/MENCHO-title.htm)
- [国土地理院技術資料とその提供について](https://www.gsi.go.jp/REPORT/TECHNICAL/technical.html)
- [国土地理院コンテンツ利用規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html)
- [日本の島の数](https://www.gsi.go.jp/kihonjohochousa/islands_index.html)
- [Wikidata:Licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)

## Marine Regions（EEZ・領海・接続水域・公海）

- ライセンスの原文は次のとおりです。
  - 「Marine Regions' products have been licensed under CC-BY since Maritime Boundaries version 11 (2019).」
  - 「Please contact us for other uses of the Licensed Material beyond license terms.」
  - 「We kindly request our users not to make our products available for download elsewhere and to always refer to marineregions.org for the most up-to-date products and services.」
- 利用条件には、法的・経済的・航海の用途を想定しないこと、科学・教育・研究のためのものであることが書かれています。CC ライセンスと食い違う場合は CC ライセンスが優先するとも書かれています。
- 刊行物や製品に使ったら info@marineregions.org に知らせてほしいとあります。
- CC BY 4.0 だけを見れば再配布できますが、ダウンロードを他所に置かないでほしいという依頼があります。そこで VLIZ に、`docs/vliz-permission-request.md` の使い方を依頼し、すべて問題ないとの返事を得ました。
  - 簡略化版を、リポジトリ・GitHub Release・GitHub Pages・npm で配る
  - ビューアで、PMTiles にして見せる
  - QGIS のプロジェクトとスタイルに入れる
  - ビルドのときに自動で取得する
- 取得は、VLIZ の WFS（`geo.vliz.be/geoserver/MarineRegions/wfs`）から GeoJSON で行います。VLIZ から取得の方法の指定はありませんでした。応答の `timeStamp` だけが毎回変わるので、固定してから SHA256 で照合します。
- 依頼に書いたとおり、次のようにします。
  - ファイルのメタデータ・README・ビューア・`DATA_LICENSE.md` に、製品ごとの引用（DOI）・CC BY 4.0・marineregions.org へのリンク・簡略化したことを書く
  - 法的な境界ではなく、航海などに使えないことを書く
  - 細かい形は配らず、細かい形が要る人を marineregions.org に案内する

| データ | 版 | 引用（DOI） |
| --- | --- | --- |
| Exclusive Economic Zones (200NM) | v12（2023-10-25） | https://doi.org/10.14284/632 |
| Territorial Seas (12NM) | v4（2023-10-25） | https://doi.org/10.14284/633 |
| Contiguous Zones (24NM) | v4（2023-10-25） | https://doi.org/10.14284/630 |
| High Seas | v2（2024-10-10） | https://doi.org/10.14284/696 |
| Internal Waters | v4（2023-10-25） | https://doi.org/10.14284/631 |
| Archipelagic Waters | v4（2023-10-25） | https://doi.org/10.14284/629 |

引用の書き方（EEZ の例）:

```text
Flanders Marine Institute (2023). Maritime Boundaries Geodatabase: Maritime Boundaries and Exclusive Economic Zones (200NM), version 12. Available online at https://www.marineregions.org/. https://doi.org/10.14284/632
```

出典:

- [Marine Regions License, terms of use & citation](https://www.marineregions.org/disclaimer.php)
- [Marine Regions Downloads](https://www.marineregions.org/downloads.php)
- [Marine Regions Sources](https://www.marineregions.org/sources.php)

## 基線（world/baselines）

- Marine Regions のダウンロード一覧と出典のページには、基線のデータがありません。内水（Internal Waters）は直線基線の陸側、群島水域（Archipelagic Waters）は群島基線の陸側の水域として説明されています。
- 日本の直線基線は、「領海及び接続水域に関する法律施行令」（昭和52年政令第210号）別表第一の基点から作ります。別表には基点の緯度経度が 208 点あります。法令は著作権法第13条第1号により権利の目的になりません。基点の測地系は条文に書かれていないため要確認です。
- 世界の基線は、内水と群島水域の外縁から導くことを VLIZ が認めました。作るかは、これから決めます。
- 日本の直線基線は、基点の測地系（日本測地系か世界測地系か）を一次資料で確かめるまで、既定は無効にして含めません。施行令は平成13年政令第434号で改められ（2002年4月1日施行）、同じ日に測量法と水路業務法の改正（平成13年法律第53号）で世界測地系に移りましたが、別表の座標がどちらに従うかを書いた資料を見つけていません。

出典:

- [e-Gov 法令検索 領海及び接続水域に関する法律施行令](https://laws.e-gov.go.jp/law/352CO0000000210)
- [e-Gov 法令検索 著作権法](https://laws.e-gov.go.jp/law/345AC0000000048)

## ビューアに含めるもの

| もの | ライセンス | 確認 |
| --- | --- | --- |
| MapLibre GL JS 6.16.0 | BSD-3-Clause | npm の `license` |
| PMTiles 4.5.0 | BSD-3-Clause | npm の `license` |
| フォント | 配らない（端末のフォントを使う） | — |

OGP 画像やスクリーンショットに国土数値情報の境界を描くときは、画像の中にも出典を入れます。

## 未確認の事項

| 事項 | 影響する公開物 | 次にやること |
| --- | --- | --- |
| 施行令の基点の測地系 | `world/baselines`（施行令を使う場合） | 海上保安庁の資料で確かめる |

## 国土地理院への問い合わせ文の案

送り先は、国土地理院 地理空間情報部 情報企画課 審査係（gsi-tsu6f-fukusei@gxb.mlit.go.jp）です（地図の利用手続パンフレットの問い合わせ先）。

```text
件名: 国土数値情報（行政区域データ）を加工したデータの再配布と測量法の手続きについて

国土地理院 地理空間情報部 情報企画課 審査係 御中

国土数値情報「行政区域データ」2026年版（N03-20260101、測量法に基づく国土地理院長承認（複製）R 7JHf 351）を加工したデータの公開について、測量法第29条・第30条の承認申請が必要かを教えてください。

1. 予定している使い方
   - 都道府県界と市区町村界のポリゴンを、座標の桁を減らし（小数点以下4〜5桁）、形を簡略化します。
   - GeoJSON・GeoPackage などの形式で、GitHub 上に無償で公開します。営利目的ではありません。
   - 同じデータを、ウェブの地図ビューアで表示します。
   - 出典として「「国土数値情報（行政区域データ）」（国土交通省）を加工して作成」と承認番号を記載します。
   - 測量や、位置の精度が求められる用途には使えないことを明記します。
2. 伺いたいこと
   - 上記の公開に、測量法第29条（複製）または第30条（使用）の承認申請が必要か。
   - 必要な場合、申請者と手続きはどうなるか。

よろしくお願いいたします。

（差出人の名前と連絡先）
```
