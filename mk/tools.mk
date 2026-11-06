IMAGE ?= geojson-tools:local
# 簡略化の結果は CPU の種類で少し変わる（mapshaper を arm64 と amd64 で動かすと出力が違う）。
# data/ と docs/size-report.md を CI と同じにするため、イメージは linux/amd64 に固定する
PLATFORM := linux/amd64
# Python のコマンドは、イメージの中ではそのまま、手元では uv を通して動かす
PY_RUN := $(if $(GEOJSON_IN_IMAGE),,uv run --frozen)
# 取得した元データと途中のファイルの置き場。worktree をまたいで使い回すときは、外の場所を指定する
export GEOJSON_CACHE ?= $(CURDIR)/.cache
# イメージの中で作ったファイルの持ち主を、手元の利用者にそろえる
IN_IMAGE = docker run --rm --platform $(PLATFORM) -v "$(CURDIR)":/work -v "$(GEOJSON_CACHE)":/cache -e GEOJSON_CACHE=/cache -w /work -u "$(shell id -u):$(shell id -g)" -e HOME=/tmp -e GEOJSON_ENABLE_MARITIME $(IMAGE)

.PHONY: setup
setup: # 手元で開発するための依存（Python と Node）を入れる
	uv sync --frozen
	npm ci

.PHONY: build-image
build-image: # データを作る道具のイメージを作る（GDAL・tippecanoe・mapshaper・uv）
	docker build --platform $(PLATFORM) -t $(IMAGE) .

.PHONY: build
build: build-image # 取得から検証・パッケージ化までを、イメージの中で行う
	mkdir -p "$(GEOJSON_CACHE)"
	$(IN_IMAGE) make build-in-image

.PHONY: build-in-image
build-in-image: check-tools fetch build-layers build-formats package-data test # make build の中身。イメージの中で動かす

.PHONY: check-tools
check-tools: # 道具がそろっているかを、版を表示して確かめる
	gdalinfo --version
	tippecanoe --version
	mapshaper -v
	python --version
