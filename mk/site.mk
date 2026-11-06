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
