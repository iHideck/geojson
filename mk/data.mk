.PHONY: fetch
fetch: # 有効なレイヤーの元データを $GEOJSON_CACHE/sources に取得し、台帳の SHA256 と照合する
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.fetch

.PHONY: build-layers
build-layers: # 有効なレイヤーを dist/ に作る（形・metadata.json・簡略化の前後の値）
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.build

.PHONY: package-data
package-data: # 公開するレイヤーを data/ に詰め、docs/size-report.md を書き直す
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.package
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.report
