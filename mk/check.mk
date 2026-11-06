.PHONY: lint
lint: # Python のコードの書き方を検査する
	$(PY_RUN) ruff check .
	$(PY_RUN) ruff format --check .

.PHONY: test
test: # 単体テストと、リポジトリの決まりの検査を動かす
	$(PY_RUN) pytest
