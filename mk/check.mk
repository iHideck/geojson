.PHONY: lint
lint: # Python のコードの書き方を検査する
	$(PY_RUN) ruff check .
	$(PY_RUN) ruff format --check .

.PHONY: test
test: # 単体テストと、リポジトリの決まりの検査を動かす
	$(PY_RUN) pytest

# QGIS の長期版（LTR）と最新版。イメージは amd64 だけ。版を上げるときは、タグと digest の両方を書き換える
QGIS_IMAGES := qgis/qgis:3.44.15@sha256:9c4afddd8eb4d03275e161b732d57ea402a1a5237eb5766957427530fd38afe0 qgis/qgis:4.2.3@sha256:5aae850e0204da0cc60421dce614f8030791e46ec7a31836bf45909761c9b839

.PHONY: check-qgis
check-qgis: # リリースの QGIS プロジェクトを、QGIS の長期版と最新版で開いて描けるかを確かめる。make build の後に動かす。描いた絵は dist/qgis/ に置く
	mkdir -p dist/qgis
	for image in $(QGIS_IMAGES); do \
	  tag=$${image%@*}; tag=$${tag#*:}; \
	  docker run --rm --platform linux/amd64 -u "$$(id -u):$$(id -g)" -e HOME=/tmp -e QT_QPA_PLATFORM=offscreen \
	    -v "$(CURDIR)/dist":/dist -v "$(CURDIR)/tests/qgis":/check:ro $$image \
	    python3 /check/open_project.py /dist/release/geojson-boundaries-qgis.zip /dist/qgis/$$tag.png || exit 1; \
	done
