# 取得から検証・パッケージ化までを make build の1回で行う。重い処理は Docker のイメージの中で動く
include mk/tools.mk mk/data.mk mk/check.mk mk/site.mk

.PHONY: help
.DEFAULT_GOAL := help
help: # 使えるコマンドを表示する
	@grep -h -E '^[a-z][a-z0-9-]*:.*?# .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?# "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
