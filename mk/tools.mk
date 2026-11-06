IMAGE ?= geojson-tools:local
# Python のコマンドは、イメージの中ではそのまま、手元では uv を通して動かす
PY_RUN := $(if $(GEOJSON_IN_IMAGE),,uv run --frozen)
# イメージの中で作ったファイルの持ち主を、手元の利用者にそろえる
IN_IMAGE = docker run --rm -v "$(CURDIR)":/work -w /work -u "$(shell id -u):$(shell id -g)" -e HOME=/tmp -e GEOJSON_ENABLE_MARITIME $(IMAGE)

.PHONY: setup
setup: # 手元で開発するための依存（Python と Node）を入れる
	uv sync --frozen
	npm ci

.PHONY: build-image
build-image: # データを作る道具のイメージを作る（GDAL・tippecanoe・mapshaper・uv）
	docker build -t $(IMAGE) .

.PHONY: build
build: build-image # 取得から検証・パッケージ化までを、イメージの中で行う
	$(IN_IMAGE) make build-in-image

.PHONY: build-in-image
build-in-image: check-tools # make build の中身。イメージの中で動かす

.PHONY: check-tools
check-tools: # 道具がそろっているかを、版を表示して確かめる
	gdalinfo --version
	tippecanoe --version
	mapshaper -v
	python --version
