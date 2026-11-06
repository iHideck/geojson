# geojson — Japan & World Boundaries

日本と世界の陸と海の境界を、同じ基準で重ねて使える軽いオープンデータ集です。いまは準備中で、データはまだ公開していません。

Lightweight GeoJSON boundaries for Japan and the world. Work in progress.

## 開発

必要なものは、Docker・make・[uv](https://docs.astral.sh/uv/)・Node.js 24 です。

| コマンド | すること |
| --- | --- |
| `make help` | コマンドの一覧を表示する |
| `make setup` | 手元で開発するための依存を入れる |
| `make build` | 取得から検証・パッケージ化までを、Docker のイメージの中で行う |
| `make lint` | Python のコードの書き方を検査する |
| `make test` | 単体テストと、リポジトリの決まりの検査を動かす |

## ライセンス

- コード: [MIT](LICENSE)
- データ: [DATA_LICENSE.md](DATA_LICENSE.md)
