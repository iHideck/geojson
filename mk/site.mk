.PHONY: setup-site
setup-site: # ビューアの依存を入れる
	npm ci --prefix site

.PHONY: serve-site
serve-site: # ビューアを手元で開く（http://localhost:5173/geojson/）。make build で作った dist/pages を読む。止めるときは Ctrl+C
	npm run dev --prefix site

.PHONY: build-site
build-site: # ビューアを site/dist に作る。make build で作った dist/pages のデータも入れる
	npm run build --prefix site

.PHONY: check-site
check-site: # ビューアの型と単体テストを確かめる
	npm run check --prefix site
	npm test --prefix site

.PHONY: capture-site
capture-site: # OGP と静止画（site/public/og.jpg）を、ビルドしたビューアから撮り直す。make build と make build-site の後に動かす
	npm run capture --prefix site

# 見た目の元の画面は、CI と同じ Playwright のイメージの中で撮る（フォントや描画が環境で変わらないように）
PLAYWRIGHT_IMAGE := mcr.microsoft.com/playwright:v1.64.1-noble@sha256:2f05f8a734509a7b3f26a912639488ee08f58a7b292d14d62271bcff9038768f

.PHONY: test-site
test-site: # ビューアをブラウザで確かめる（PMTiles の表示・操作・見た目）。make build の後に動かす
	docker run --rm -v "$(CURDIR)":/work -v /work/site/node_modules -w /work/site -e CI=1 -e HOME=/root $(PLAYWRIGHT_IMAGE) \
	  bash -c "npm ci --no-audit --no-fund && npm run build && npx playwright test"

.PHONY: update-site-snapshots
update-site-snapshots: # 見た目を変えたときに、見た目の元の画面（site/tests/*-snapshots）を撮り直す。make build の後に動かす
	docker run --rm -v "$(CURDIR)":/work -v /work/site/node_modules -w /work/site -e CI=1 -e HOME=/root $(PLAYWRIGHT_IMAGE) \
	  bash -c "npm ci --no-audit --no-fund && npm run build && npx playwright test --grep 見た目 --update-snapshots"

.PHONY: check-site-budget
check-site-budget: # ビューアの初めに読む JS と CSS の大きさを、予算と比べる。make build-site の後に動かす
	npm run budget --prefix site

.PHONY: check-site-lighthouse
check-site-lighthouse: # Lighthouse で、LCP（PC 2.5 秒、スマートフォン 4 秒）とアクセシビリティを確かめる。make build-site の後に動かす
	npm run lighthouse --prefix site
