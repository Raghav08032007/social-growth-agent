.PHONY: up down test lint migrate seed
up:
	python scripts/init_local.py
	docker compose up --build -d
down:
	docker compose down
test:
	python -m unittest discover -s backend -p 'test_*.py'
	cd services/api && python -m pytest
	python scripts/validate_catalogue.py
	cd frontend && npm run build
lint:
	cd services/api && python -m ruff check growth tests
	cd frontend && npm run typecheck
migrate:
	docker compose run --rm migrate
seed:
	@echo "Provision deliberately: docker compose exec api flask --app growth provision --name YOUR_NAME --workspace YOUR_WORKSPACE"
