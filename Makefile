.PHONY: run install test clean freeze migrate

run:
	docker compose up --build

install:
	pip install -r requirements.txt

freeze:
	pip freeze > requirements.txt

test:
	PYTHONPATH=. pytest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete