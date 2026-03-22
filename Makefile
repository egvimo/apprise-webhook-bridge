format:
	uv run ruff format
	uv run ruff check --select I --fix

lint:
	uv run ruff check

lint-fix:
	uv run ruff check --fix

test:
	uv run pytest

run:
	uv run uvicorn apprise_webhook_bridge.main:app --reload --host 0.0.0.0 --port 8001 --log-config config/log_config.yaml
