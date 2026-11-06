.PHONY: fetch
fetch: # 有効なレイヤーの元データを $GEOJSON_CACHE/sources に取得し、台帳の SHA256 と照合する
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.fetch

.PHONY: build-layers
build-layers: # 有効なレイヤーを dist/ に作る（形・metadata.json・簡略化の前後の値）
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.build

.PHONY: build-formats
build-formats: # 公開するレイヤーの配布形式を、dist/release（リリース）と dist/pages（GitHub Pages のデータと STAC）に作る。イメージの中で動かす
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.formats

.PHONY: package-data
package-data: # 公開するレイヤーを data/ に詰め、styles/ の QML と SLD と docs/size-report.md を書き直す
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.package
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.report

.PHONY: build-npm
build-npm: # npm パッケージ japan-world-boundaries の中身を dist/npm に組む（公開はしない）。package-data の後に動かす
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.npm_package
