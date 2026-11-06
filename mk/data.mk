.PHONY: fetch
fetch: # 有効なレイヤーの元データを $GEOJSON_CACHE/sources に取得し、台帳の SHA256 と照合する
	PYTHONPATH=scripts $(PY_RUN) python -m boundaries.fetch
