format:
	uv run black .
	uv run isort .
format-check:
	uv run black --check .
	uv run isort --check .
dep-check:
	uv run deptry .
create-dev:
	uv sync --all-groups
	@echo "run: source .venv/bin/activate"
update-dev:
	uv sync --upgrade --all-groups
lock:
	uv lock
test:
	uv run pytest --cov-report term --cov-report html --cov=./runeascend .
