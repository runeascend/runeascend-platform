format:
	poetry run black .
	poetry run isort . 
format-check:
	poetry run black --check .
	poetry run isort --check .
dep-check:
	poetry run deptry .
create-dev:
	python3.11 -m venv .venv
	.venv/bin/pip install poetry==1.4.2
	.venv/bin/python3 -m poetry install --with dev
	echo "run source .venv/bin/activate"
update-dev:
	.venv/bin/python3 -m poetry update
unit-test:
	poetry run pytest --cov-report term --cov-report html --cov=./runespreader tests/unit

build-e2e:
	docker build -t runeascend:e2e -f Dockerfile .

e2e-test:
	build-e2e
	poetry run pytest --cov-report term --cov-report html --cov=./runespreader tests/e2e

test: unit-test e2e-test
