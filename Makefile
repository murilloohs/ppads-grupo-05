up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api

ps:
	docker compose ps

migrate:
	docker compose exec api alembic upgrade head

revision:
	docker compose exec api alembic revision --autogenerate -m "$(m)"

test:
	docker compose exec api pytest -q

lint:
	docker compose exec api ruff check .

reset-db:
	docker compose down -v
	docker compose up --build -d
