install:
	uv sync

dev:
	uv run flask --debug --app page_analyzer:app run

run:
	uv run hexlet-python-package

test:
	uv run pytest

push:
	git add .; git commit -m 'some changes'; git push

lint:
	uv run ruff check .

format:
	uv run ruff check . --fix

build:
	./build.sh

PORT ?= 8000
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

.PHONY: install test lint selfcheck check build
