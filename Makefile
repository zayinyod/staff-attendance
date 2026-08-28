# 開発用タスク定義
#
# devcontainer の Dockerfile からビルドしたイメージを使い、
# ホスト側から Django のテスト・静的検査・開発サーバーを実行する。
# devcontainer.json の features [Node] は適用されないため、
# フロントエンドの起動は対象外とする。

IMAGE       := staff-attendance-dev
DOCKERFILE  := .devcontainer/Dockerfile
CONTEXT     := .devcontainer
WORKSPACE   := /workspaces/staff_attendance
BACKEND_DIR := $(WORKSPACE)/staff_attendance
HOST_UID    := $(shell id -u)
HOST_GID    := $(shell id -g)

# コンテナ内で任意のコマンドを実行する共通形式
DOCKER_RUN = docker run --rm --user $(HOST_UID):$(HOST_GID) \
	-v $(CURDIR):$(WORKSPACE) \
	-w $(BACKEND_DIR) \
	$(IMAGE)

# 対話操作やポート公開を伴う場合の形式
DOCKER_RUN_IT = docker run --rm -it --user $(HOST_UID):$(HOST_GID) \
	-v $(CURDIR):$(WORKSPACE) \
	-w $(BACKEND_DIR)

.DEFAULT_GOAL := help

.PHONY: help build rebuild test test-file check migrations-check migrations \
        migrate seed loaddata lint serve shell django-shell collectstatic clean

help: ## タスク一覧を表示する
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

build: ## 開発用イメージをビルドする
	docker build -t $(IMAGE) -f $(DOCKERFILE) $(CONTEXT)

rebuild: ## キャッシュを使わずにイメージを再ビルドする
	docker build --no-cache -t $(IMAGE) -f $(DOCKERFILE) $(CONTEXT)

test: ## テストを実行する
	$(DOCKER_RUN) python manage.py test --verbosity 2

test-file: ## 指定したテストのみ実行する [make test-file T=attendance.tests.test_views]
	@test -n "$(T)" || { echo "T にテストパスを指定する [e.g. T=attendance.tests.test_views]"; exit 1; }
	$(DOCKER_RUN) python manage.py test $(T) --verbosity 2

check: ## Django の構成チェックを実行する
	$(DOCKER_RUN) python manage.py check

migrations-check: ## 未作成のマイグレーションがないか確認する
	$(DOCKER_RUN) python manage.py makemigrations --check --dry-run

migrations: ## マイグレーションを作成する
	$(DOCKER_RUN) python manage.py makemigrations attendance

migrate: ## マイグレーションを適用する
	$(DOCKER_RUN) python manage.py migrate

seed: migrate loaddata ## 新規環境の初期データを投入する [migrate + loaddata]

loaddata: ## 所属部署のフィクスチャを読み込む
	$(DOCKER_RUN) python manage.py loaddata departments

lint: ## flake8 で静的検査を実行する
	docker run --rm --user $(HOST_UID):$(HOST_GID) \
		-v $(CURDIR):$(WORKSPACE) -w $(WORKSPACE) $(IMAGE) \
		bash -c "pip install --quiet --disable-pip-version-check flake8 \
			&& flake8 --config .devcontainer/.flake8 staff_attendance/"

serve: ## 開発サーバーを起動する [http://localhost:8000]
	$(DOCKER_RUN_IT) -p 8000:8000 $(IMAGE) \
		python manage.py runserver 0.0.0.0:8000

shell: ## コンテナのシェルを起動する
	$(DOCKER_RUN_IT) $(IMAGE) bash

django-shell: ## Django シェルを起動する
	$(DOCKER_RUN_IT) $(IMAGE) python manage.py shell

collectstatic: ## 静的ファイルを STATIC_ROOT に収集する
	$(DOCKER_RUN) python manage.py collectstatic --noinput

clean: ## __pycache__ を削除する
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
