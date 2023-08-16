format:
	poetry run black .
	poetry run isort . 
create-dev:
	python3.11 -m venv .venv
	.venv/bin/pip install poetry==1.4.2
	.venv/bin/python3 -m poetry install
	echo "run source .venv/bin/activate"
update-dev:
	.venv/bin/python3 -m poetry update
test:
	poetry run pytest