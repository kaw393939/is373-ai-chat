UV ?= uv
.PHONY: setup migrate seed dev test test-e2e check build up
setup:
	$(UV) sync --frozen
	npm --prefix frontend ci
migrate:
	$(UV) run alembic upgrade head
seed:
	$(UV) run python -m app.cli seed
dev:
	$(UV) run uvicorn app.main:create_app --factory --reload
check:
	$(UV) run ruff check app tests deploy
	$(UV) run ruff format --check app tests deploy migrations
	npm --prefix frontend run build
test:
	$(UV) run pytest --cov --cov-report=term-missing --cov-report=xml:artifacts/coverage.xml
test-e2e:
	$(UV) run pytest tests/e2e -v
build:
	docker build --build-arg COMMIT_SHA=$$(git rev-parse HEAD) -t is373-chat:local .
up:
	docker compose up -d --wait db
	docker compose run --rm app alembic upgrade head
	docker compose run --rm app python -m app.cli seed
	docker compose up -d --wait app
